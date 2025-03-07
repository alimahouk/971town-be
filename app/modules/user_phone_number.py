from datetime import datetime
from typing import Any, TypeVar, Type

from app.config import Configuration, DatabaseTable, ProtocolKey
from app.modules import db
from app.modules.country_dialing_code import CountryDialingCode


###########
# CLASSES #
###########


T = TypeVar("T", bound="UserPhoneNumber")


class UserPhoneNumber:
    def __init__(self,
                 data: dict) -> None:
        self.creation_timestamp: datetime = None
        self.dialing_code: CountryDialingCode = None
        self.id: int = 0
        self.is_verified: bool = False
        self.phone_number: str = None
        self.user_id: int = 0

        if data:
            if ProtocolKey.CREATION_TIMESTAMP in data:
                self.creation_timestamp: datetime = data[ProtocolKey.CREATION_TIMESTAMP]

            if ProtocolKey.DIALING_CODE_ID in data:
                self.dialing_code = CountryDialingCode.get_by_id(data[ProtocolKey.DIALING_CODE_ID])

            if ProtocolKey.ID in data:
                self.id: int = data[ProtocolKey.ID]

            if ProtocolKey.IS_VERIFIED in data:
                self.is_verified: bool = data[ProtocolKey.IS_VERIFIED]

            if ProtocolKey.PHONE_NUMBER in data:
                self.phone_number: str = data[ProtocolKey.PHONE_NUMBER]

            if ProtocolKey.USER_ID in data:
                self.user_id: int = data[ProtocolKey.USER_ID]

    def __eq__(self,
               __o: object) -> bool:
        ret = False

        if isinstance(__o, type(self)) and \
                self.phone_number == __o.phone_number:
            ret = True

        return ret

    def __hash__(self) -> int:
        return hash(self.dialing_code, self.phone_number)

    def __repr__(self) -> str:
        ret = ""

        if self.dialing_code and self.phone_number:
            ret += f"(+{self.dialing_code}) {self.phone_number}"

        return ret

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.ID: self.id,
            ProtocolKey.IS_VERIFIED: self.is_verified,
            ProtocolKey.PHONE_NUMBER: self.phone_number
        }

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        if self.dialing_code:
            serialized[ProtocolKey.DIALING_CODE] = self.dialing_code.as_dict()

        if self.user_id:
            serialized[ProtocolKey.USER_ID] = self.user_id

        return serialized

    @classmethod
    def create(cls: Type[T],
               country_dialing_code: CountryDialingCode,
               phone_number: str,
               user_id: int) -> T:
        """
        [NOTE] This method makes no assumptions and does not
        attempt to validate phone_number.
        """

        if not isinstance(country_dialing_code, CountryDialingCode):
            raise TypeError(
                f"Argument 'country_dialing_code' must be of type CountryDialingCode, not {type(country_dialing_code)}.")

        if not country_dialing_code:
            raise ValueError("Argument 'country_dialing_code' is None.")

        if not isinstance(phone_number, str):
            raise TypeError(f"Argument 'phone_number' must be of type str, not {type(phone_number)}.")

        if not phone_number:
            raise ValueError("Argument 'phone_number' must be a non-empty string.")

        if not isinstance(user_id, int) and user_id is not None:
            raise TypeError(f"Argument 'user_id' must be of type int or None, not {type(user_id)}.")

        if user_id and user_id <= 0:
            raise ValueError("Argument 'user_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()

            if user_id:
                cursor.execute(
                    f"""
                    INSERT INTO {DatabaseTable.USER_PHONE_NUMBER}
                    ({ProtocolKey.DIALING_CODE_ID}, {ProtocolKey.PHONE_NUMBER}, {ProtocolKey.USER_ID})
                    VALUES (%s, %s, %s) RETURNING *;
                    """,
                    (country_dialing_code.id, phone_number, user_id)
                )
            else:
                cursor.execute(
                    f"""
                    INSERT INTO {DatabaseTable.USER_PHONE_NUMBER}
                    ({ProtocolKey.DIALING_CODE_ID}, {ProtocolKey.PHONE_NUMBER})
                    VALUES (%s, %s) RETURNING *;
                    """,
                    (country_dialing_code.id, phone_number)
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
        if not self.user_id:
            raise Exception("Deletion requires a user ID.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.USER_PHONE_NUMBER}
                WHERE {ProtocolKey.USER_ID} = %s;
                """,
                (self.user_id,)
            )
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

    def formatted_str(self) -> str:
        dialing_code = self.dialing_code.code
        phone_number = self.phone_number

        return f"+{dialing_code}{phone_number}"

    @classmethod
    def get_by_id(cls: Type[T],
                  number_id: int) -> T:
        if not isinstance(number_id, int):
            raise TypeError(f"Argument 'number_id' must be of type int, not {type(number_id)}.")

        if number_id <= 0:
            raise ValueError("Argument 'number_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_PHONE_NUMBER}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (number_id,)
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

    @classmethod
    def get_by_phone_number(cls: Type[T],
                            country_dialing_code: CountryDialingCode,
                            phone_number: str) -> T:
        if not isinstance(country_dialing_code, CountryDialingCode):
            raise TypeError(
                f"Argument 'country_dialing_code' must be of type CountryDialingCode, not {type(country_dialing_code)}.")

        if not country_dialing_code:
            raise ValueError("Argument 'country_dialing_code' is None.")

        if not isinstance(phone_number, str):
            raise TypeError(f"Argument 'phone_number' must be of type str, not {type(phone_number)}.")

        if not phone_number:
            raise ValueError("Argument 'phone_number' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            # Trim leading zero.
            if phone_number.startswith("0"):
                phone_number = phone_number[1:]

            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_PHONE_NUMBER}
                WHERE {ProtocolKey.DIALING_CODE_ID} = %s AND {ProtocolKey.PHONE_NUMBER} = %s;
                """,
                (country_dialing_code.id, phone_number)
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

    @classmethod
    def get_by_user_id(cls: Type[T],
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
                SELECT * FROM {DatabaseTable.USER_PHONE_NUMBER}
                WHERE {ProtocolKey.USER_ID} = %s;
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

    def mark_verified(self) -> None:
        """
        Marks the phone number as verified in the database.

        [NOTE] Also sets the is_verified property on the object
        to True.
        """

        if not self.id:
            raise Exception("Phone number is missing an ID.")

        if not self.dialing_code or not self.phone_number:
            raise Exception("Phone number requires a dialing code and an actual phone number.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.USER_PHONE_NUMBER}
                SET {ProtocolKey.IS_VERIFIED} = true
                WHERE {ProtocolKey.ID} = %s;
                """,
                (self.id,)
            )
            conn.commit()

            self.is_verified = True
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
                DELETE FROM {DatabaseTable.USER_PHONE_NUMBER}
                WHERE {ProtocolKey.USER_ID} IS NULL
                AND {ProtocolKey.CREATION_TIMESTAMP} <= NOW()- INTERVAL '{Configuration.USER_VERIFICATION_CODE_TTL} second';
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

    def set_user_id(self,
                    user_id: int) -> None:
        """
        Attaches a user ID to the phone number in the database.

        [NOTE] Also sets the user_id property on the object.
        """

        if not isinstance(user_id, int):
            raise TypeError(f"Argument 'user_id' must be of type int, not {type(user_id)}.")

        if user_id <= 0:
            raise ValueError("Argument 'user_id' must be a positive, non-zero integer.")

        if not self.id:
            raise Exception("Phone number is missing an ID.")

        if not isinstance(self.dialing_code, CountryDialingCode):
            raise TypeError(
                f"Property 'dialing_code' must be of type CountryDialingCode, not {type(self.dialing_code)}.")

        if not self.dialing_code:
            raise Exception("Property 'dialing_code' is None.")

        if not isinstance(self.phone_number, str):
            raise TypeError(f"Property 'phone_number' must be of type str, not {type(self.phone_number)}.")

        if not self.phone_number:
            raise Exception("Property 'phone_number' must be a non-empty string.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.USER_PHONE_NUMBER}
                SET {ProtocolKey.USER_ID} = %s
                WHERE {ProtocolKey.ID} = %s;
                """,
                (user_id, self.id)
            )
            conn.commit()

            self.user_id = user_id
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()
