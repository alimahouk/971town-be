from typing import Any, TypeVar, Type

from app.config import DatabaseTable, ProtocolKey
from app.modules import db


###########
# CLASSES #
###########


T = TypeVar("T", bound="Currency")


class Currency:
    def __init__(self,
                 data: dict) -> None:
        self.code: str = None
        self.symbol: str = None

        if data:
            if ProtocolKey.CODE in data:
                self.code: str = data[ProtocolKey.CODE]

            if ProtocolKey.SYMBOL in data:
                self.symbol: str = data[ProtocolKey.SYMBOL]

    def __eq__(self,
               __o: object) -> bool:
        ret = False

        if isinstance(__o, type(self)) and \
                self.code == __o.code:
            ret = True

        return ret

    def __hash__(self) -> int:
        return hash(self.code)

    def __repr__(self) -> str:
        return f"{self.code} ({self.symbol})"

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.CODE: self.code,
            ProtocolKey.SYMBOL: self.symbol
        }

        return serialized

    @staticmethod
    def code_exists(currency_code: str) -> bool:
        if not isinstance(currency_code, str):
            raise TypeError(f"Argument 'currency_code' must be of type str, not {type(currency_code)}.")

        if not currency_code:
            raise ValueError("Argument 'currency_code' must be a non-empty string.")

        ret = False
        conn = None
        cursor = None
        currency_code = currency_code.strip().upper()

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.CURRENCY}
                WHERE {ProtocolKey.CODE} = %s;
                """,
                (currency_code,)
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
    def get_all(cls: Type[T]) -> list[T]:
        ret = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(f"""SELECT * FROM {DatabaseTable.CURRENCY}""")
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
    def get_by_code(cls: Type[T],
                    currency_code: str) -> T:
        if not isinstance(currency_code, str):
            raise TypeError(f"Argument 'currency_code' must be of type str, not {type(currency_code)}.")

        if not currency_code:
            raise ValueError("Argument 'currency_code' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.CURRENCY}
                WHERE {ProtocolKey.CODE} = %s;
                """,
                (currency_code,)
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
