from datetime import datetime, timedelta
from flask import request
import string
from typing import Any, TypeVar, Type

from app.config import Configuration, DatabaseTable, ProtocolKey, ResponseStatus
from app.modules import db, user_account_session
from app.modules.user_account import UserAccount
from app.modules.user_account_session import UserAccountSession
from app.modules.user_phone_number import UserPhoneNumber
from app.modules.user_phone_number_verification_code import UserPhoneNumberVerificationCode
from app.modules.user_shadow_ban import UserShadowBan


###########
# CLASSES #
###########


T = TypeVar("T", bound="User")


class User:
    def __init__(self,
                 data: dict) -> None:
        self.accounts: list[UserAccount] = []
        self.creation_timestamp: datetime = None
        self.id: int = 0
        self.shadow_bans: list[UserShadowBan] = []
        self.phone_number: UserPhoneNumber = None

        if data:
            if ProtocolKey.CREATION_TIMESTAMP in data:
                self.creation_timestamp: datetime = data[ProtocolKey.CREATION_TIMESTAMP]

            if ProtocolKey.ID in data:
                self.id: int = data[ProtocolKey.ID]
                self.phone_number = UserPhoneNumber.get_by_user_id(self.id)
                self.shadow_bans = UserShadowBan.get_all_for_user(self.id)

    def __eq__(self,
               __o: object) -> bool:
        ret = False

        if isinstance(__o, type(self)) and \
                self.id == __o.id:
            ret = True

        return ret

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        ret = ""

        if self.id:
            ret += "User " + self.id.__str__()

        return ret

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.ID: self.id,
            ProtocolKey.PHONE_NUMBER_ID: self.phone_number.id
        }

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        return serialized

    @classmethod
    def create(cls: Type[T]) -> T:
        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.USER}
                ({ProtocolKey.ID})
                VALUES (DEFAULT) RETURNING *;
                """
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
        if not self.id:
            raise Exception("Deletion requires a user ID.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.USER}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (self.id,)
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
                            phone_number: UserPhoneNumber) -> T:
        if not isinstance(phone_number, UserPhoneNumber):
            raise TypeError(
                f"Argument 'phone_number' must be of type UserPhoneNumber, not {type(phone_number)}."
            )

        if not phone_number:
            raise ValueError("Argument 'phone_number' is None.")

        if not phone_number.user_id:
            raise Exception("Argument 'phone_number' has no user ID associated with it.")

        return cls.get_by_user_id(phone_number.user_id)

    @classmethod
    def get_by_id(cls: Type[T],
                  user_id: int) -> T:
        if not isinstance(user_id, int):
            raise TypeError(f"Argument 'user_id' must be of type int, not {type(user_id)}.")

        if user_id <= 0:
            raise ValueError("Argument 'user_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (user_id,)
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

    @staticmethod
    def id_exists(user_id: int) -> bool:
        if not isinstance(user_id, int):
            raise TypeError(f"Argument 'user_id' must be of type int, not {type(user_id)}.")

        if user_id <= 0:
            raise ValueError("Argument 'user_id' must be a positive, non-zero integer.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (user_id,)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                ret = True
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    @staticmethod
    def is_shadow_banned_user(user_id: int) -> bool:
        if not isinstance(user_id, int):
            raise TypeError(f"Argument 'user_id' must be of type int, not {type(user_id)}.")

        if user_id <= 0:
            raise ValueError("Argument 'user_id' must be a positive, non-zero integer.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_SHADOW_BAN}
                WHERE {ProtocolKey.USER_ID} = %s;
                """,
                (user_id,)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                ret = True
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret


####################
# MODULE FUNCTIONS #
####################


