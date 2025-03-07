from datetime import datetime
from flask import request
import re
import string
from psycopg2 import InterfaceError
from psycopg2.extensions import adapt, register_adapter, AsIs
from typing import Any, TypeVar, Type
from urllib.parse import urlparse

from app.config import Configuration, ContentVisibility, DatabaseTable, \
    EditAccessLevel, EntityType, ProtocolKey, \
    ResponseStatus, StoreStatus
from app.modules import db
from app.modules.brand import Brand
from app.modules.country import Country
from app.modules.locality import Locality
from app.modules.tag import Tag
from app.modules.user_account import UserAccount


###########
# CLASSES #
###########


T = TypeVar("T", bound="Store")


class Point:
    def __init__(self,
                 x: float,
                 y: float) -> None:
        """
        :param x: Longitude
        :type x: float
        :param y: Latitude
        :type y: float
        """
        self.x = x
        self.y = y

    @staticmethod
    def adapt_point(point):
        x = adapt(point.x).getquoted().decode("utf-8")
        y = adapt(point.y).getquoted().decode("utf-8")

        return AsIs("'SRID=4326;POINT(%s %s)'" % (x, y))

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.LONGITUDE: self.x,
            ProtocolKey.LATITUDE: self.y
        }

        return serialized

    @staticmethod
    def cast_point(value):
        ret = None

        if value:
            points: str = value[value.find("(") + 1:value.find(")")]

            if points:
                parts = points.split()

                ret = Point(float(parts[0]), float(parts[1]))
            else:
                raise InterfaceError("Bad point representation: %r" % value)

        return ret

    @staticmethod
    def set_up() -> None:
        register_adapter(Point, Point.adapt_point)


Point.set_up()


class PhysicalAddress:
    def __init__(self) -> None:
        self.building: str = None
        self.coordinates: Point = None
        self.floor: str = None
        self.locality: Locality = None
        self.post_code: str = None
        self.street: str = None
        self.unit: str = None

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.BUILDING: self.building,
            ProtocolKey.FLOOR: self.floor,
            ProtocolKey.POST_CODE: self.post_code,
            ProtocolKey.STREET: self.street,
            ProtocolKey.UNIT: self.unit
        }

        if self.coordinates:
            serialized[ProtocolKey.COORDINATES] = self.coordinates.as_dict()

        if self.locality:
            serialized[ProtocolKey.LOCALITY] = self.locality.as_dict()

        return serialized


