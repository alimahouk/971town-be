from typing import Any, TypeVar, Type

from app.config import DatabaseTable, ProtocolKey, ResponseStatus
from app.modules import db


###########
# CLASSES #
###########


T = TypeVar("T", bound="ProductColor")


class ProductColor:
    def __init__(self,
                 data: dict) -> None:
        self.hex: str = None
        self.name: str = None

        if data:
            if ProtocolKey.HEX in data:
                self.hex: str = data[ProtocolKey.HEX]

            if ProtocolKey.NAME in data:
                self.name: str = data[ProtocolKey.NAME]

    def __eq__(self,
               __o: object) -> bool:
        ret = False

        if isinstance(__o, type(self)) and \
                self.hex == __o.hex:
            ret = True

        return ret

    def __hash__(self) -> int:
        return hash(self.hex)

    def __repr__(self) -> str:
        return f"{self.name} (#{self.hex})"

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.HEX: self.hex,
            ProtocolKey.NAME: self.name
        }

        return serialized

    @classmethod
    def get_all(cls: Type[T]) -> list[T]:
        ret = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.PRODUCT_COLOR}
                ORDER BY {ProtocolKey.NAME} ASC;
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
    def get_by_code(cls: Type[T],
                    hex: str) -> T:
        if not isinstance(hex, str):
            raise TypeError(f"Argument 'hex' must be of type str, not {type(hex)}.")

        if not hex:
            raise ValueError("Argument 'hex' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.PRODUCT_COLOR}
                WHERE {ProtocolKey.HEX} = %s;
                """,
                (hex,)
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


def get_all() -> tuple[dict, ResponseStatus]:
    response_status = ResponseStatus.OK

    results = ProductColor.get_all()
    serialized = []

    for result in results:
        serialized.append(result.as_dict())

    response = {
        ProtocolKey.PRODUCT_COLORS: serialized
    }

    return (response, response_status)
