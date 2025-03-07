from datetime import datetime
from typing import Any, TypeVar, Type

from app.config import DatabaseTable, ProtocolKey
from app.modules import db


###########
# CLASSES #
###########


T = TypeVar("T", bound="UserShadowBan")


class UserShadowBan:
    def __init__(self,
                 data: dict) -> None:
        self.creation_timestamp: datetime = None
        self.imposer_id: int = 0
        self.store_id: int = 0
        self.user_id: int = 0

        if data:
            if ProtocolKey.CREATION_TIMESTAMP in data:
                self.creation_timestamp: datetime = data[ProtocolKey.CREATION_TIMESTAMP]

            if ProtocolKey.IMPOSER_ID in data:
                self.imposer_id: int = data[ProtocolKey.IMPOSER_ID]

            if ProtocolKey.STORE_ID in data:
                self.store_id: int = data[ProtocolKey.STORE_ID]

            if ProtocolKey.USER_ID in data:
                self.user_id: int = data[ProtocolKey.USER_ID]

    def __eq__(self,
               __o: object) -> bool:
        ret = False

        if isinstance(__o, type(self)) and \
                self.user_id == __o.user_id and \
                self.store_id == __o.store_id:
            ret = True

        return ret

    def __hash__(self) -> int:
        return hash((self.user_id, self.store_id))

    def __repr__(self) -> str:
        return f"Shadow Ban (User: {self.user_id.__str__()}, Store: {self.store_id.__str__()})"

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.IMPOSER_ID: self.imposer_id,
            ProtocolKey.STORE_ID: self.store_id,
            ProtocolKey.USER_ID: self.user_id
        }

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        return serialized

    @classmethod
    def create(cls: Type[T],
               imposer_id: int,
               store_id: int,
               user_id: int) -> T:
        if not isinstance(imposer_id, int):
            raise TypeError(f"Argument 'imposer_id' must be of type int, not {type(imposer_id)}.")

        if imposer_id <= 0:
            raise ValueError("Argument 'imposer_id' must be a positive, non-zero integer.")

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
                INSERT INTO {DatabaseTable.USER_SHADOW_BAN}
                ({ProtocolKey.IMPOSER_ID}, {ProtocolKey.STORE_ID}, {ProtocolKey.USER_ID})
                VALUES (%s, %s, %s) RETURNING *;
                """,
                (imposer_id, store_id, user_id)
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
                DELETE FROM {DatabaseTable.USER_SHADOW_BAN}
                WHERE {ProtocolKey.STORE_ID} = %s AND {ProtocolKey.USER_ID} = %s;
                """,
                (self.store_id, self.user_id)
            )
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

    @staticmethod
    def delete_all_for_store(store_id: int) -> None:
        if not isinstance(store_id, int):
            raise TypeError(f"Argument 'store_id' must be of type int, not {type(store_id)}.")

        if store_id <= 0:
            raise ValueError("Argument 'store_id' must be a positive, non-zero integer.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.USER_SHADOW_BAN}
                WHERE {ProtocolKey.STORE_ID} = %s;
                """,
                (store_id,)
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
    def get_all_for_user(cls: Type[T],
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
                f"""SELECT * FROM {DatabaseTable.USER_SHADOW_BAN}
                WHERE {ProtocolKey.USER_ID} = %s;""",
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