class Store:
    def __init__(self,
                 data: dict) -> None:
        self.address: PhysicalAddress = PhysicalAddress()
        self.alias: str = None
        self.brand: Brand = None
        self.creation_timestamp: datetime = None
        self.creator: UserAccount = None
        self.creator_id: int = 0
        self.description: str = None
        self.edit_access_level: EditAccessLevel = EditAccessLevel.OPEN
        self.id: int = 0
        self.name: str = None
        self.status: StoreStatus = StoreStatus.OPEN
        self.tags: set[Tag] = set()
        self.visibility: ContentVisibility = ContentVisibility.PUBLICLY_VISIBLE
        self.website: str = None

        if data:
            if ProtocolKey.ALIAS in data:
                self.alias: str = data[ProtocolKey.ALIAS]

            if ProtocolKey.BRAND_ID in data and data[ProtocolKey.BRAND_ID]:
                self.brand = Brand.get_by_id(data[ProtocolKey.BRAND_ID])

            if ProtocolKey.BUILDING in data:
                self.address.building: str = data[ProtocolKey.BUILDING]

            if ProtocolKey.COORDINATES_TEXT in data:
                self.address.coordinates: Point = Point.cast_point(data[ProtocolKey.COORDINATES_TEXT])

            if ProtocolKey.CREATION_TIMESTAMP in data:
                self.creation_timestamp: datetime = data[ProtocolKey.CREATION_TIMESTAMP]

            if ProtocolKey.CREATOR_ID in data:
                self.creator_id: int = data[ProtocolKey.CREATOR_ID]

            if ProtocolKey.DESCRIPTION in data:
                self.description: str = data[ProtocolKey.DESCRIPTION]

            if ProtocolKey.EDIT_ACCESS_LEVEL in data and data[ProtocolKey.EDIT_ACCESS_LEVEL]:
                self.edit_access_level = EditAccessLevel(data[ProtocolKey.EDIT_ACCESS_LEVEL])

            if ProtocolKey.FLOOR in data:
                self.address.floor: str = data[ProtocolKey.FLOOR]

            if ProtocolKey.ID in data:
                self.id: int = data[ProtocolKey.ID]

            if ProtocolKey.LOCALITY_ID in data and data[ProtocolKey.LOCALITY_ID]:
                self.address.locality = Locality.get_by_id(data[ProtocolKey.LOCALITY_ID])

            if ProtocolKey.NAME in data:
                self.name: str = data[ProtocolKey.NAME]

            if ProtocolKey.POST_CODE in data:
                self.address.post_code: str = data[ProtocolKey.POST_CODE]

            if ProtocolKey.STATUS in data and data[ProtocolKey.STATUS]:
                self.status = StoreStatus(data[ProtocolKey.STATUS])

            if ProtocolKey.STREET in data:
                self.address.street: str = data[ProtocolKey.STREET]

            if ProtocolKey.UNIT in data:
                self.address.unit: str = data[ProtocolKey.UNIT]

            if ProtocolKey.VISIBILITY in data and data[ProtocolKey.VISIBILITY]:
                self.visibility = EditAccessLevel(data[ProtocolKey.VISIBILITY])

            if ProtocolKey.WEBSITE in data:
                self.website: str = data[ProtocolKey.WEBSITE]

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
        ret = "Store " + self.id.__str__()

        if self.name:
            ret += f" ({self.name})"

        return ret

    @staticmethod
    def alias_exists(alias: str) -> bool:
        """
        Compares against aliases in the stores table.
        Avoid using this method and use the one in the common module,
        which compares aliases globally.
        """

        if not isinstance(alias, str):
            raise TypeError(f"Argument 'alias' must be of type str, not {type(alias)}.")

        if not alias:
            raise ValueError("Argument 'alias' must be a non-empty string.")

        ret = False
        conn = None
        cursor = None
        alias = alias.lower()

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.ALIAS}
                WHERE {ProtocolKey.ALIAS} = %s;
                """,
                (alias,)
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

    @staticmethod
    def alias_valid(alias: str) -> bool:
        ret = True

        if not alias:
            ret = False
        else:
            pattern = re.compile(
                f"^(?=.{{{Configuration.ALIAS_MIN_LEN},{Configuration.ALIAS_MAX_LEN}}}$)(?![_.])[a-zA-Z0-9._-]+(?<![_.])$")
            ret = pattern.match(alias)

        return ret

    def as_dict(self) -> dict[ProtocolKey, Any]:
        tags_serialized = []

        if self.tags:
            for tag in self.tags:
                tags_serialized.append(tag.as_dict())

        serialized = {
            ProtocolKey.ALIAS: self.alias,
            ProtocolKey.CREATOR_ID: self.creator_id,
            ProtocolKey.DESCRIPTION: self.description,
            ProtocolKey.ID: self.id,
            ProtocolKey.NAME: self.name,
            ProtocolKey.TAGS: tags_serialized,
            ProtocolKey.WEBSITE: self.website
        }

        if self.address:
            serialized[ProtocolKey.ADDRESS] = self.address.as_dict()

        if self.brand:
            serialized[ProtocolKey.BRAND] = self.brand.as_dict()

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        if self.creator:
            serialized[ProtocolKey.CREATOR] = self.creator.as_dict()

        if self.edit_access_level:
            serialized[ProtocolKey.EDIT_ACCESS_LEVEL] = self.edit_access_level.value

        if self.status:
            serialized[ProtocolKey.STATUS] = self.status.value

        if self.visibility:
            serialized[ProtocolKey.VISIBILITY] = self.visibility.value

        return serialized

    @classmethod
    def create(cls: Type[T],
               alias: str,
               brand_id: int,
               coordinates: Point,
               creator_id: int,
               locality_id: int,
               name: str,
               status: StoreStatus) -> T:
        if not isinstance(alias, str):
            raise TypeError(f"Argument 'alias' must be of type str, not {type(alias)}.")

        alias = "".join(char for char in alias if char in string.printable)

        if not alias:
            raise ValueError("Argument 'alias' must be a non-empty string.")

        if not isinstance(brand_id, int):
            raise TypeError(f"Argument 'brand_id' must be of type int, not {type(brand_id)}.")

        if brand_id <= 0:
            raise ValueError("Argument 'brand_id' must be a positive, non-zero integer.")

        if not isinstance(coordinates, Point):
            raise TypeError(f"Argument 'coordinates' must be of type Point, not {type(coordinates)}.")

        if not isinstance(creator_id, int):
            raise TypeError(f"Argument 'creator_id' must be of type int, not {type(creator_id)}.")

        if creator_id <= 0:
            raise ValueError("Argument 'creator_id' must be a positive, non-zero integer.")

        if not isinstance(locality_id, int):
            raise TypeError(f"Argument 'locality_id' must be of type int, not {type(locality_id)}.")

        if locality_id <= 0:
            raise ValueError("Argument 'locality_id' must be a positive, non-zero integer.")

        if not isinstance(name, str):
            raise TypeError(f"Argument 'name' must be of type str, not {type(name)}.")

        if not name:
            raise ValueError("Argument 'name' must be a non-empty string.")

        if not isinstance(status, StoreStatus):
            raise TypeError(f"Argument 'status' must be of type StoreStatus, not {type(status)}.")

        ret: Type[T] = None
        conn = None
        cursor = None
        alias = alias.lower()

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.STORE}
                ({ProtocolKey.ALIAS}, {ProtocolKey.BRAND_ID}, {ProtocolKey.COORDINATES},
                  {ProtocolKey.CREATOR_ID}, {ProtocolKey.NAME}, {ProtocolKey.LOCALITY_ID},
                  {ProtocolKey.STATUS})
                VALUES
                (%s, %s, %s, 
                 %s, %s, %s, 
                 %s)
                RETURNING *;
                """,
                (alias, brand_id, coordinates,
                 creator_id, name, locality_id,
                 status.value)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                ret = cls(result)

                cursor.execute(
                    f"""
                    INSERT INTO {DatabaseTable.ALIAS}
                    ({ProtocolKey.ID}, {ProtocolKey.ALIAS}, {ProtocolKey.ENTITY_TYPE})
                    VALUES (%s, %s, %s);
                    """,
                    (ret.id, alias, EntityType.STORE)
                )
                conn.commit()
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    def create_manager(self,
                       account_id: int) -> None:
        if not isinstance(account_id, int):
            raise TypeError(f"Argument 'account_id' must be of type int, not {type(account_id)}.")

        if account_id <= 0:
            raise ValueError("Argument 'account_id' must be a positive, non-zero integer.")

        if not self.id:
            raise Exception("Store has no ID associated with it.")

        if not Store.is_manager(account_id, self.id):
            conn = None
            cursor = None

            try:
                conn = db.connect()
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    INSERT INTO {DatabaseTable.STORE_MANAGER}
                    ({ProtocolKey.USER_ACCOUNT_ID}, {ProtocolKey.STORE_ID})
                    VALUES (%s, %s);
                    """,
                    (account_id, self.id)
                )
                conn.commit()
            except Exception as e:
                print(e)
            finally:
                if cursor:
                    cursor.close()

                if conn:
                    conn.close()

    def delete(self) -> None:
        """
        [NOTE] This method erases the store's record from the database.
        """

        if not self.id and not self.alias:
            raise Exception("Deletion requires either a store ID or alias.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()

            if self.id:
                cursor.execute(
                    f"""
                    DELETE FROM {DatabaseTable.STORE}
                    WHERE {ProtocolKey.ID} = %s;
                    """,
                    (self.id,)
                )
            else:
                cursor.execute(
                    f"""
                    DELETE FROM {DatabaseTable.STORE}
                    WHERE {ProtocolKey.ALIAS} = %s;
                    """,
                    (self.alias,)
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
                (SELECT *, ST_AsText(coordinates) as {ProtocolKey.COORDINATES_TEXT}
                FROM {DatabaseTable.STORE}
                WHERE {ProtocolKey.POSTGRES_SEARCH_NAME} @@ plainto_tsquery('english', %s)
                AND {ProtocolKey.VISIBILITY} NOT IN ({ContentVisibility.DELETED.value}, {ContentVisibility.GHOSTED.value}, {ContentVisibility.REMOVED.value}))
                AS match
                ORDER BY rank DESC;
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
    def get_all_by_user(cls: Type[T],
                        user_id: int) -> list[T]:
        if not isinstance(user_id, int):
            raise TypeError(f"Argument 'user_id' must be of type int, not {type(user_id)}.")

        if user_id <= 0:
            raise ValueError("Argument 'user_id' must be a positive, non-zero integer.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT *, ST_AsText(coordinates) as {ProtocolKey.COORDINATES_TEXT}
                FROM {DatabaseTable.STORE}
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
    def get_by_alias(cls: Type[T],
                     alias: str) -> T:
        if not isinstance(alias, str):
            raise TypeError(f"Argument 'alias' must be of type str, not {type(alias)}.")

        if not alias:
            raise ValueError("Argument 'alias' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None
        alias = alias.lower()

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT *, ST_AsText(coordinates) as {ProtocolKey.COORDINATES_TEXT}
                FROM {DatabaseTable.STORE}
                WHERE {ProtocolKey.ALIAS} = %s;
                """,
                (alias,)
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

    @classmethod
    def get_by_id(cls: Type[T],
                  store_id: int) -> T:
        if not isinstance(store_id, int):
            raise TypeError(f"Argument 'store_id' must be of type int, not {type(store_id)}.")

        if store_id <= 0:
            raise ValueError("Argument 'store_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT *, ST_AsText(coordinates) as {ProtocolKey.COORDINATES_TEXT}
                FROM {DatabaseTable.STORE}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (store_id,)
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

    @staticmethod
    def get_id_for_alias(alias: str) -> int:
        if not isinstance(alias, str):
            raise TypeError(f"Argument 'alias' must be of type str, not {type(alias)}.")

        if not alias:
            raise ValueError("Argument 'alias' must be a non-empty string.")

        ret: int = 0
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.STORE}
                WHERE {ProtocolKey.ALIAS} = %s;
                """,
                (alias,)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                ret = result[ProtocolKey.ID]
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    @classmethod
    def get_nearby(cls: Type[T],
                   coordinates: Point,
                   radius: int = 1000) -> list[T]:
        """
        :param radius: The search radius in meters.
        :type radius: int
        """

        if not isinstance(coordinates, Point):
            raise TypeError(f"Argument 'coordinates' must be of type Point, not {type(coordinates)}.")

        if not isinstance(radius, int):
            raise TypeError(f"Argument 'radius' must be of type int, not {type(radius)}.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT *, ST_AsText(coordinates) as {ProtocolKey.COORDINATES_TEXT}
                FROM {DatabaseTable.STORE}
                WHERE ST_DWithin({ProtocolKey.COORDINATES}::geography,
                                 ST_GeogFromText(%s),
                                 %s, false)
                AND {ProtocolKey.VISIBILITY} NOT IN ({ContentVisibility.DELETED.value}, {ContentVisibility.GHOSTED.value}, {ContentVisibility.REMOVED.value})
                LIMIT 20;
                """,
                (coordinates, radius)
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

    @staticmethod
    def get_tags(store_id: int) -> list[Tag]:
        if not isinstance(store_id, int):
            raise TypeError(f"Argument 'store_id' must be of type int, not {type(store_id)}.")

        if store_id <= 0:
            raise ValueError("Argument 'store_id' must be a positive, non-zero integer.")

        ret: list[Tag] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT *
                FROM {DatabaseTable.TAG}
                INNER JOIN {DatabaseTable.STORE_TAG} ON {DatabaseTable.STORE_TAG}.{ProtocolKey.TAG_ID} = {DatabaseTable.TAG}.{ProtocolKey.ID}
                WHERE {DatabaseTable.STORE_TAG}.{ProtocolKey.STORE_ID} = %s;
                """,
                (store_id,)
            )
            results = cursor.fetchall()
            conn.commit()

            for result in results:
                ret.append(Tag(result))
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    @staticmethod
    def id_exists(store_id: int) -> bool:
        if not isinstance(store_id, int):
            raise TypeError(f"Argument 'store_id' must be of type int, not {type(store_id)}.")

        if store_id <= 0:
            raise ValueError("Argument 'store_id' must be a positive, non-zero integer.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.STORE}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (store_id,)
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

    @staticmethod
    def is_manager(account_id: int,
                   store_id: int) -> bool:
        if not isinstance(account_id, int):
            raise TypeError(f"Argument 'account_id' must be of type int, not {type(account_id)}.")

        if account_id <= 0:
            raise ValueError("Argument 'account_id' must be a positive, non-zero integer.")

        if not isinstance(store_id, int):
            raise TypeError(f"Argument 'store_id' must be of type int, not {type(store_id)}.")

        if store_id <= 0:
            raise ValueError("Argument 'store_id' must be a positive, non-zero integer.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.STORE_MANAGER}
                WHERE {ProtocolKey.USER_ACCOUNT_ID} = %s AND {ProtocolKey.STORE_ID} = %s;
                """,
                (account_id, store_id)
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

    def managers(self) -> list[UserAccount]:
        if not self.id:
            raise Exception("Store has no ID associated with it.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.STORE}
                RIGHT JOIN ON {DatabaseTable.STORE_MANAGER}.{ProtocolKey.USER_ACCOUNT_ID} = {DatabaseTable.USER_ACCOUNT}.{ProtocolKey.ID}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (self.id,)
            )
            results = cursor.fetchall()
            conn.commit()

            for result in results:
                ret.append(UserAccount(result))
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    def set_edit_access_level(self,
                              edit_access_level: EditAccessLevel):
        if not isinstance(edit_access_level, EditAccessLevel):
            raise TypeError(
                f"Argument 'edit_access_level' must be of type EditAccessLevel, not {type(edit_access_level)}.")

        if not edit_access_level:
            raise ValueError("Argument 'edit_access_level' is None.")

        if not self.id:
            raise Exception("Store has no ID associated with it.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.STORE}
                SET {ProtocolKey.EDIT_ACCESS_LEVEL} = %s
                WHERE {ProtocolKey.ID} = %s;
                """,
                (edit_access_level.value, self.id)
            )
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

    def set_visibility(self,
                       visibility: ContentVisibility):
        """
        [NOTE] This method does not delete the store's record from the database.
        """

        if not isinstance(visibility, ContentVisibility):
            raise TypeError(f"Argument 'visibility' must be of type ContentVisibility, not {type(visibility)}.")

        if not visibility:
            raise ValueError("Argument 'visibility' is None.")

        if not self.id:
            raise Exception("Store has no ID associated with it.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.STORE}
                SET {ProtocolKey.VISIBILITY} = %s
                WHERE {ProtocolKey.ID} = %s;
                """,
                (visibility.value, self.id)
            )
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

    def update(self) -> None:
        if not self.alias:
            raise Exception("Store must have an alias associated with it.")

        if not self.id:
            raise Exception("Store has no ID associated with it.")

        if not self.name:
            raise Exception("Store must have a name associated with it.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.STORE}
                SET {ProtocolKey.BUILDING} = %s, {ProtocolKey.COORDINATES} = %s, {ProtocolKey.FLOOR} = %s,
                {ProtocolKey.LOCALITY_ID} = %s, {ProtocolKey.POST_CODE} = %s, {ProtocolKey.STATUS} = %s
                {ProtocolKey.STREET} = %s, {ProtocolKey.UNIT} = %s, {ProtocolKey.DESCRIPTION} = %s, 
                {ProtocolKey.NAME} = %s, {ProtocolKey.WEBSITE} = %s
                WHERE {ProtocolKey.ID} = %s;
                """,
                (self.address.building, self.address.coordinates, self.address.floor,
                 self.address.locality.id, self.address.post_code, self.status.value,
                 self.address.street, self.address.unit, self.description,
                 self.name, self.website, self.id)
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


def create_store(alias: str,
                 brand_id: str,
                 latitude: str,
                 longitude: str,
                 locality_alpha_2_code: str,
                 locality_name: str,
                 name: str,
                 tags: str) -> tuple[dict, ResponseStatus]:
    if brand_id:
        try:
            brand_id = int(brand_id)

            if brand_id <= 0:
                brand_id = None
        except ValueError:
            brand_id = None
    else:
        brand_id = None

    if latitude:
        try:
            latitude = float(latitude)
        except ValueError:
            latitude = None
    else:
        latitude = None

    if longitude:
        try:
            longitude = float(longitude)
        except ValueError:
            longitude = None
    else:
        longitude = None

    if locality_alpha_2_code:
        locality_alpha_2_code = "".join(char for char in locality_alpha_2_code if char in string.printable)
    else:
        locality_alpha_2_code = None

    if locality_name:
        locality_name = locality_name.strip()
    else:
        locality_name = None

    if name:
        name = name.strip()
    else:
        name = None

    if not alias or \
            not brand_id or \
            not latitude or \
            not longitude or \
            not locality_alpha_2_code or \
            not locality_name or \
            not name:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not alias:
            error_message += ": 'alias' must be an ASCII non-empty string."
        elif not brand_id:
            error_message += ": 'brand_id' must be a positive, non-zero integer."
        elif not latitude:
            error_message += ": 'latitude' must be a non-empty string."
        elif not longitude:
            error_message += ": 'longitude' must be a non-empty string."
        elif not locality_alpha_2_code:
            error_message += ": 'locality_alpha_2_code' must be a non-empty string."
        elif not locality_name:
            error_message += ": 'locality_name' must be a non-empty string."
        elif not name:
            error_message += ": 'name' must be a non-empty string."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}
        alias = alias.lower()

        if Store.alias_valid(alias):
            if not Store.alias_exists(alias):
                brand = Brand.get_by_id(brand_id)

                if brand and \
                        brand.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
                    if Country.alpha_2_code_exists(locality_alpha_2_code):
                        session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
                        creator = UserAccount.get_by_session(session_id)
                        coordinates = Point(longitude, latitude)
                        locality = Locality.get_by_name(locality_name)

                        if not locality:
                            locality = Locality.create(locality_alpha_2_code, locality_name)

                        store = Store.create(
                            alias,
                            brand_id,
                            coordinates,
                            creator.id,
                            locality.id,
                            name,
                            StoreStatus.OPEN
                        )

                        if store:
                            store.create_manager(creator.id)

                            response = {
                                ProtocolKey.STORE: store.as_dict()
                            }
                        else:
                            response_status = ResponseStatus.INTERNAL_SERVER_ERROR
                            response = {
                                ProtocolKey.ERROR: {
                                    ProtocolKey.ERROR_CODE: response_status.value,
                                    ProtocolKey.ERROR_MESSAGE: f"An error occurred while trying to add the store."
                                }
                            }
                    else:
                        # Invalid country code.
                        response_status = ResponseStatus.BAD_REQUEST
                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: ResponseStatus.ALPHA_2_CODE_INVALID.value,
                                ProtocolKey.ERROR_MESSAGE: f"Invalid alpha-2 code."
                            }
                        }
                else:
                    # Invalid brand ID.
                    response_status = ResponseStatus.BAD_REQUEST
                    response = {
                        ProtocolKey.ERROR: {
                            ProtocolKey.ERROR_CODE: ResponseStatus.BRAND_NOT_FOUND.value,
                            ProtocolKey.ERROR_MESSAGE: f"Invalid brand ID."
                        }
                    }
            else:
                # Alias is taken.
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.ALIAS_EXISTS.value,
                        ProtocolKey.ERROR_MESSAGE: "Alias already in use."
                    }
                }
        else:
            # Invalid alias.
            response_status = ResponseStatus.BAD_REQUEST
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.ALIAS_INVALID.value,
                    ProtocolKey.ERROR_MESSAGE: f"Alias format is invalid. An alias must be between {Configuration.ALIAS_MIN_LEN} and {Configuration.ALIAS_MAX_LEN} characters long and can only contain dots, dashes, underscores, and alphanumeric ASCII characters."
                }
            }

    return (response, response_status)


def delete_store(store_id: str) -> tuple[dict, ResponseStatus]:
    if store_id:
        try:
            store_id = int(store_id)

            if store_id <= 0:
                store_id = None
        except ValueError:
            store_id = None

    if not store_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'store_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}
        store = Store.get_by_id(store_id)

        if store:
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
            user_account = UserAccount.get_by_session(session_id)

            if user_account.is_admin:
                store.delete()

                response = {
                    ProtocolKey.STORE_ID: store.id
                }
            else:
                response_status = ResponseStatus.FORBIDDEN
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: response_status.value,
                        ProtocolKey.ERROR_MESSAGE: "User account is not an admin. Only admins can delete."
                    }
                }
        else:
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.STORE_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No store exists for this ID."
                }
            }

    return (response, response_status)


def get_store(alias: str = None,
              store_id: str = None) -> tuple[dict, ResponseStatus]:
    if store_id:
        try:
            store_id = int(store_id)

            if store_id <= 0:
                store_id = None
        except ValueError:
            store_id = None
    else:
        store_id = None

    if not alias and \
            not store_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'alias' must be a non-empty string or 'store_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}

        if store_id:
            store = Store.get_by_id(store_id)
        else:
            if Store.alias_valid(alias):
                store = Store.get_by_alias(alias)
            else:
                # Invalid alias.
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.ALIAS_INVALID.value,
                        ProtocolKey.ERROR_MESSAGE: f"Alias format is invalid."
                    }
                }

        if response_status == ResponseStatus.OK:
            if store and \
                    store.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
                store.tags = Store.get_tags(store.id)

                response = {
                    ProtocolKey.STORE: store.as_dict()
                }
            else:
                response_status = ResponseStatus.NOT_FOUND
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.STORE_NOT_FOUND.value,
                        ProtocolKey.ERROR_MESSAGE: "No store exists for this alias/store ID."
                    }
                }

    return (response, response_status)


def get_stores(query: str = None,
               latitude: str = None,
               longitude: str = None) -> tuple[dict, ResponseStatus]:
    if latitude:
        try:
            latitude = float(latitude)
        except ValueError:
            latitude = None
    else:
        latitude = None

    if longitude:
        try:
            longitude = float(longitude)
        except ValueError:
            longitude = None
    else:
        longitude = None

    if (longitude and not latitude) or \
            (latitude and not longitude):
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: coordinates must include latitude and longitude."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        serialized = []

        if latitude and longitude:
            coordinates = Point(longitude, latitude)
            results = Store.get_nearby(coordinates)
        elif query:
            query = query.strip()
            results = Store.get_all(query)
        else:
            results = []

        for result in results:
            serialized.append(result.as_dict())

        response = {
            ProtocolKey.STORES: serialized
        }

    return (response, response_status)


def remove_store(store_id: str) -> tuple[dict, ResponseStatus]:
    if store_id:
        try:
            store_id = int(store_id)

            if store_id <= 0:
                store_id = None
        except ValueError:
            store_id = None
    else:
        store_id = None

    if not store_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'store_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}
        store = Store.get_by_id(store_id)

        if store and \
                store.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
            user_account = UserAccount.get_by_session(session_id)

            if user_account.is_admin or Store.is_manager(user_account.id, store_id):
                if user_account.id == store.creator_id:
                    visibility = ContentVisibility.DELETED
                else:
                    visibility = ContentVisibility.REMOVED

                store.set_visibility(visibility)

                response = {
                    ProtocolKey.VISIBILITY: visibility.value
                }
            else:
                response_status = ResponseStatus.FORBIDDEN
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: response_status.value,
                        ProtocolKey.ERROR_MESSAGE: "User account is neither an admin nor a manager of this store."
                    }
                }
        else:
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.STORE_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No store exists for this ID."
                }
            }

    return (response, response_status)


def update_store(building: str,
                 description: str,
                 floor: str,
                 latitude: str,
                 locality_alpha_2_code: str,
                 locality_name: str,
                 longitude: str,
                 name: str,
                 post_code: str,
                 status: str,
                 store_id: str,
                 street: str,
                 tags: str,
                 unit: str,
                 website: str) -> tuple[dict, ResponseStatus]:
    if building:
        building = building.strip()
    else:
        building = None

    if description:
        description = description.strip()
    else:
        description = None

    if floor:
        floor = floor.strip()
    else:
        floor = None

    if latitude:
        try:
            latitude = float(latitude)
        except ValueError:
            latitude = None
    else:
        latitude = None

    if locality_alpha_2_code:
        locality_alpha_2_code = "".join(char for char in locality_alpha_2_code if char in string.printable)
    else:
        locality_alpha_2_code = None

    if locality_name:
        locality_name = locality_name.strip()
    else:
        locality_name = None

    if longitude:
        try:
            longitude = float(longitude)
        except ValueError:
            longitude = None
    else:
        longitude = None

    if name:
        name = name.strip()
    else:
        name = None

    if post_code:
        post_code = post_code.strip()
    else:
        post_code = None

    if status:
        try:
            status = StoreStatus(int(status))
        except ValueError:
            status = None
    else:
        status = None

    if street:
        street = street.strip()
    else:
        street = None

    if unit:
        unit = unit.strip()
    else:
        unit = None

    if store_id:
        try:
            store_id = int(store_id)

            if store_id <= 0:
                store_id = None
        except ValueError:
            store_id = None
    else:
        store_id = None

    if website:
        website = "".join(char for char in website if char in string.printable)

        try:
            website_url_test = urlparse(website)

            if not website_url_test.scheme:
                website = "http://" + website
        except Exception:
            website = None
    else:
        website = None

    if not latitude or \
            not longitude or \
            not locality_alpha_2_code or \
            not locality_name or \
            not name or \
            not status or \
            not store_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not latitude:
            error_message += ": 'latitude' must be a non-empty string."
        elif not longitude:
            error_message += ": 'longitude' must be a non-empty string."
        elif not locality_alpha_2_code:
            error_message += ": 'locality_alpha_2_code' must be a non-empty string."
        elif not locality_name:
            error_message += ": 'locality_name' must be a non-empty string."
        elif not name:
            error_message += ": 'name' must be a non-empty string."
        elif not status:
            error_message += ": 'status' must be a positive, non-zero integer."
        elif not store_id:
            error_message += ": 'store_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}

        response_status = ResponseStatus.OK
        response = {}
        store = Store.get_by_id(store_id)

        if store and \
                store.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
            user_account = UserAccount.get_by_session(session_id)

            if store.edit_access_level == EditAccessLevel.OPEN or \
                    (store.edit_access_level == EditAccessLevel.PUBLICLY_ACCESSIBLE and Store.is_manager(user_account.id, store_id)) or \
                    user_account.is_admin:
                locality = Locality.get_by_name(locality_name)

                if not locality:
                    locality = Locality.create(locality_alpha_2_code, locality_name)

                store.address.building = building
                store.address.coordinates = Point(longitude, latitude)
                store.address.floor = floor
                store.address.locality = locality
                store.address.post_code = post_code
                store.address.street = street
                store.address.unit = unit
                store.description = description
                store.name = name
                store.status = status
                store.website = website
                store.update()

                response = {
                    ProtocolKey.STORE: store.as_dict()
                }
            else:
                response_status = ResponseStatus.FORBIDDEN
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: response_status.value,
                        ProtocolKey.ERROR_MESSAGE: "User account is neither an admin nor a manager of this store."
                    }
                }
        else:
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.STORE_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No store exists for this ID."
                }
            }

    return (response, response_status)
