from datetime import datetime
from dateutil import parser as date_parser
from flask import request
import hashlib
import json
import os
from PIL import Image
import re
import string
from typing import Any, TypeVar, Type
from urllib.parse import urlparse
from werkzeug.utils import secure_filename

from app import app
from app.config import (Configuration, ContentVisibility, DatabaseTable,
                        EditAccessLevel, EntityType, Field,
                        MediaMode, ProtocolKey, ResponseStatus,
                        UserAction)
from app.modules import db
from app.modules.s3 import s3
from app.modules.tag import Tag
from app.modules.user_account import UserAccount


###########
# CLASSES #
###########


T = TypeVar("T", bound="Brand")


class Brand:
    def __init__(self,
                 data: dict) -> None:
        self.alias: str = None
        self.avatar_light_path: str = None
        self.creation_timestamp: datetime = None
        self.creator: UserAccount = None
        self.creator_id: int = 0
        self.description: str = None
        self.edit_access_level: EditAccessLevel = EditAccessLevel.OPEN
        self.id: int = 0
        self.name: str = None
        self.product_count: int = 0
        self.products: list = None
        self.rep: int = 0
        self.tags: set[Tag] = set()
        self.visibility: ContentVisibility = ContentVisibility.PUBLICLY_VISIBLE
        self.website: str = None

        if data:
            if ProtocolKey.ALIAS in data:
                self.alias: str = data[ProtocolKey.ALIAS]

            if ProtocolKey.AVATAR_LIGHT_MODE_FILE_PATH in data:
                self.avatar_light_path: str = data[ProtocolKey.AVATAR_LIGHT_MODE_FILE_PATH]

            if ProtocolKey.CREATION_TIMESTAMP in data:
                creation_timestamp = data[ProtocolKey.CREATION_TIMESTAMP]

                if isinstance(creation_timestamp, datetime):
                    self.creation_timestamp: datetime = creation_timestamp
                elif isinstance(creation_timestamp, str):
                    self.creation_timestamp: datetime = date_parser.parse(creation_timestamp)

            if ProtocolKey.CREATOR_ID in data:
                self.creator_id: int = data[ProtocolKey.CREATOR_ID]

            if ProtocolKey.DESCRIPTION in data:
                self.description: str = data[ProtocolKey.DESCRIPTION]

            if ProtocolKey.EDIT_ACCESS_LEVEL in data and data[ProtocolKey.EDIT_ACCESS_LEVEL]:
                self.edit_access_level = EditAccessLevel(data[ProtocolKey.EDIT_ACCESS_LEVEL])

            if ProtocolKey.ID in data:
                self.id: int = data[ProtocolKey.ID]

            if ProtocolKey.NAME in data:
                self.name: str = data[ProtocolKey.NAME]

            if ProtocolKey.REP in data:
                self.rep: int = data[ProtocolKey.REP]

            if ProtocolKey.VISIBILITY in data and data[ProtocolKey.VISIBILITY]:
                self.visibility = ContentVisibility(data[ProtocolKey.VISIBILITY])

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
        ret = "Brand " + self.id.__str__()

        if self.name:
            ret += f" ({self.name})"

        return ret

    @staticmethod
    def add_history(brand_id: int = 0,
                    editor_id: int = 0,
                    action_id: UserAction = UserAction.UNDEFINED,
                    field_id: Field = Field.UNDEFINED,
                    field_value: Any = None) -> bool:
        if not isinstance(brand_id, int):
            raise TypeError(f"Argument 'brand_id' must be of type int, not {type(brand_id)}.")

        if brand_id <= 0:
            raise ValueError("Argument 'brand_id' must be a positive, non-zero integer.")

        if not isinstance(editor_id, int):
            raise TypeError(f"Argument 'editor_id' must be of type int, not {type(editor_id)}.")

        if editor_id <= 0:
            raise ValueError("Argument 'editor_id' must be a positive, non-zero integer.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.BRAND_EDIT_HISTORY}
                ({ProtocolKey.EDITOR_ID}, {ProtocolKey.BRAND_ID}, {ProtocolKey.FIELD_VALUE},
                {ProtocolKey.FIELD_ID}, {ProtocolKey.ACTION_ID})
                VALUES (%s, %s, %s, %s, %s);
                """,
                (editor_id, brand_id, field_value, field_id.value, action_id.value)
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
    def alias_exists(alias: str) -> bool:
        """
        Compares against aliases in the brands table.
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
                SELECT * FROM {DatabaseTable.BRAND}
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
        serialized = {
            ProtocolKey.ALIAS: self.alias,
            ProtocolKey.AVATAR_LIGHT_MODE_FILE_PATH: self.avatar_light_path,
            ProtocolKey.CREATOR_ID: self.creator_id,
            ProtocolKey.DESCRIPTION: self.description,
            ProtocolKey.ID: self.id,
            ProtocolKey.NAME: self.name,
            ProtocolKey.PRODUCT_COUNT: self.product_count,
            ProtocolKey.REP: self.rep,
            ProtocolKey.WEBSITE: self.website
        }

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        if self.creator:
            serialized[ProtocolKey.CREATOR] = self.creator.as_dict()

        if self.edit_access_level:
            serialized[ProtocolKey.EDIT_ACCESS_LEVEL] = self.edit_access_level.value

        if self.products:
            products_serialized = []
            for product in self.products:
                products_serialized.append(product.as_dict())

            serialized[ProtocolKey.PRODUCTS] = products_serialized

        if self.tags:
            tags_serialized = []

            for tag in self.tags:
                tags_serialized.append(tag.as_dict())

            serialized[ProtocolKey.TAGS] = tags_serialized

        if self.visibility:
            serialized[ProtocolKey.VISIBILITY] = self.visibility.value

        return serialized

    @classmethod
    def create(cls: Type[T],
               alias: str,
               creator_id: int,
               name: str) -> T:
        if not isinstance(alias, str):
            raise TypeError(f"Argument 'alias' must be of type str, not {type(alias)}.")

        if not alias:
            raise ValueError("Argument 'alias' must be a non-empty string.")

        if not isinstance(creator_id, int):
            raise TypeError(f"Argument 'creator_id' must be of type int, not {type(creator_id)}.")

        if creator_id <= 0:
            raise ValueError("Argument 'creator_id' must be a positive, non-zero integer.")

        if not isinstance(name, str):
            raise TypeError(f"Argument 'name' must be of type str, not {type(name)}.")

        if not name:
            raise ValueError("Argument 'name' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None
        alias = alias.lower()

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.BRAND}
                ({ProtocolKey.ALIAS}, {ProtocolKey.CREATOR_ID}, {ProtocolKey.NAME})
                VALUES (%s, %s, %s) RETURNING *;
                """,
                (alias, creator_id, name)
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
                    (ret.id, alias, EntityType.BRAND)
                )

                ret.creator = UserAccount.get_by_id(ret.creator_id)

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
            raise Exception("Brand has no ID associated with it.")

        if not Brand.is_manager(account_id, self.id):
            conn = None
            cursor = None

            try:
                conn = db.connect()
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    INSERT INTO {DatabaseTable.BRAND_MANAGER}
                    ({ProtocolKey.USER_ACCOUNT_ID}, {ProtocolKey.BRAND_ID})
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

    def create_tag(self,
                   tag_id: int) -> None:
        if not self.id:
            raise Exception("Creating a brand tag requires a brand ID.")

        if not isinstance(tag_id, int):
            raise TypeError(f"Argument 'tag_id' must be of type int, not {type(tag_id)}.")

        if tag_id <= 0:
            raise ValueError("Argument 'tag_id' must be a positive, non-zero integer.")

        if not Brand.get_tag(self.id, tag_id):
            conn = None
            cursor = None

            try:
                conn = db.connect()
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    INSERT INTO {DatabaseTable.BRAND_TAG}
                    ({ProtocolKey.BRAND_ID}, {ProtocolKey.TAG_ID})
                    VALUES (%s, %s);
                    """,
                    (self.id, tag_id)
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
        [NOTE] This method erases the brand's record from the database.
        """

        if not self.id and not self.alias:
            raise Exception("Deletion requires either a brand ID or alias.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()

            if self.id:
                cursor.execute(
                    f"""
                    DELETE FROM {DatabaseTable.BRAND}
                    WHERE {ProtocolKey.ID} = %s;
                    """,
                    (self.id,)
                )
            else:
                cursor.execute(
                    f"""
                    DELETE FROM {DatabaseTable.BRAND}
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

    def delete_tag(self,
                   tag_id: int) -> None:
        if not self.id:
            raise Exception("Creating a brand tag requires a brand ID.")

        if not isinstance(tag_id, int):
            raise TypeError(f"Argument 'tag_id' must be of type int, not {type(tag_id)}.")

        if tag_id <= 0:
            raise ValueError("Argument 'tag_id' must be a positive, non-zero integer.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.BRAND_TAG}
                WHERE {ProtocolKey.BRAND_ID} = %s AND {ProtocolKey.TAG_ID} = %s;
                """,
                (self.id, tag_id)
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
                query: str,
                offset: int = 0) -> list[T]:
        if not isinstance(query, str):
            raise TypeError(f"Argument 'query' must be of type str, not {type(query)}.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()

            if query:
                cursor.execute(
                    f"""
                    SELECT *, ts_rank(match.{ProtocolKey.POSTGRES_SEARCH_NAME}, plainto_tsquery('english', %s)) AS rank FROM
                    (SELECT * FROM {DatabaseTable.BRAND}
                    WHERE {ProtocolKey.POSTGRES_SEARCH_NAME} @@ plainto_tsquery('english', %s)
                    AND {ProtocolKey.VISIBILITY} NOT IN ({ContentVisibility.DELETED.value}, {ContentVisibility.GHOSTED.value}, {ContentVisibility.REMOVED.value}))
                    AS match
                    ORDER BY rank DESC
                    LIMIT 20 OFFSET %s;
                    """,
                    (query, query, offset)
                )
            else:
                cursor.execute(
                    f"""
                    SELECT * FROM {DatabaseTable.BRAND}
                    ORDER BY {ProtocolKey.NAME} ASC
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
                SELECT * FROM {DatabaseTable.BRAND}
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
                SELECT * FROM {DatabaseTable.BRAND}
                WHERE {ProtocolKey.ALIAS} = %s;
                """,
                (alias,)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                from app.modules.product import Product

                ret = cls(result)
                ret.creator = UserAccount.get_by_id(ret.creator_id)
                ret.product_count = Product.get_product_count(ret.id)
                ret.tags = Brand.get_tags(ret.id)

                if ret.product_count > 0:
                    ret.products = Product.get_some_products(ret.id)
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
                  brand_id: int) -> T:
        if not isinstance(brand_id, int):
            raise TypeError(f"Argument 'brand_id' must be of type int, not {type(brand_id)}.")

        if brand_id <= 0:
            raise ValueError("Argument 'brand_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.BRAND}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (brand_id,)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                from app.modules.product import Product

                ret = cls(result)
                ret.creator = UserAccount.get_by_id(ret.creator_id)
                ret.product_count = Product.get_product_count(ret.id)
                ret.tags = Brand.get_tags(ret.id)

                if ret.product_count > 0:
                    ret.products = Product.get_some_products(ret.id)
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
                SELECT * FROM {DatabaseTable.BRAND}
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

    @staticmethod
    def get_tag(brand_id: int,
                tag_id: int) -> Tag:
        if not isinstance(brand_id, int):
            raise TypeError(f"Argument 'brand_id' must be of type int, not {type(brand_id)}.")

        if brand_id <= 0:
            raise ValueError("Argument 'brand_id' must be a positive, non-zero integer.")

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
                SELECT *
                FROM {DatabaseTable.TAG}
                INNER JOIN {DatabaseTable.BRAND_TAG} ON {DatabaseTable.BRAND_TAG}.{ProtocolKey.TAG_ID} = {DatabaseTable.TAG}.{ProtocolKey.ID}
                WHERE {DatabaseTable.BRAND_TAG}.{ProtocolKey.BRAND_ID} = %s AND {DatabaseTable.TAG}.{ProtocolKey.ID} = %s;
                """,
                (brand_id, tag_id)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                ret = Tag(result)
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    @staticmethod
    def get_tags(brand_id: int) -> list[Tag]:
        if not isinstance(brand_id, int):
            raise TypeError(f"Argument 'brand_id' must be of type int, not {type(brand_id)}.")

        if brand_id <= 0:
            raise ValueError("Argument 'brand_id' must be a positive, non-zero integer.")

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
                INNER JOIN {DatabaseTable.BRAND_TAG} ON {DatabaseTable.BRAND_TAG}.{ProtocolKey.TAG_ID} = {DatabaseTable.TAG}.{ProtocolKey.ID}
                WHERE {DatabaseTable.BRAND_TAG}.{ProtocolKey.BRAND_ID} = %s;
                """,
                (brand_id,)
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
    def id_exists(brand_id: int) -> bool:
        if not isinstance(brand_id, int):
            raise TypeError(f"Argument 'brand_id' must be of type int, not {type(brand_id)}.")

        if brand_id <= 0:
            raise ValueError("Argument 'brand_id' must be a positive, non-zero integer.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.BRAND}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (brand_id,)
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
                   brand_id: int) -> bool:
        if not isinstance(account_id, int):
            raise TypeError(f"Argument 'account_id' must be of type int, not {type(account_id)}.")

        if account_id <= 0:
            raise ValueError("Argument 'account_id' must be a positive, non-zero integer.")

        if not isinstance(brand_id, int):
            raise TypeError(f"Argument 'brand_id' must be of type int, not {type(brand_id)}.")

        if brand_id <= 0:
            raise ValueError("Argument 'brand_id' must be a positive, non-zero integer.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.BRAND_MANAGER}
                WHERE {ProtocolKey.USER_ACCOUNT_ID} = %s AND {ProtocolKey.BRAND_ID} = %s;
                """,
                (account_id, brand_id)
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
            raise Exception("Brand has no ID associated with it.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.BRAND}
                RIGHT JOIN ON {DatabaseTable.BRAND_MANAGER}.{ProtocolKey.USER_ACCOUNT_ID} = {DatabaseTable.USER_ACCOUNT}.{ProtocolKey.ID}
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
            raise Exception("Brand has no ID associated with it.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.BRAND}
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
        [NOTE] This method does not delete the brand's record from the database.
        """

        if not isinstance(visibility, ContentVisibility):
            raise TypeError(f"Argument 'visibility' must be of type ContentVisibility, not {type(visibility)}.")

        if not visibility:
            raise ValueError("Argument 'visibility' is None.")

        if not self.id:
            raise Exception("Brand has no ID associated with it.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.BRAND}
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
            raise Exception("Brand must have an alias associated with it.")

        if not self.id:
            raise Exception("Brand has no ID associated with it.")

        if not self.name:
            raise Exception("Brand must have a name associated with it.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.BRAND}
                SET {ProtocolKey.DESCRIPTION} = %s, {ProtocolKey.NAME} = %s,
                {ProtocolKey.REP} = %s, {ProtocolKey.WEBSITE} = %s
                WHERE {ProtocolKey.ID} = %s;
                """,
                (self.description, self.name, self.rep, self.website, self.id)
            )
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

    def update_avatar_path(self,
                           file_path: str,
                           media_mode: MediaMode) -> None:
        if not self.id:
            raise Exception("Brand has no ID associated with it.")

        if not file_path:
            file_path = None
        elif not isinstance(file_path, str):
            raise TypeError(f"Argument 'file_path' must be of type str, not {type(file_path)}.")

        if not isinstance(media_mode, MediaMode):
            raise TypeError(f"Argument 'media_mode' must be of type MediaMode, not {type(media_mode)}.")

        if media_mode == MediaMode.LIGHT:
            column = ProtocolKey.AVATAR_LIGHT_MODE_FILE_PATH
        else:
            column = ProtocolKey.AVATAR_DARK_MODE_FILE_PATH

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.BRAND}
                SET {column} = %s
                WHERE {ProtocolKey.ID} = %s;
                """,
                (file_path, self.id)
            )
            conn.commit()

            if media_mode == MediaMode.LIGHT:
                self.avatar_light_path = file_path
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()


class BrandEditHistory:
    def __init__(self,
                 data: dict) -> None:
        self.action_id: UserAction = UserAction.UNDEFINED
        self.brand_id: int = 0
        self.editor_id: int = 0
        self.field_id: Field = Field.UNDEFINED
        self.field_value: Any = None

        if data:
            if ProtocolKey.ACTION_ID in data:
                self.action_id: UserAction = UserAction(data[ProtocolKey.ACTION_ID])

            if ProtocolKey.BRAND_ID in data:
                self.brand_id: int = data[ProtocolKey.BRAND_ID]

            if ProtocolKey.EDITOR_ID in data:
                self.editor_id: int = data[ProtocolKey.EDITOR_ID]

            if ProtocolKey.FIELD_ID in data:
                self.field_id: Field = Field(data[ProtocolKey.FIELD_ID])

            if ProtocolKey.FIELD_VALUE in data:
                self.field_value: Any = data[ProtocolKey.FIELD_VALUE]


####################
# MODULE FUNCTIONS #
####################


def allowed_avatar_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Configuration.ALLOWED_AVATAR_FILE_EXTENSIONS


def check_alias(alias: str) -> tuple[dict, ResponseStatus]:
    if not alias:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'alias' must be an ASCII non-empty string."

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

        if Brand.alias_valid(alias):
            if not Brand.alias_exists(alias):
                response = {
                    ProtocolKey.ALIAS: alias
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


def create_brand(alias: str,
                 name: str,
                 tags: str) -> tuple[dict, ResponseStatus]:
    if name:
        name = name.strip()
    else:
        name = None

    if tags:
        try:
            tags = json.loads(tags)
        except:
            tags = None
    else:
        tags = None

    if not alias or \
            not name or \
            not tags:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not alias:
            error_message += ": 'alias' must be an ASCII non-empty string."
        elif not name:
            error_message += ": 'name' must be a non-empty string."
        elif not tags:
            error_message += ": 'tags' must be a non-empty JSON array string."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}

        if len(alias) > Configuration.ALIAS_MAX_LEN:
            response_status = ResponseStatus.BAD_REQUEST
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.ALIAS_INVALID.value,
                    ProtocolKey.ERROR_MESSAGE: f"Alias can't be more than {Configuration.ALIAS_MAX_LEN} characters long."
                }
            }

        if response_status == ResponseStatus.OK:
            if len(name) > Configuration.NAME_MAX_LEN:
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.NAME_INVALID.value,
                        ProtocolKey.ERROR_MESSAGE: f"Name can't be more than {Configuration.NAME_MAX_LEN} characters long."
                    }
                }

        if response_status == ResponseStatus.OK:
            if len(tags) > Configuration.TAG_MAX_COUNT:
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.TAG_INVALID.value,
                        ProtocolKey.ERROR_MESSAGE: f"Can't have more than {Configuration.TAG_MAX_COUNT} tags."
                    }
                }
            else:
                for tag_name in tags:
                    if any(illegal in tag_name for illegal in Configuration.TAG_ILLEGAL_CHARACTERS) or \
                            len(tag_name) > Configuration.TAG_MAX_LEN or \
                            not tag_name:
                        response_status = ResponseStatus.BAD_REQUEST
                        error_message = ""

                        if any(illegal in tag_name for illegal in Configuration.TAG_ILLEGAL_CHARACTERS):
                            error_message = "a tag cannot contain punctuation or whitespace characters."
                        elif len(tag_name) > Configuration.TAG_MAX_LEN:
                            error_message = "a tag can only be up to {Configuration.TAG_MAX_LEN} characters in length."
                        elif not tag_name:
                            error_message = "a tag can't be blank."

                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: ResponseStatus.TAG_INVALID.value,
                                ProtocolKey.ERROR_MESSAGE: f"Tag '{tag_name}' is invalid: {error_message}"
                            }
                        }

                        break

        if response_status == ResponseStatus.OK:
            alias = alias.lower()

            if Brand.alias_valid(alias):
                if not Brand.alias_exists(alias):
                    session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
                    creator = UserAccount.get_by_session(session_id)
                    brand = Brand.create(alias, creator.id, name)

                    if brand:
                        brand.create_manager(creator.id)

                        for tag_name in tags:
                            tag = Tag.get_by_name(tag_name)

                            if not tag:
                                tag = Tag.create(tag_name, creator.id)

                            brand.create_tag(tag.id)

                        brand.tags = Brand.get_tags(brand.id)

                        response = {
                            ProtocolKey.BRAND: brand.as_dict()
                        }
                    else:
                        response_status = ResponseStatus.INTERNAL_SERVER_ERROR
                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: response_status.value,
                                ProtocolKey.ERROR_MESSAGE: "An internal server error occurred."
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


def delete_brand(brand_id: str) -> tuple[dict, ResponseStatus]:
    if brand_id:
        try:
            brand_id = int(brand_id)

            if brand_id <= 0:
                brand_id = None
        except ValueError:
            brand_id = None

    if not brand_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'brand_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}
        brand = Brand.get_by_id(brand_id)

        if brand:
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
            user_account = UserAccount.get_by_session(session_id)

            if user_account.is_admin:
                if brand.avatar_light_path:
                    # Delete the avatar file.
                    if app.debug:
                        try:
                            os.remove(os.path.join(Configuration.AVATAR_DIR, brand.avatar_light_path))
                        except OSError:
                            pass
                    else:
                        s3.delete_media(brand.avatar_light_path)

                brand.delete()

                response = {
                    ProtocolKey.BRAND_ID: brand.id
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
                    ProtocolKey.ERROR_CODE: ResponseStatus.BRAND_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No brand exists for this ID."
                }
            }

    return (response, response_status)


def get_brand(alias: str = None,
              brand_id: str = None) -> tuple[dict, ResponseStatus]:
    if brand_id:
        try:
            brand_id = int(brand_id)

            if brand_id <= 0:
                brand_id = None
        except ValueError:
            brand_id = None

    if not alias and \
            not brand_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'alias' must be a non-empty string or 'brand_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}

        if brand_id:
            brand = Brand.get_by_id(brand_id)
        else:
            if Brand.alias_valid(alias):
                brand = Brand.get_by_alias(alias)
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
            if brand and \
                    brand.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
                response = {
                    ProtocolKey.BRAND: brand.as_dict()
                }
            else:
                response_status = ResponseStatus.NOT_FOUND
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.BRAND_NOT_FOUND.value,
                        ProtocolKey.ERROR_MESSAGE: "No brand exists for this alias/brand ID."
                    }
                }

    return (response, response_status)


def get_brands(query: str) -> tuple[dict, ResponseStatus]:
    query = query.strip()
    response_status = ResponseStatus.OK
    serialized = []

    if isinstance(query, str):
        results = Brand.get_all(query)

        for result in results:
            # This line is slowing things down.
            # result.tags = Brand.get_tags(result.id)
            serialized.append(result.as_dict())

    response = {
        ProtocolKey.BRANDS: serialized
    }

    return (response, response_status)


def remove_brand(brand_id: str) -> tuple[dict, ResponseStatus]:
    if brand_id:
        try:
            brand_id = int(brand_id)

            if brand_id <= 0:
                brand_id = None
        except ValueError:
            brand_id = None

    if not brand_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'brand_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}
        brand = Brand.get_by_id(brand_id)

        if brand and \
                brand.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
            user_account = UserAccount.get_by_session(session_id)

            if user_account.is_admin or Brand.is_manager(user_account.id, brand_id):
                if user_account.id == brand.creator_id:
                    visibility = ContentVisibility.DELETED
                else:
                    visibility = ContentVisibility.REMOVED

                brand.set_visibility(visibility)
                Brand.add_history(brand.id, user_account.id, UserAction.UPDATED, Field.VISIBILITY, visibility.value)

                response = {
                    ProtocolKey.VISIBILITY: visibility.value
                }
            else:
                response_status = ResponseStatus.FORBIDDEN
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: response_status.value,
                        ProtocolKey.ERROR_MESSAGE: "User account is neither an admin nor a manager of this brand."
                    }
                }
        else:
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.BRAND_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No brand exists for this ID."
                }
            }

    return (response, response_status)


def update_avatar(brand_id: str,
                  media_mode: str) -> tuple[dict, ResponseStatus]:
    if brand_id:
        try:
            brand_id = int(brand_id)

            if brand_id <= 0:
                brand_id = None
        except ValueError:
            brand_id = None
    else:
        brand_id = None

    if ProtocolKey.AVATAR.value not in request.files:
        avatar = None
    else:
        avatar = request.files[ProtocolKey.AVATAR.value]

        if not avatar.filename:
            avatar = None

    if media_mode:
        try:
            media_mode = MediaMode(int(media_mode))
        except ValueError:
            media_mode = None
    else:
        media_mode = None

    if not brand_id or \
            not avatar or \
            not media_mode:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not brand_id:
            error_message += ": 'brand_id' must be a positive, non-zero integer."
        elif not avatar:
            error_message += f": 'avatar' must be a an image in one of the following formats: {','.join(Configuration.ALLOWED_AVATAR_FILE_EXTENSIONS)}"
        elif not media_mode:
            error_message += ": 'media_mode' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        brand = Brand.get_by_id(brand_id)

        if brand and \
                brand.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
            if allowed_avatar_file(avatar.filename):
                avatar_bytes = avatar.read()
                avatar_hash = hashlib.sha256(avatar_bytes).hexdigest()

                brand_media_dir = os.path.join(Configuration.BRAND_MEDIA_DIR, f"{brand_id}")
                os.makedirs(brand_media_dir, exist_ok=True)
                # We'd like to standardize all images to be in JPEG format.
                file_path_final = os.path.join(brand_media_dir, f"{avatar_hash}_avatar_full.jpg")

                avatar_filename = secure_filename(avatar.filename)
                file_path_tmp = os.path.join("/tmp", avatar_filename)
                avatar.stream.seek(0)
                avatar.save(file_path_tmp)

                try:
                    # Convert to PNG.
                    pil_image = Image.open(file_path_tmp)
                    pil_image.save(file_path_final)
                    avatar_light_path = f"brand/{brand_id}/{avatar_hash}_avatar_full.jpg"

                    # Don't bother updating if it's the same image being re-uploaded.
                    if brand.avatar_light_path != avatar_light_path:
                        if app.debug:
                            # Delete the previous avatar.
                            if brand.avatar_light_path:
                                try:
                                    os.remove(os.path.join(Configuration.MEDIA_DIR, brand.avatar_light_path))
                                except OSError:
                                    pass
                        else:
                            # Delete the previous avatar.
                            if brand.avatar_light_path:
                                s3.delete_media(brand.avatar_light_path)

                            s3.upload_media(file_path_final, avatar_light_path)
                            # Don't need the local file anymore.
                            os.remove(file_path_final)

                        brand.update_avatar_path(avatar_light_path, media_mode)

                        # Auditing.
                        session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
                        editor = UserAccount.get_by_session(session_id)
                        Brand.add_history(brand.id, editor.id, UserAction.UPDATED, Field.AVATAR, avatar_light_path)
                    else:
                        print("User re-uploaded the same image; ignoring.")

                    response_status = ResponseStatus.OK
                    response = {
                        ProtocolKey.AVATAR_LIGHT_MODE_FILE_PATH: avatar_light_path,
                        ProtocolKey.BRAND_ID: brand.id
                    }
                except IOError:
                    # File is not an image file.
                    response_status = ResponseStatus.BAD_REQUEST
                    response = {
                        ProtocolKey.ERROR: {
                            ProtocolKey.ERROR_CODE: ResponseStatus.MEDIA_INVALID.value,
                            ProtocolKey.ERROR_MESSAGE: f"Invalid file. Allowed image formats: {', '.join(Configuration.ALLOWED_AVATAR_FILE_EXTENSIONS)}"
                        }
                    }
                finally:
                    # Clean up.
                    os.remove(file_path_tmp)
            else:
                response_status = ResponseStatus.FORBIDDEN
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.MEDIA_UNSUPPORTED.value,
                        ProtocolKey.ERROR_MESSAGE: f"Invalid file type. Allowed image formats: {', '.join(Configuration.ALLOWED_AVATAR_FILE_EXTENSIONS)}"
                    }
                }
        else:
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.BRAND_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No brand exists for this ID."
                }
            }

    return (response, response_status)


def update_brand(brand_id: str = None,
                 description: str = None,
                 name: str = None,
                 tags: str = None,
                 website: str = None) -> tuple[dict, ResponseStatus]:
    if brand_id:
        try:
            brand_id = int(brand_id)

            if brand_id <= 0:
                brand_id = None
        except ValueError:
            brand_id = None
    else:
        brand_id = None

    if description:
        description = description.strip()
    else:
        description = None

    if name:
        name = name.strip()
    else:
        name = None

    if tags:
        try:
            tags = json.loads(tags)
        except:
            tags = None
    else:
        tags = None

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

    if not brand_id or \
            not name or \
            not tags:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not brand_id:
            error_message += ": 'brand_id' must be a positive, non-zero integer."
        elif not name:
            error_message += ": 'name' must be a non-empty string."
        elif not tags:
            error_message += ": 'tags' must be a non-empty JSON array string."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}

        if description and len(description) > Configuration.DESCRIPTION_MAX_LEN:
            response_status = ResponseStatus.BAD_REQUEST
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.DESCRIPTION_INVALID.value,
                    ProtocolKey.ERROR_MESSAGE: f"Description can't be more than {Configuration.DESCRIPTION_MAX_LEN} characters long."
                }
            }

        if response_status == ResponseStatus.OK:
            if len(name) > Configuration.NAME_MAX_LEN:
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.NAME_INVALID.value,
                        ProtocolKey.ERROR_MESSAGE: f"Name can't be more than {Configuration.NAME_MAX_LEN} characters long."
                    }
                }

        if response_status == ResponseStatus.OK:
            if len(tags) > Configuration.TAG_MAX_COUNT:
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.TAG_INVALID.value,
                        ProtocolKey.ERROR_MESSAGE: f"Can't have more than {Configuration.TAG_MAX_COUNT} tags."
                    }
                }
            else:
                for tag_name in tags:
                    if any(illegal in tag_name for illegal in Configuration.TAG_ILLEGAL_CHARACTERS) or \
                            len(tag_name) > Configuration.TAG_MAX_LEN or \
                            not tag_name:
                        response_status = ResponseStatus.BAD_REQUEST
                        error_message = ""

                        if any(illegal in tag_name for illegal in Configuration.TAG_ILLEGAL_CHARACTERS):
                            error_message = "a tag cannot contain punctuation or whitespace characters."
                        elif len(tag_name) > Configuration.TAG_MAX_LEN:
                            error_message = "a tag can only be up to {Configuration.TAG_MAX_LEN} characters in length."
                        elif not tag_name:
                            error_message = "a tag can't be blank."

                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: ResponseStatus.TAG_INVALID.value,
                                ProtocolKey.ERROR_MESSAGE: f"Tag '{tag_name}' is invalid: {error_message}"
                            }
                        }

                        break

        if response_status == ResponseStatus.OK and website:
            if website and len(website) > Configuration.URL_MAX_LEN:
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.URL_INVALID.value,
                        ProtocolKey.ERROR_MESSAGE: f"Website URL can't be more than {Configuration.URL_MAX_LEN} characters long."
                    }
                }

        if response_status == ResponseStatus.OK:
            brand = Brand.get_by_id(brand_id)

            if brand and \
                    brand.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
                session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
                user_account = UserAccount.get_by_session(session_id)

                if brand.edit_access_level == EditAccessLevel.OPEN or \
                        (brand.edit_access_level == EditAccessLevel.PUBLICLY_ACCESSIBLE and Brand.is_manager(user_account.id, brand_id)) or \
                        user_account.is_admin:
                    auditEntries = []

                    if description != brand.description:
                        auditEntries.append({
                            ProtocolKey.ACTION_ID: UserAction.UPDATED,
                            ProtocolKey.BRAND_ID: brand.id,
                            ProtocolKey.EDITOR_ID: user_account.id,
                            ProtocolKey.FIELD_ID: Field.DESCRIPTION,
                            ProtocolKey.FIELD_VALUE: description
                        })

                    if name != brand.name:
                        auditEntries.append({
                            ProtocolKey.ACTION_ID: UserAction.UPDATED,
                            ProtocolKey.BRAND_ID: brand.id,
                            ProtocolKey.EDITOR_ID: user_account.id,
                            ProtocolKey.FIELD_ID: Field.NAME,
                            ProtocolKey.FIELD_VALUE: name
                        })

                    if website != brand.website:
                        auditEntries.append({
                            ProtocolKey.ACTION_ID: UserAction.UPDATED,
                            ProtocolKey.BRAND_ID: brand.id,
                            ProtocolKey.EDITOR_ID: user_account.id,
                            ProtocolKey.FIELD_ID: Field.WEBSITE,
                            ProtocolKey.FIELD_VALUE: website
                        })

                    brand.description = description
                    brand.name = name
                    brand.website = website
                    brand.update()

                    for tag_name in tags:
                        exists = False

                        for tag in brand.tags:
                            if tag_name == tag.name:
                                exists = True
                                break

                        if not exists:
                            tag = Tag.get_by_name(tag_name)

                            if not tag:
                                tag = Tag.create(tag_name, user_account.id)

                            brand.create_tag(tag.id)
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.ADDED,
                                ProtocolKey.BRAND_ID: brand.id,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.TAGS,
                                ProtocolKey.FIELD_VALUE: tag.id
                            })

                    for tag in brand.tags:
                        exists = False

                        for tag_name in tags:
                            if tag_name == tag.name:
                                exists = True
                                break

                        if not exists:
                            brand.delete_tag(tag.id)
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.DELETED,
                                ProtocolKey.BRAND_ID: brand.id,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.TAGS,
                                ProtocolKey.FIELD_VALUE: tag.id
                            })

                    brand.tags = Brand.get_tags(brand.id)

                    for entry in auditEntries:
                        brand.add_history(**entry)

                    response = {
                        ProtocolKey.BRAND: brand.as_dict()
                    }
                else:
                    response_status = ResponseStatus.FORBIDDEN
                    response = {
                        ProtocolKey.ERROR: {
                            ProtocolKey.ERROR_CODE: response_status.value,
                            ProtocolKey.ERROR_MESSAGE: "User account is neither an admin nor a manager of this brand."
                        }
                    }
            else:
                response_status = ResponseStatus.NOT_FOUND
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.BRAND_NOT_FOUND.value,
                        ProtocolKey.ERROR_MESSAGE: "No brand exists for this ID."
                    }
                }

    return (response, response_status)
