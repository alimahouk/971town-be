from typing import Any, TypeVar, Type

from app.config import DatabaseTable, ProtocolKey
from app.modules import db


###########
# CLASSES #
###########


T = TypeVar("T", bound="UserOS")


class UserOS:
    def __init__(self,
                 data: dict) -> None:
        self.id: int = 0
        self.name: str = None
        self.version: str = None

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
        ret = ""

        if self.id:
            ret += f"OS: {self.id}"

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

        return serialized

    @classmethod
    def create(cls: Type[T],
               os_name: str) -> T:
        if not isinstance(os_name, str):
            raise TypeError(f"Argument 'os_name' must be of type str, not {type(os_name)}.")

        if not os_name:
            raise ValueError("Argument 'os_name' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.USER_OS}
                ({ProtocolKey.NAME})
                VALUES (%s) RETURNING *;
                """,
                (os_name,)
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
            raise Exception("Deletion requires an OS ID.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.USER_OS}
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
    def get_by_id(cls: Type[T],
                  os_id: int) -> T:
        if not isinstance(os_id, int):
            raise TypeError(f"Argument 'os_id' must be of type int, not {type(os_id)}.")

        if os_id <= 0:
            raise ValueError("Argument 'os_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_OS}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (os_id,)
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
                    os_name: str) -> T:
        if not isinstance(os_name, str):
            raise TypeError(f"Argument 'os_name' must be of type str, not {type(os_name)}.")

        if not os_name:
            raise ValueError("Argument 'os_name' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_OS}
                WHERE {ProtocolKey.NAME} = %s;
                """,
                (os_name,)
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

    def update(self) -> None:
        if not self.id:
            raise Exception("Updating requires an OS ID.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.USER_OS}
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
