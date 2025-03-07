from datetime import datetime
from typing import Any, TypeVar, Type

from app.config import DatabaseTable, ProtocolKey, ResponseStatus
from app.modules import db
from app.modules.country import Country


###########
# CLASSES #
###########


T = TypeVar("T", bound="Locality")


class Locality:
    def __init__(self,
                 data: dict) -> None:
        self.country: Country = None
        self.creation_timestamp: datetime = None
        self.id: int = 0
        self.name: str = None

        if data:
            if ProtocolKey.ALPHA_2_CODE in data and data[ProtocolKey.ALPHA_2_CODE]:
                self.country: Country = Country.get_by_alpha_2_code(data[ProtocolKey.ALPHA_2_CODE])

            if ProtocolKey.CREATION_TIMESTAMP in data:
                self.creation_timestamp: datetime = data[ProtocolKey.CREATION_TIMESTAMP]

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
            ProtocolKey.ID: self.id,
            ProtocolKey.NAME: self.name
        }

        if self.country:
            serialized[ProtocolKey.COUNTRY] = self.country.as_dict()

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        return serialized

    @staticmethod
    def clean(name: str) -> str:
        """
        A clean name has no whitespaces, is lowercase, and only contains alphanumeric
        characters.
        """

        invisible = frozenset([" "])
        punctuation = frozenset(
            [",", ";", ".",
             "-", "–", "_",
             "/", "\\", "(",
             ")", "[", "]",
             "<", ">", "!",
             "?", "~", "'",
             "\"", "`", "|",
             "@", "#", "$",
             "%", "^", "*",
             "+", "=", "±",
             "{", "}"]
        )
        name_clean = name.strip()
        name_clean = name_clean.replace("&", "and")
        name_clean = "".join(char for char in name_clean if char not in invisible)
        name_clean = "".join(char for char in name_clean if char not in punctuation)
        name_clean = name_clean.lower()

        return name_clean

    @classmethod
    def create(cls: Type[T],
               alpha_2_code: str,
               name: str) -> T:
        if not isinstance(alpha_2_code, str):
            raise TypeError(f"Argument 'alpha_2_code' must be of type str, not {type(alpha_2_code)}.")

        if not alpha_2_code:
            raise ValueError("Argument 'alpha_2_code' must be a non-empty string.")

        if not isinstance(name, str):
            raise TypeError(f"Argument 'name' must be of type str, not {type(name)}.")

        if not name:
            raise ValueError("Argument 'name' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None
        name_clean = cls.clean(name)

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.LOCALITY}
                ({ProtocolKey.ALPHA_2_CODE}, {ProtocolKey.NAME}, {ProtocolKey.NAME_CLEAN})
                VALUES (%s, %s, %s) RETURNING *;
                """,
                (alpha_2_code, name, name_clean)
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
    def get_all(cls: Type[T],
                query: str) -> list[T]:
        if not isinstance(query, str):
            raise TypeError(f"Argument 'query' must be of type str, not {type(query)}.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT *, ts_rank(match.{ProtocolKey.POSTGRES_SEARCH_NAME}, plainto_tsquery('english', %s)) AS rank FROM
                (SELECT * FROM {DatabaseTable.LOCALITY}
                WHERE {ProtocolKey.POSTGRES_SEARCH_NAME} @@ plainto_tsquery('english', %s))
                AS match
                ORDER BY rank DESC
                LIMIT 20;
                """,
                (query, query)
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
    def get_all_by_country(cls: Type[T],
                           alpha_2_code: int) -> list[T]:
        if not isinstance(alpha_2_code, str):
            raise TypeError(f"Argument 'alpha_2_code' must be of type str, not {type(alpha_2_code)}.")

        if not alpha_2_code:
            raise ValueError("Argument 'alpha_2_code' must be a non-empty string.")

        ret = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.LOCALITY}
                WHERE {ProtocolKey.ALPHA_2_CODE} = %s;
                """,
                (alpha_2_code,)
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
                  locality_id: int) -> T:
        if not isinstance(locality_id, int):
            raise TypeError(f"Argument 'locality_id' must be of type int, not {type(locality_id)}.")

        if locality_id <= 0:
            raise ValueError("Argument 'locality_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.LOCALITY}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (locality_id,)
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
                    locality_name: str) -> T:
        if not isinstance(locality_name, str):
            raise TypeError(f"Argument 'locality_name' must be of type str, not {type(locality_name)}.")

        if not locality_name:
            raise ValueError("Argument 'locality_name' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None
        locality_name = cls.clean(locality_name)

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.LOCALITY}
                WHERE {ProtocolKey.NAME_CLEAN} = %s;
                """,
                (locality_name,)
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


def get_localities(query: str) -> tuple[dict, ResponseStatus]:
    query = query.strip()
    response_status = ResponseStatus.OK
    serialized = []

    if query:
        results = Locality.get_all(query)

        for result in results:
            serialized.append(result.as_dict())

    response = {
        ProtocolKey.LOCALITIES: serialized
    }

    return (response, response_status)
