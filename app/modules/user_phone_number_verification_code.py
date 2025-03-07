from datetime import datetime, timedelta
import hashlib
import re
import sched
import string
import threading
import time
from twilio.rest import Client
from typing import Any, TypeVar, Type
import uuid

from app import app
from app.config import Configuration, DatabaseTable, ProtocolKey, ResponseStatus
from app.modules import db
from app.modules.country_dialing_code import CountryDialingCode
from app.modules.user_account import UserAccount
from app.modules.user_phone_number import UserPhoneNumber


###########
# CLASSES #
###########


T = TypeVar("T", bound="UserPhoneNumberVerificationCode")


class UserPhoneNumberVerificationCode:
    def __init__(self,
                 data: dict) -> None:
        self.attempts: int = 0
        self.creation_timestamp: datetime = None
        self.phone_number: UserPhoneNumber = None
        self.verification_code: str = None

        if data:
            if ProtocolKey.ATTEMPTS in data:
                self.attempts: int = data[ProtocolKey.ATTEMPTS]

            if ProtocolKey.CREATION_TIMESTAMP in data:
                self.creation_timestamp: datetime = data[ProtocolKey.CREATION_TIMESTAMP]

            if ProtocolKey.PHONE_NUMBER_ID in data:
                phone_number_id: int = data[ProtocolKey.PHONE_NUMBER_ID]
                self.phone_number = UserPhoneNumber.get_by_id(phone_number_id)

            if ProtocolKey.VERIFICATION_CODE in data:
                self.verification_code: str = data[ProtocolKey.VERIFICATION_CODE]

    def __eq__(self,
               __o: object) -> bool:
        ret = False

        if isinstance(__o, type(self)) and \
                self.phone_number.id == __o.phone_number.id and \
                self.verification_code == __o.verification_code:
            ret = True

        return ret

    def __hash__(self) -> int:
        return hash((self.phone_number.id, self.verification_code))

    def __repr__(self) -> str:
        return f"Verification Code {self.verification_code}"

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized: dict[ProtocolKey, Any] = {}

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        if self.phone_number:
            serialized[ProtocolKey.PHONE_NUMBER] = self.phone_number.as_dict()

        return serialized

    @classmethod
    def create(cls: Type[T],
               phone_number: UserPhoneNumber,
               verification_code: str) -> T:
        if not isinstance(phone_number, UserPhoneNumber):
            raise TypeError(f"Argument 'phone_number' must be of type UserPhoneNumber, not {type(phone_number)}.")

        if not phone_number.id:
            raise ValueError("Argument 'phone_number' has no ID associated with it.")

        if not isinstance(verification_code, str):
            raise TypeError(f"Argument 'verification_code' must be of type str, not {type(verification_code)}.")

        if not verification_code:
            raise ValueError("Argument 'verification_code' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.USER_PHONE_NUMBER_VERIFICATION_CODE}
                ({ProtocolKey.PHONE_NUMBER_ID}, {ProtocolKey.VERIFICATION_CODE})
                VALUES (%s, %s) RETURNING *;
                """,
                (phone_number.id, verification_code)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                ret = cls(result)
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    def delete(self) -> None:
        if not self.verification_code or not self.phone_number:
            raise Exception("Deletion requires a verification code and phone number.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.USER_PHONE_NUMBER_VERIFICATION_CODE}
                WHERE {ProtocolKey.PHONE_NUMBER_ID} = %s AND {ProtocolKey.VERIFICATION_CODE} = %s;
                """,
                (self.phone_number.id, self.verification_code)
            )
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

    @classmethod
    def get_by_phone_number(cls: Type[T],
                            phone_number_id: int) -> T:
        if not isinstance(phone_number_id, int):
            raise TypeError(f"Argument 'phone_number_id' must be of type int, not {type(phone_number_id)}.")

        if phone_number_id <= 0:
            raise ValueError("Argument 'phone_number_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_PHONE_NUMBER_VERIFICATION_CODE}
                WHERE {ProtocolKey.PHONE_NUMBER_ID} = %s;
                """,
                (phone_number_id,)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                ret = cls(result)
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    def increment_attempts(self) -> None:
        """
        Increments the attempt count. To be used when an incorrect code
        is entered.

        [NOTE] Also increments the attempts property on the object.
        """

        if not self.id:
            raise Exception("Phone number verification code is missing an ID.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.USER_PHONE_NUMBER_VERIFICATION_CODE}
                SET {ProtocolKey.ATTEMPTS} = {ProtocolKey.ATTEMPTS} + 1
                WHERE {ProtocolKey.PHONE_NUMBER_ID} = %s;
                """,
                (self.phone_number.id,)
            )
            conn.commit()

            self.attempts += 1
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

    @staticmethod
    def purge_stale() -> None:
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.USER_PHONE_NUMBER_VERIFICATION_CODE}
                WHERE {ProtocolKey.CREATION_TIMESTAMP} <= NOW()- INTERVAL '{Configuration.USER_VERIFICATION_CODE_TTL} second';
                """
            )
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()


class VerificationCodePurgeJob(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)

    def purge_stale(self,
                    scheduled_task: sched.scheduler) -> None:
        try:
            """
            No need to manually delete from UserPhoneNumberVerificationCode;
            it'll cascade from UserPhoneNumber.
            """
            UserPhoneNumber.purge_stale()
        except Exception as e:
            print(e)

        scheduled_task.enter(Configuration.USER_VERIFICATION_CODE_PURGE_INTERVAL,
                             1,
                             self.purge_stale,
                             (scheduled_task,))

    def run(self) -> None:
        stale_codes_scheduled_task = sched.scheduler(time.time, time.sleep)

        stale_codes_scheduled_task.enter(Configuration.USER_VERIFICATION_CODE_PURGE_INTERVAL,
                                         1,
                                         self.purge_stale,
                                         (stale_codes_scheduled_task,))
        stale_codes_scheduled_task.run()


stale_codes_scheduled_task = VerificationCodePurgeJob()
stale_codes_scheduled_task.start()


####################
# MODULE FUNCTIONS #
####################


def check_verification_code(phone_number_id: str,
                            code: str) -> tuple[dict, ResponseStatus]:
    try:
        phone_number_id = int(phone_number_id)

        if phone_number_id <= 0:
            phone_number_id = None
    except ValueError:
        phone_number_id = None

    if code:
        code = "".join(char for char in code if char in string.printable)

    if not phone_number_id or \
            not phone_number_id or \
            phone_number_id <= 0 or \
            not code:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not phone_number_id or phone_number_id <= 0:
            error_message += ": 'phone_number_id' must be a positive, non-zero integer."
        elif not code:
            error_message += ": 'code' must be a non-empty string."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}

        user_phone_number = UserPhoneNumber.get_by_id(phone_number_id)

        if user_phone_number:
            verification_code = UserPhoneNumberVerificationCode.get_by_phone_number(user_phone_number.id)

            if verification_code:
                if verification_code.creation_timestamp < datetime.utcnow() - timedelta(seconds=Configuration.USER_VERIFICATION_CODE_TTL):
                    # Code expired.
                    verification_code.delete()

                    response_status = ResponseStatus.BAD_REQUEST
                    response = {
                        ProtocolKey.ERROR: {
                            ProtocolKey.ERROR_CODE: ResponseStatus.VERIFICATION_CODE_EXPIRED.value,
                            ProtocolKey.ERROR_MESSAGE: "Entered verification code has expired."
                        }
                    }
                elif code == verification_code.verification_code:
                    if not user_phone_number.is_verified:
                        user_phone_number.mark_verified()

                    # Don't delete the verification code yet; it'll be needed for user registration/login.

                    if user_phone_number.user_id:
                        # Existing user.
                        user_id = user_phone_number.user_id
                        accounts_full = UserAccount.get_all_by_user(user_id)
                        accounts_serialized: list[dict] = []

                        for account in accounts_full:
                            accounts_serialized.append(account.as_dict())

                        response = {
                            ProtocolKey.PHONE_NUMBER_ID: user_phone_number.id,
                            ProtocolKey.USER_ID: user_id,
                            ProtocolKey.USER_ACCOUNTS: accounts_serialized
                        }
                    else:
                        # New user.
                        response = {
                            ProtocolKey.PHONE_NUMBER_ID: user_phone_number.id
                        }
                else:
                    # Incorrect code.
                    verification_code.increment_attempts()

                    if verification_code.attempts >= Configuration.USER_VERIFICATION_CODE_ATTEMPT_LIMIT:
                        response_status = ResponseStatus.TOO_MANY_REQUESTS
                        error_code = ResponseStatus.VERIFICATION_CODE_EXPIRED
                        error_message = "Entered verification code is incorrect. All attempts have been exhausted and the code has been invalidated."
                        verification_code.delete()
                    else:
                        response_status = ResponseStatus.BAD_REQUEST
                        error_code = ResponseStatus.VERIFICATION_CODE_INCORRECT
                        error_message = f"Entered verification code is incorrect. {Configuration.USER_VERIFICATION_CODE_ATTEMPT_LIMIT - verification_code.attempts} attempt(s) remaining."

                    response = {
                        ProtocolKey.ERROR: {
                            ProtocolKey.ERROR_CODE: error_code.value,
                            ProtocolKey.ERROR_MESSAGE: error_message
                        }
                    }
            else:
                # No verification code exists for the number.
                response_status = ResponseStatus.NOT_FOUND
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.VERIFICATION_CODE_NOT_FOUND.value,
                        ProtocolKey.ERROR_MESSAGE: "No verification code exists for this phone number."
                    }
                }
        else:
            # Phone number is not registered.
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.PHONE_NUMBER_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "Phone number is not registered."
                }
            }

    return (response, response_status)


def generate_verification_code() -> str:
    """
    Generates a six-digit code.

    [NOTE] This function doesn't write anything to the database.
    """

    rand = uuid.uuid4().hex
    num = ""

    for c in rand:
        if c.isdigit():
            num += c

    return num[:Configuration.USER_VERIFICATION_CODE_LEN]


def send_verification_code(alpha_2_code: str,
                           dialing_code: str,
                           phone_number: str) -> tuple[dict, ResponseStatus]:
    """
    Sends a six-digit code via SMS to the given number.
    A record of this gets created in the database for
    verifying the code once submitted back by the user.
    """

    if alpha_2_code:
        alpha_2_code = "".join(char for char in alpha_2_code if char in string.printable)

    if dialing_code:
        dialing_code = "".join(char for char in dialing_code if char in string.printable)

    if phone_number:
        # Remove all non-numeric characters.
        phone_number = re.sub("[^0-9]", "", phone_number)
        # Trim leading zero.
        if phone_number.startswith("0"):
            phone_number = phone_number[1:]

    if not alpha_2_code or \
            not dialing_code or \
            not phone_number:
        error_message = "Invalid or missing parameter"

        if not alpha_2_code:
            error_message += ": 'alpha_2_code' must be a non-empty string."
        elif not dialing_code:
            error_message += ": 'dialing_code' must be a non-empty string."
        elif not phone_number:
            error_message += ": 'phone_number' must be a non-empty string."

        response_status = ResponseStatus.BAD_REQUEST
        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}

        country_dialing_code = CountryDialingCode.get_by_country_and_dialing_code(
            alpha_2_code,
            dialing_code
        )

        user_phone_number = UserPhoneNumber.get_by_phone_number(country_dialing_code, phone_number)

        if not user_phone_number:
            user_phone_number = UserPhoneNumber.create(country_dialing_code, phone_number, None)

        if user_phone_number:
            # Delete any existing code.
            existing_code = UserPhoneNumberVerificationCode.get_by_phone_number(user_phone_number.id)

            if existing_code:
                existing_code.delete()

            formatted_phone_number = user_phone_number.formatted_str()

            if app.debug or \
                    phone_number == Configuration.TESTING_PHONE_NUMBER:
                # A special phone number that uses a static OTP.
                code_plaintext = Configuration.TESTING_OTP
                is_testing = True
            else:
                code_plaintext = generate_verification_code()
                is_testing = False

            # For added security, we store a hash of the code, not the code itself.
            code_digest = hashlib.sha256(code_plaintext.encode("utf-8")).hexdigest()
            verification_code = UserPhoneNumberVerificationCode.create(user_phone_number, code_digest)

            try:
                if not is_testing:
                    client = Client(Configuration.TWILIO_ACCOUNT_SID, Configuration.TWILIO_AUTH_TOKEN)
                    client.messages.create(
                        body=f"Your {Configuration.SERVICE_NAME} verification code is {code_plaintext} (valid for {int(Configuration.USER_VERIFICATION_CODE_TTL / 60)} mins).",
                        from_="+447700164646",
                        to=formatted_phone_number
                    )

                response = verification_code.as_dict()
            except:
                # Phone number is invalid.
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.PHONE_NUMBER_INVALID.value,
                        ProtocolKey.ERROR_MESSAGE: "Phone number is invalid."
                    }
                }
        else:
            response_status = ResponseStatus.INTERNAL_SERVER_ERROR

    return (response, response_status)
