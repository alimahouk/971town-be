from typing import Any, TypeVar, Type

from app.config import DatabaseTable, ProtocolKey, ResponseStatus
from app.modules import db
from app.modules.country import Country


###########
# CLASSES #
###########


T = TypeVar("T", bound="CountryDialingCode")


class CountryDialingCode:
    def __init__(self,
                 data: dict) -> None:
        self.country: Country = None
        self.code: str = None
        self.id: int = 0

        if data:
            if ProtocolKey.ALPHA_2_CODE in data:
                alpha_2_code: str = data[ProtocolKey.ALPHA_2_CODE]
                self.country = Country.get_by_alpha_2_code(alpha_2_code)

            if ProtocolKey.CODE in data:
                self.code: str = data[ProtocolKey.CODE]

            if ProtocolKey.ID in data:
                self.id: str = data[ProtocolKey.ID]

    def __eq__(self,
               __o: object) -> bool:
        ret = False

        if isinstance(__o, type(self)) and \
                self.alpha_2_code == __o.alpha_2_code and \
                self.code == __o.code:
            ret = True

        return ret

    def __hash__(self) -> int:
        return hash(self.alpha_2_code, self.code)

    def __repr__(self) -> str:
        return f"{self.code} ({self.alpha_2_code})"

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.CODE: self.code,
            ProtocolKey.ID: self.id,
        }

        if self.country:
            serialized[ProtocolKey.COUNTRY] = self.country.as_dict()

        return serialized

    @classmethod
    def get_all(cls: Type[T],
                enabled_only=False) -> list[T]:
        if not isinstance(enabled_only, bool):
            raise TypeError(f"Argument 'enabled_only' must be of type bool, not {type(enabled_only)}.")

        ret = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()

            if enabled_only:
                cursor.execute(
                    f"""
                    SELECT * FROM {DatabaseTable.COUNTRY_DIALING_CODE}
                    WHERE {ProtocolKey.ALPHA_2_CODE} IN
                        (SELECT {ProtocolKey.ALPHA_2_CODE} FROM {DatabaseTable.COUNTRY}
                        WHERE {ProtocolKey.IS_ENABLED} = true);
                    """
                )
            else:
                cursor.execute(
                    f"""
                    SELECT * FROM {DatabaseTable.COUNTRY_DIALING_CODE};
                    """
                )

            results = cursor.fetchall()
            conn.commit()

            for result in results:
                ret.append(cls(result))
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    @classmethod
    def get_all_for_country(cls: Type[T],
                            alpha_2_code: str) -> list[T]:
        if not isinstance(alpha_2_code, str):
            raise TypeError(f"Argument 'alpha_2_code' must be of type str, not {type(alpha_2_code)}.")

        if not alpha_2_code:
            raise ValueError("Argument 'alpha_2_code' must be a non-empty string.")

        ret = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.COUNTRY_DIALING_CODE}
                WHERE {ProtocolKey.ALPHA_2_CODE} = %s;
                """,
                (alpha_2_code,)
            )
            results = cursor.fetchall()
            conn.commit()

            for result in results:
                ret.append(cls(result))
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    @classmethod
    def get_by_country_and_dialing_code(cls: Type[T],
                                        alpha_2_code: str,
                                        dialing_code: str) -> T:
        if not isinstance(alpha_2_code, str):
            raise TypeError(f"Argument 'alpha_2_code' must be of type str, not {type(alpha_2_code)}.")

        if not alpha_2_code:
            raise ValueError("Argument 'alpha_2_code' must be a non-empty string.")

        if not isinstance(dialing_code, str):
            raise TypeError(f"Argument 'dialing_code' must be of type str, not {type(dialing_code)}.")

        if not dialing_code:
            raise ValueError("Argument 'dialing_code' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.COUNTRY_DIALING_CODE}
                WHERE {ProtocolKey.ALPHA_2_CODE} = %s AND {ProtocolKey.CODE} = %s;
                """,
                (alpha_2_code, dialing_code,)
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
    def get_by_id(cls: Type[T],
                  dialing_code_id: str) -> T:
        if not isinstance(dialing_code_id, int):
            raise TypeError(f"Argument 'dialing_code_id' must be of type int, not {type(dialing_code_id)}.")

        if dialing_code_id <= 0:
            raise ValueError("Argument 'dialing_code_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.COUNTRY_DIALING_CODE}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (dialing_code_id,)
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


####################
# MODULE FUNCTIONS #
####################


def get_all(is_enabled: str = None) -> tuple[dict, ResponseStatus]:
    response_status = ResponseStatus.OK

    if is_enabled:
        try:
            is_enabled = bool(is_enabled)
        except ValueError:
            is_enabled = False
    else:
        is_enabled = False

    results = CountryDialingCode.get_all(enabled_only=is_enabled)
    serialized = []

    for result in results:
        serialized.append(result.as_dict())

    response = {
        ProtocolKey.DIALING_CODES: serialized
    }

    return (response, response_status)
