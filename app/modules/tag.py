from datetime import datetime
import string
from typing import Any, TypeVar, Type

from app.config import DatabaseTable, ProtocolKey
from app.modules import db


###########
# CLASSES #
###########


T = TypeVar("T", bound="Tag")


class Tag:
    def __init__(self,
                 data: dict) -> None:
        self.creation_timestamp: datetime = None
        self.creator_id: int = 0
        self.id: int = 0
        self.name: str = None

        if data:
            if ProtocolKey.CREATION_TIMESTAMP in data:
                self.creation_timestamp: datetime = data[ProtocolKey.CREATION_TIMESTAMP]

            if ProtocolKey.CREATOR_ID in data:
                self.creator_id: int = data[ProtocolKey.CREATOR_ID]

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
        return self.name

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.CREATOR_ID: self.creator_id,
            ProtocolKey.ID: self.id,
            ProtocolKey.NAME: self.name
        }

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        return serialized

    @classmethod
    def create(cls: Type[T],
               name: str,
               creator_id: int) -> T:
        """
        [NOTE] Tags are stored in lowercase.
        """

        if not isinstance(name, str):
            raise TypeError(f"Argument 'name' must be of type str, not {type(name)}.")

        if not name:
            raise ValueError("Argument 'name' must be a non-empty string.")

        if not isinstance(creator_id, int):
            raise TypeError(f"Argument 'creator_id' must be of type int, not {type(creator_id)}.")

        if creator_id <= 0:
            raise ValueError("Argument 'creator_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None
        # Tags cannot contain whitespace.
        name = "".join(char for char in name if char in string.printable)
        name = name.lower()

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.TAG}
                ({ProtocolKey.NAME}, {ProtocolKey.CREATOR_ID})
                VALUES (%s, %s) RETURNING *;
                """,
                (name, creator_id)
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
    def get_all_by_user(cls: Type[T],
                        user_id: int) -> list[T]:
        if not isinstance(user_id, int):
            raise TypeError(f"Argument 'user_id' must be of type int, not {type(user_id)}.")

        if user_id <= 0:
            raise ValueError("Argument 'user_id' must be a positive, non-zero integer.")

        ret = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.TAG}
                WHERE {ProtocolKey.CREATOR_ID} = %s;
                """,
                (user_id,)
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
                  tag_id: int) -> T:
        if not isinstance(tag_id, int):
            raise TypeError(f"Argument 'tag_id' must be of type int, not {type(tag_id)}.")

        if tag_id <= 0:
            raise ValueError("Argument 'tag_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.TAG}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (tag_id,)
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
                    tag_name: str) -> T:
        if not isinstance(tag_name, str):
            raise TypeError(f"Argument 'tag_name' must be of type str, not {type(tag_name)}.")

        if not tag_name:
            raise ValueError("Argument 'tag_name' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None
        # Tags cannot contain whitespace.
        tag_name = "".join(char for char in tag_name if char in string.printable)
        tag_name = tag_name.lower()

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.TAG}
                WHERE {ProtocolKey.NAME} = %s;
                """,
                (tag_name,)
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
