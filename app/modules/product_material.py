from typing import Any, TypeVar, Type

from app.config import DatabaseTable, ProtocolKey, ResponseStatus
from app.modules import db


###########
# CLASSES #
###########


T = TypeVar("T", bound="ProductMaterial")


class ProductMaterial:
    def __init__(self,
                 data: dict) -> None:
        self.id: int = None
        self.name: str = None

        if data:
            if ProtocolKey.ID in data:
                self.id: int = data[ProtocolKey.ID]

            if ProtocolKey.NAME in data:
                self.name: str = data[ProtocolKey.NAME]

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
        return f"{self.name} ({self.id})"

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.ID: self.id,
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
                SELECT * FROM {DatabaseTable.PRODUCT_MATERIAL}
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
    def get_by_id(cls: Type[T],
                  material_id: int) -> T:
        if not isinstance(material_id, int):
            raise TypeError(f"Argument 'material_id' must be of type int, not {type(material_id)}.")

        if material_id <= 0:
            raise ValueError("Argument 'material_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.PRODUCT_MATERIAL}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (material_id,)
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

    results = ProductMaterial.get_all()
    serialized = []

    for result in results:
        serialized.append(result.as_dict())

    response = {
        ProtocolKey.PRODUCT_MATERIALS: serialized
    }

    return (response, response_status)
