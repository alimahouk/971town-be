from datetime import datetime
import hashlib
from typing import Any, TypeVar, Type
import uuid

from app.config import DatabaseTable, ProtocolKey
from app.modules import db


###########
# CLASSES #
###########


T = TypeVar("T", bound="UserClient")


class UserClient:
    def __init__(self,
                 data: dict) -> None:
        self.creation_timestamp: datetime = None
        self.id: str = None
        self.name: str = None
        self.version: str = None

        if data:
            if ProtocolKey.CREATION_TIMESTAMP in data:
                self.creation_timestamp: datetime = data[ProtocolKey.CREATION_TIMESTAMP]

            if ProtocolKey.ID in data:
                self.id: str = data[ProtocolKey.ID]

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
        ret = ""

        if self.id:
            ret += f"Client: {self.id}"

        if self.name:
            ret += f" ({self.name}"

            if self.version:
                ret += f" {self.version})"
        elif self.version:
            ret += f" ({self.version})"

        return ret

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.ID: self.id,
            ProtocolKey.NAME: self.name,
            ProtocolKey.VERSION: self.version
        }

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        return serialized

    @classmethod
    def create(cls: Type[T],
               client_id: str,
               client_name: str) -> T:
        if not isinstance(client_id, str):
            raise TypeError(f"Argument 'client_id' must be of type str, not {type(client_id)}.")

        if not client_id:
            raise ValueError("Argument 'client_id' must be a non-empty string.")

        if not isinstance(client_name, str):
            raise TypeError(f"Argument 'client_name' must be of type str, not {type(client_name)}.")

        if not client_name:
            raise ValueError("Argument 'client_name' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.USER_CLIENT}
                ({ProtocolKey.ID}, {ProtocolKey.NAME})
                VALUES (%s, %s) RETURNING *;
                """,
                (client_id, client_name)
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
        if not self.id:
            raise Exception("Deletion requires a client ID.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.USER_CLIENT}
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

    @staticmethod
    def generate_id() -> str:
        """
        Generates a session ID.
        """
        rand = uuid.uuid4().hex

        return hashlib.sha256(rand.encode("utf-8")).hexdigest()

    @classmethod
    def get_by_id(cls: Type[T],
                  client_id: str) -> T:
        if not isinstance(client_id, str):
            raise TypeError(f"Argument 'client_id' must be of type str, not {type(client_id)}.")

        if not client_id:
            raise ValueError("Argument 'client_id' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_CLIENT}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (client_id,)
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
                    client_name: str) -> T:
        if not isinstance(client_name, str):
            raise TypeError(f"Argument 'client_name' must be of type str, not {type(client_name)}.")

        if not client_name:
            raise ValueError("Argument 'client_name' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_CLIENT}
                WHERE {ProtocolKey.NAME} = %s;
                """,
                (client_name,)
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

    @staticmethod
    def id_exists(client_id: str) -> bool:
        if not isinstance(client_id, str):
            raise TypeError(f"Argument 'client_id' must be of type str, not {type(client_id)}.")

        if not client_id:
            raise ValueError("Argument 'client_id' must be a non-empty string.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_CLIENT}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (client_id,)
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

    def update(self) -> None:
        if not self.id:
            raise Exception("Updating requires a client ID.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.USER_CLIENT}
                SET {ProtocolKey.NAME} = %s
                WHERE {ProtocolKey.ID} = %s;
                """,
                (self.name, self.id)
            )
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()