def join(alias: str,
         client_id: str,
         code: str,
         phone_number_id: int) -> tuple[dict, ResponseStatus]:
    """
    For new users signing up.
    """

    if code:
        code = "".join(char for char in code if char in string.printable)
    else:
        code = None

    try:
        phone_number_id = int(phone_number_id)

        if phone_number_id <= 0:
            phone_number_id = None
    except ValueError:
        phone_number_id = None

    if not alias or \
            not phone_number_id or \
            phone_number_id <= 0 or \
            not code:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not alias:
            error_message += ": 'alias' must be an ASCII non-empty string."
        elif not phone_number_id or phone_number_id <= 0:
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
            if user_phone_number.is_verified:
                verification_code = UserPhoneNumberVerificationCode.get_by_phone_number(user_phone_number.id)

                if verification_code:
                    if verification_code.creation_timestamp < datetime.utcnow() - timedelta(seconds=Configuration.USER_VERIFICATION_CODE_TTL):
                        # Code expired.
                        verification_code.delete()

                        response_status = ResponseStatus.BAD_REQUEST
                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: ResponseStatus.VERIFICATION_CODE_EXPIRED.value,
                                ProtocolKey.ERROR_MESSAGE: "Previously entered verification code has expired."
                            }
                        }
                    elif code == verification_code.verification_code:
                        alias = alias.lower()

                        if UserAccount.alias_valid(alias):
                            if not UserAccount.alias_exists(alias):
                                if user_phone_number.user_id:
                                    new_user = None
                                    user_id = user_phone_number.user_id
                                else:
                                    new_user = User.create()
                                    user_id = new_user.id
                                    user_phone_number.set_user_id(user_id)

                                if not new_user:
                                    account_count = UserAccount.get_count(user_id)

                                    if account_count >= Configuration.USER_ACCOUNT_MAX_COUNT:
                                        response_status = ResponseStatus.BAD_REQUEST
                                        response = {
                                            ProtocolKey.ERROR: {
                                                ProtocolKey.ERROR_CODE: ResponseStatus.USER_ACCOUNT_MAX_COUNT_REACHED.value,
                                                ProtocolKey.ERROR_MESSAGE: "Limit of accounts associated with this phone number has been reached."
                                            }
                                        }

                                if response_status == ResponseStatus.OK:
                                    new_account = UserAccount.create(alias, user_id)
                                    new_session = user_account_session.create_session(client_id, new_account.id)

                                    verification_code.delete()  # Don't need this anymore.

                                    if new_session:
                                        response = {
                                            ProtocolKey.USER_ACCOUNT: new_account.as_dict(is_public=False),
                                            ProtocolKey.USER_ACCOUNT_SESSION: {
                                                ProtocolKey.CREATION_TIMESTAMP: new_session.creation_timestamp,
                                                ProtocolKey.ID: new_session.id,
                                                ProtocolKey.USER_ACCOUNT_ID: new_account.id
                                            }
                                        }
                                    else:
                                        # Unsupported client.
                                        response = {
                                            ProtocolKey.ERROR: {
                                                ProtocolKey.ERROR_CODE: ResponseStatus.UNSUPPORTED_CLIENT.value,
                                                ProtocolKey.ERROR_MESSAGE: "Unsupported client."
                                            }
                                        }
                            else:
                                # Alias is taken.
                                response_status = ResponseStatus.BAD_REQUEST
                                response = {
                                    ProtocolKey.ERROR: {
                                        ProtocolKey.ERROR_CODE: ResponseStatus.ALIAS_EXISTS.value,
                                        ProtocolKey.ERROR_MESSAGE: "Alias already in use."
                                    }
                                }
                        else:
                            # Invalid alias.
                            response_status = ResponseStatus.BAD_REQUEST
                            response = {
                                ProtocolKey.ERROR: {
                                    ProtocolKey.ERROR_CODE: ResponseStatus.ALIAS_INVALID.value,
                                    ProtocolKey.ERROR_MESSAGE: f"Alias format is invalid. An alias must be between {Configuration.ALIAS_MIN_LEN} and {Configuration.ALIAS_MAX_LEN} characters long and can only contain dots, dashes, underscores, and alphanumeric ASCII characters."
                                }
                            }
                    else:
                        # Incorrect code.
                        response_status = ResponseStatus.BAD_REQUEST
                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: ResponseStatus.VERIFICATION_CODE_INCORRECT.value,
                                ProtocolKey.ERROR_MESSAGE: "Verification code is incorrect."
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
                # Phone number is not verified.
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.PHONE_NUMBER_UNVERIFIED.value,
                        ProtocolKey.ERROR_MESSAGE: "Phone number is not verified."
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


