from typing import Any, TypeVar, Type

from app.config import DatabaseTable, ProtocolKey, ResponseStatus
from app.modules import db
from app.modules.continent import Continent
from app.modules.currency import Currency


###########
# CLASSES #
###########


T = TypeVar("T", bound="Country")


class Country:
    def __init__(self,
                 data: dict) -> None:
        self.alpha_2_code: str = None
        self.alpha_3_code: str = None
        self.continent: Continent = None
        self.currency: Currency = None
        self.full_name: str = None
        self.name: str = None
        self.numeric_3_code: str = None

        if data:
            if ProtocolKey.ALPHA_2_CODE in data:
                self.alpha_2_code: str = data[ProtocolKey.ALPHA_2_CODE]

            if ProtocolKey.ALPHA_3_CODE in data:
                self.alpha_3_code: str = data[ProtocolKey.ALPHA_3_CODE]

            if ProtocolKey.CONTINENT_CODE in data and data[ProtocolKey.CONTINENT_CODE]:
                self.continent = Continent.get_by_code(data[ProtocolKey.CONTINENT_CODE])

            if ProtocolKey.CURRENCY_CODE in data and data[ProtocolKey.CURRENCY_CODE]:
                self.currency = Currency.get_by_code(data[ProtocolKey.CURRENCY_CODE])

            if ProtocolKey.FULL_NAME in data:
                self.full_name: str = data[ProtocolKey.FULL_NAME]

            if ProtocolKey.NAME in data:
                self.name: str = data[ProtocolKey.NAME]

            if ProtocolKey.NUMERIC_3_CODE in data:
                self.numeric_3_code: str = data[ProtocolKey.NUMERIC_3_CODE]

    def __eq__(self,
               __o: object) -> bool:
        ret = False

        if isinstance(__o, type(self)) and \
                self.alpha_2_code == __o.alpha_2_code:
            ret = True

        return ret

    def __hash__(self) -> int:
        return hash(self.alpha_2_code)

    def __repr__(self) -> str:
        return f"{self.name} ({self.alpha_2_code})"

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.ALPHA_2_CODE: self.alpha_2_code,
            ProtocolKey.ALPHA_3_CODE: self.alpha_3_code,
            ProtocolKey.NAME: self.name,
            ProtocolKey.FULL_NAME: self.full_name,
            ProtocolKey.NUMERIC_3_CODE: self.numeric_3_code
        }

        if self.continent:
            serialized[ProtocolKey.CONTINENT] = self.continent.as_dict()

        if self.currency:
            serialized[ProtocolKey.CURRENCY] = self.currency.as_dict()

        return serialized

    @staticmethod
    def alpha_2_code_exists(alpha_2_code: str) -> bool:
        if not isinstance(alpha_2_code, str):
            raise TypeError(f"Argument 'alpha_2_code' must be of type str, not {type(alpha_2_code)}.")

        if not alpha_2_code:
            raise ValueError("Argument 'alpha_2_code' must be a non-empty string.")

        ret = False
        conn = None
        cursor = None
        alpha_2_code = alpha_2_code.strip().upper()

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.COUNTRY}
                WHERE {ProtocolKey.ALPHA_2_CODE} = %s;
                """,
                (alpha_2_code,)
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
                    SELECT * FROM {DatabaseTable.COUNTRY}
                    WHERE {ProtocolKey.IS_ENABLED} = true;
                    """
                )
            else:
                cursor.execute(f"""SELECT * FROM {DatabaseTable.COUNTRY}""")

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
    def get_all_for_continent(cls: Type[T],
                              continent_code: str) -> list[T]:
        if not isinstance(continent_code, str):
            raise TypeError(f"Argument 'continent_code' must be of type str, not {type(continent_code)}.")

        if not continent_code:
            raise ValueError("Argument 'continent_code' must be a non-empty string.")

        ret = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.COUNTRY}
                WHERE {ProtocolKey.CONTINENT_CODE} = %s;
                """,
                (continent_code,)
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
    def get_by_alpha_2_code(cls: Type[T],
                            alpha_2_code: str) -> T:
        if not isinstance(alpha_2_code, str):
            raise TypeError(f"Argument 'alpha_2_code' must be of type str, not {type(alpha_2_code)}.")

        if not alpha_2_code:
            raise ValueError("Argument 'alpha_2_code' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.COUNTRY}
                WHERE {ProtocolKey.ALPHA_2_CODE} = %s;
                """,
                (alpha_2_code,)
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
    def get_by_alpha_3_code(cls: Type[T],
                            alpha_3_code: str) -> T:
        if not isinstance(alpha_3_code, str):
            raise TypeError(f"Argument 'alpha_3_code' must be of type str, not {type(alpha_3_code)}.")

        if not alpha_3_code:
            raise ValueError("Argument 'alpha_3_code' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.COUNTRY}
                WHERE {ProtocolKey.ALPHA_3_CODE} = %s;
                """,
                (alpha_3_code,)
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
    def get_by_name(cls: Type[T],
                    country_name: str) -> T:
        if not isinstance(country_name, str):
            raise TypeError(f"Argument 'country_name' must be of type str, not {type(country_name)}.")

        if not country_name:
            raise ValueError("Argument 'country_name' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.COUNTRY}
                WHERE {ProtocolKey.NAME} = %s;
                """,
                (country_name,)
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
    def get_by_numeric_3_code(cls: Type[T],
                              numeric_3_code: str) -> T:
        if not isinstance(numeric_3_code, str):
            raise TypeError(f"Argument 'numeric_3_code' must be of type str, not {type(numeric_3_code)}.")

        if not numeric_3_code:
            raise ValueError("Argument 'numeric_3_code' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.COUNTRY}
                WHERE {ProtocolKey.NUMERIC_3_CODE} = %s;
                """,
                (numeric_3_code,)
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

    results = Country.get_all(enabled_only=is_enabled)
    serialized = []

    for result in results:
        serialized.append(result.as_dict())

    response = {
        ProtocolKey.COUNTRIES: serialized
    }

    return (response, response_status)
