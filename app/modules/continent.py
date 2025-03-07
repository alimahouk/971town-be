from typing import Any, TypeVar, Type

from app.config import DatabaseTable, ProtocolKey
from app.modules import db


###########
# CLASSES #
###########


T = TypeVar("T", bound="Continent")


class Continent:
    def __init__(self,
                 data: dict) -> None:
        self.code: str = None
        self.name: str = None

        if data:
            if ProtocolKey.CODE in data:
                self.code: str = data[ProtocolKey.CODE]

            if ProtocolKey.NAME in data:
                self.name: str = data[ProtocolKey.NAME]

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
        return f"{self.name} ({self.code})"

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.CODE: self.code,
            ProtocolKey.NAME: self.name
        }

        return serialized

    @classmethod
    def get_by_code(cls: Type[T],
                    continent_code: str) -> T:
        if not isinstance(continent_code, str):
            raise TypeError(f"Argument 'continent_code' must be of type str, not {type(continent_code)}.")

        if not continent_code:
            raise ValueError("Argument 'continent_code' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.CONTINENT}
                WHERE {ProtocolKey.CODE} = %s;
                """,
                (continent_code,)
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
                    continent_name: str) -> T:
        if not isinstance(continent_name, str):
            raise TypeError(f"Argument 'continent_name' must be of type str, not {type(continent_name)}.")

        if not continent_name:
            raise ValueError("Argument 'continent_name' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.CONTINENT}
                WHERE {ProtocolKey.NAME} = %s;
                """,
                (continent_name,)
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