def log_in(client_id: str,
           code: str,
           phone_number_id: int,
           user_account_id: int) -> tuple[dict, ResponseStatus]:
    if code:
        code = "".join(char for char in code if char in string.printable)
    else:
        code = None

    try:
        user_account_id = int(user_account_id)
    except ValueError:
        user_account_id = None

    try:
        phone_number_id = int(phone_number_id)

        if phone_number_id <= 0:
            phone_number_id = None
    except ValueError:
        phone_number_id = None

    if not user_account_id or \
            not phone_number_id or \
            phone_number_id <= 0 or \
            not code:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not user_account_id or user_account_id <= 0:
            error_message += ": 'user_account_id' must be a positive, non-zero integer."
        elif not phone_number_id or phone_number_id <= 0:
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
            if user_phone_number.is_verified:
                verification_code = UserPhoneNumberVerificationCode.get_by_phone_number(user_phone_number.id)

                if verification_code:
                    if verification_code.creation_timestamp < datetime.utcnow() - timedelta(seconds=Configuration.USER_VERIFICATION_CODE_TTL):
                        # Code expired.
                        verification_code.delete()

                        response_status = ResponseStatus.BAD_REQUEST
                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: ResponseStatus.VERIFICATION_CODE_EXPIRED.value,
                                ProtocolKey.ERROR_MESSAGE: "Previously entered verification code has expired."
                            }
                        }
                    elif code == verification_code.verification_code:
                        account = UserAccount.get_by_id(user_account_id)

                        if account:
                            new_session = user_account_session.create_session(client_id, account.id)
                            verification_code.delete()  # Don't need this anymore.

                            if new_session:
                                response = {
                                    ProtocolKey.USER_ACCOUNT: account.as_dict(is_public=False),
                                    ProtocolKey.USER_ACCOUNT_SESSION: {
                                        ProtocolKey.CREATION_TIMESTAMP: new_session.creation_timestamp,
                                        ProtocolKey.ID: new_session.id,
                                        ProtocolKey.USER_ACCOUNT_ID: account.id
                                    }
                                }
                            else:
                                # Unsupported client.
                                response = {
                                    ProtocolKey.ERROR: {
                                        ProtocolKey.ERROR_CODE: ResponseStatus.UNSUPPORTED_CLIENT.value,
                                        ProtocolKey.ERROR_MESSAGE: "Unsupported client."
                                    }
                                }
                        else:
                            # Account doesn't exist.
                            response_status = ResponseStatus.NOT_FOUND
                            response = {
                                ProtocolKey.ERROR: {
                                    ProtocolKey.ERROR_CODE: ResponseStatus.response_status.value,
                                    ProtocolKey.ERROR_MESSAGE: f"No account exists for this ID."
                                }
                            }
                    else:
                        # Incorrect code.
                        response_status = ResponseStatus.BAD_REQUEST
                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: ResponseStatus.VERIFICATION_CODE_INCORRECT.value,
                                ProtocolKey.ERROR_MESSAGE: "Verification code is incorrect."
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
                # Phone number is not verified.
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.PHONE_NUMBER_UNVERIFIED.value,
                        ProtocolKey.ERROR_MESSAGE: "Phone number is not verified."
                    }
                }
        else:
            # Phone number is not registered.
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: response_status.value,
                    ProtocolKey.ERROR_MESSAGE: "Phone number is not registered."
                }
            }

    return (response, response_status)


def log_out() -> tuple[dict, ResponseStatus]:
    session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)

    if session_id:
        session = UserAccountSession.get_by_id(session_id)
    else:
        session = None

    if session:
        session.delete()

        response_status = ResponseStatus.OK
        response = {
            ProtocolKey.USER_ACCOUNT_ID: session.user_account_id
        }
    else:
        response_status = ResponseStatus.UNAUTHORIZED
        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: "Cannot log out; this is an invalid session."
            }
        }

    return (response, response_status)
