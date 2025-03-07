from datetime import datetime
from typing import Any, TypeVar, Type

from app.config import DatabaseTable, MediaMode, MediaType, \
    ProtocolKey
from app.modules import db
from app.modules.user_account import UserAccount


###########
# CLASSES #
###########


T = TypeVar("T", bound="ProductMedium")


class ProductMedium:
    def __init__(self,
                 data: dict) -> None:
        self.attribution: str = None
        self.creation_timestamp: datetime = None
        self.creator: UserAccount = None
        self.creator_id: int = None
        self.file_path: str = None
        self.id: str = None
        self.index: int = None
        self.media_mode: MediaMode = None
        self.media_type: MediaType = None
        self.product_id: int = None

        if data:
            if ProtocolKey.ATTRIBUTION in data:
                self.attribution: str = data[ProtocolKey.ATTRIBUTION]

            if ProtocolKey.CREATION_TIMESTAMP in data:
                self.creation_timestamp: datetime = data[ProtocolKey.CREATION_TIMESTAMP]

            if ProtocolKey.CREATOR_ID in data:
                self.creator_id: int = data[ProtocolKey.CREATOR_ID]

            if ProtocolKey.FILE_PATH in data:
                self.file_path: str = data[ProtocolKey.FILE_PATH]

            if ProtocolKey.ID in data:
                self.id: int = data[ProtocolKey.ID]

            if ProtocolKey.INDEX in data:
                self.index: int = data[ProtocolKey.INDEX]

            if ProtocolKey.MEDIA_MODE in data and data[ProtocolKey.MEDIA_MODE]:
                self.media_mode: MediaMode = MediaMode(data[ProtocolKey.MEDIA_MODE])

            if ProtocolKey.MEDIA_TYPE in data and data[ProtocolKey.MEDIA_TYPE]:
                self.media_type: MediaType = MediaType(data[ProtocolKey.MEDIA_TYPE])

            if ProtocolKey.PRODUCT_ID in data:
                self.product_id: int = data[ProtocolKey.PRODUCT_ID]

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
        return f"{self.id} ({self.file_path})"

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.ATTRIBUTION: self.attribution,
            ProtocolKey.CREATOR_ID: self.creator_id,
            ProtocolKey.FILE_PATH: self.file_path,
            ProtocolKey.ID: self.id,
            ProtocolKey.INDEX: self.index,
            ProtocolKey.MEDIA_MODE: self.media_mode,
            ProtocolKey.MEDIA_TYPE: self.media_type,
            ProtocolKey.PRODUCT_ID: self.product_id
        }

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        if self.creator:
            serialized[ProtocolKey.CREATOR] = self.creator.as_dict()

        return serialized

    @classmethod
    def create(cls: Type[T],
               attribution: str,
               creator_id: int,
               file_path: str,
               index: int,
               media_mode: MediaMode,
               media_type: MediaType,
               product_id: int) -> T:
        if attribution and not isinstance(attribution, str):
            raise TypeError(f"Argument 'attribution' must be of type str, not {type(attribution)}.")

        if not isinstance(creator_id, int):
            raise TypeError(f"Argument 'creator_id' must be of type int, not {type(creator_id)}.")

        if creator_id <= 0:
            raise ValueError("Argument 'creator_id' must be a positive, non-zero integer.")

        if not isinstance(file_path, str):
            raise TypeError(f"Argument 'file_path' must be of type str, not {type(file_path)}.")

        if not file_path:
            raise ValueError("Argument 'file_path' must be a non-empty string.")

        if not isinstance(index, int):
            raise TypeError(f"Argument 'index' must be of type int, not {type(index)}.")

        if index < 0:
            raise ValueError("Argument 'index' must be an integer greater than or equal to zero.")

        if not isinstance(media_mode, MediaMode):
            raise TypeError(f"Argument 'media_mode' must be of type MediaMode, not {type(media_mode)}.")

        if not isinstance(media_type, MediaType):
            raise TypeError(f"Argument 'media_type' must be of type MediaType, not {type(media_type)}.")

        if not isinstance(product_id, int):
            raise TypeError(f"Argument 'product_id' must be of type int, not {type(product_id)}.")

        if product_id <= 0:
            raise ValueError("Argument 'product_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.PRODUCT_MEDIUM}
                ({ProtocolKey.ATTRIBUTION}, {ProtocolKey.CREATOR_ID}, {ProtocolKey.FILE_PATH},
                {ProtocolKey.INDEX}, {ProtocolKey.MEDIA_MODE}, {ProtocolKey.MEDIA_TYPE},
                {ProtocolKey.PRODUCT_ID})
                VALUES
                (%s, %s, %s, 
                 %s, %s, %s,
                 %s)
                 RETURNING *;
                """,
                (attribution, creator_id, file_path,
                 index, media_mode.value, media_type.value,
                 product_id)
            )

            result = cursor.fetchone()
            conn.commit()

            if result:
                ret = cls(result)
                ret.creator = UserAccount.get_by_id(ret.creator_id)
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    def delete(self) -> None:
        """
        [NOTE] This method erases the medium's record from the database.
        """

        if not self.id:
            raise Exception("Medium has no ID associated with it.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.PRODUCT_MEDIUM}
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
    def get_all(cls: Type[T],
                product_id: int = None) -> list[T]:
        if not isinstance(product_id, int):
            raise TypeError(f"Argument 'product_id' must be of type int, not {type(product_id)}.")

        if product_id <= 0:
            raise ValueError("Argument 'product_id' must be a positive, non-zero integer.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.PRODUCT_MEDIUM}
                WHERE {ProtocolKey.PRODUCT_ID} = %s
                ORDER BY {ProtocolKey.INDEX} ASC;
                """,
                (product_id,)
            )
            results = cursor.fetchall()
            conn.commit()

            for result in results:
                medium = cls(result)
                medium.creator = UserAccount.get_by_id(medium.creator_id)
                ret.append(medium)
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    def update(self) -> None:
        if not self.id:
            raise Exception("Medium has no ID associated with it.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.PRODUCT_MEDIUM}
                SET {ProtocolKey.ATTRIBUTION} = %s, {ProtocolKey.INDEX} = %s
                WHERE {ProtocolKey.ID} = %s;
                """,
                (self.attribution, self.index, self.id)
            )
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()


####################
# MODULE FUNCTIONS #
####################
