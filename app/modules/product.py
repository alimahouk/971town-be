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
                        EditAccessLevel, EntityType, Field, MediaMode,
                        ProductStatus, ProtocolKey, ResponseStatus,
                        UserAction)
from app.modules import db
from app.modules.brand import Brand
from app.modules.product_color import ProductColor
from app.modules.product_material import ProductMaterial
from app.modules.product_medium import ProductMedium
from app.modules.s3 import s3
from app.modules.tag import Tag
from app.modules.user_account import UserAccount


###########
# CLASSES #
###########


T = TypeVar("T", bound="Product")


class Product:
    def __init__(self,
                 data: dict) -> None:
        self.alias: str = None
        self.brand: Brand = None
        self.brand_id: int = 0
        self.creation_timestamp: datetime = None
        self.creator: UserAccount = None
        self.creator_id: int = 0
        self.description: str = None
        self.display_name_override: bool = False
        self.edit_access_level: EditAccessLevel = EditAccessLevel.OPEN
        self.id: int = 0
        self.main_color: ProductColor = None
        self.main_color_code: str = None
        self.material: str = None
        self.material_id: int = None
        self.media: list[ProductMedium] = None
        self.name: str = None
        self.parent_product: Product = None
        self.parent_product_id: int = 0
        self.preorder_timestamp: datetime = None
        self.release_timestamp: datetime = None
        self.status: ProductStatus = ProductStatus.AVAILABLE
        self.tags: set[Tag] = set()
        self.upc: str = None
        self.url: str = None
        self.variant_count: int = 0
        self.variants: list[Product] = None
        self.visibility: ContentVisibility = ContentVisibility.PUBLICLY_VISIBLE

        if data:
            if ProtocolKey.ALIAS in data and data[ProtocolKey.ALIAS]:
                self.alias: str = data[ProtocolKey.ALIAS]

            if ProtocolKey.BRAND in data and data[ProtocolKey.BRAND]:
                self.brand: Brand = Brand(data[ProtocolKey.BRAND])

            if ProtocolKey.BRAND_ID in data and data[ProtocolKey.BRAND_ID]:
                self.brand_id: int = data[ProtocolKey.BRAND_ID]

            if ProtocolKey.CREATION_TIMESTAMP in data and data[ProtocolKey.CREATION_TIMESTAMP]:
                creation_timestamp = data[ProtocolKey.CREATION_TIMESTAMP]

                if isinstance(creation_timestamp, datetime):
                    self.creation_timestamp: datetime = creation_timestamp
                elif isinstance(creation_timestamp, str):
                    self.creation_timestamp: datetime = date_parser.parse(creation_timestamp)

            if ProtocolKey.CREATOR in data and data[ProtocolKey.CREATOR]:
                self.creator: UserAccount = UserAccount(data[ProtocolKey.CREATOR])

            if ProtocolKey.CREATOR_ID in data and data[ProtocolKey.CREATOR_ID]:
                self.creator_id: int = data[ProtocolKey.CREATOR_ID]

            if ProtocolKey.DESCRIPTION in data and data[ProtocolKey.DESCRIPTION]:
                self.description: str = data[ProtocolKey.DESCRIPTION]

            if ProtocolKey.EDIT_ACCESS_LEVEL in data and data[ProtocolKey.EDIT_ACCESS_LEVEL]:
                self.edit_access_level = EditAccessLevel(data[ProtocolKey.EDIT_ACCESS_LEVEL])

            if ProtocolKey.ID in data and data[ProtocolKey.ID]:
                self.id: int = data[ProtocolKey.ID]

            if ProtocolKey.MAIN_COLOR_CODE in data and data[ProtocolKey.MAIN_COLOR_CODE]:
                self.main_color_code: str = data[ProtocolKey.MAIN_COLOR_CODE]

            if ProtocolKey.MATERIAL_ID in data and data[ProtocolKey.MATERIAL_ID]:
                self.material_id: int = data[ProtocolKey.MATERIAL_ID]

            if ProtocolKey.NAME in data and data[ProtocolKey.NAME]:
                self.name: str = data[ProtocolKey.NAME]

            if ProtocolKey.OVERRIDES_DISPLAY_NAME in data and data[ProtocolKey.OVERRIDES_DISPLAY_NAME]:
                self.display_name_override: bool = data[ProtocolKey.OVERRIDES_DISPLAY_NAME]

            if ProtocolKey.PARENT_PRODUCT in data and data[ProtocolKey.PARENT_PRODUCT]:
                self.parent_product: Product = Product(data[ProtocolKey.PARENT_PRODUCT])

            if ProtocolKey.PARENT_PRODUCT_ID in data and data[ProtocolKey.PARENT_PRODUCT_ID]:
                self.parent_product_id: int = data[ProtocolKey.PARENT_PRODUCT_ID]

            if ProtocolKey.PREORDER_TIMESTAMP in data and data[ProtocolKey.PREORDER_TIMESTAMP]:
                preorder_timestamp = data[ProtocolKey.PREORDER_TIMESTAMP]

                if isinstance(preorder_timestamp, datetime):
                    self.preorder_timestamp: datetime = preorder_timestamp
                elif isinstance(preorder_timestamp, str):
                    self.preorder_timestamp: datetime = date_parser.parse(preorder_timestamp)

            if ProtocolKey.RELEASE_TIMESTAMP in data and data[ProtocolKey.RELEASE_TIMESTAMP]:
                release_timestamp = data[ProtocolKey.RELEASE_TIMESTAMP]

                if isinstance(release_timestamp, datetime):
                    self.release_timestamp: datetime = release_timestamp
                elif isinstance(release_timestamp, str):
                    self.release_timestamp: datetime = date_parser.parse(release_timestamp)

            if ProtocolKey.STATUS in data and data[ProtocolKey.STATUS]:
                self.status = ProductStatus(data[ProtocolKey.STATUS])

            if ProtocolKey.UPC in data and data[ProtocolKey.UPC]:
                self.upc: str = data[ProtocolKey.UPC]

            if ProtocolKey.URL in data and data[ProtocolKey.URL]:
                self.url: str = data[ProtocolKey.URL]

            if ProtocolKey.VISIBILITY in data and data[ProtocolKey.VISIBILITY]:
                self.visibility = EditAccessLevel(data[ProtocolKey.VISIBILITY])

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
        ret = "Product " + self.id.__str__()

        if self.name:
            ret += f" ({self.name})"

        return ret

    @staticmethod
    def add_history(product_id: int = 0,
                    editor_id: int = 0,
                    action_id: UserAction = UserAction.UNDEFINED,
                    field_id: Field = Field.UNDEFINED,
                    field_value: Any = None) -> bool:
        if not isinstance(product_id, int):
            raise TypeError(f"Argument 'product_id' must be of type int, not {type(product_id)}.")

        if product_id <= 0:
            raise ValueError("Argument 'product_id' must be a positive, non-zero integer.")

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
                INSERT INTO {DatabaseTable.PRODUCT_EDIT_HISTORY}
                    ({ProtocolKey.EDITOR_ID}, {ProtocolKey.PRODUCT_ID}, {ProtocolKey.FIELD_VALUE},
                    {ProtocolKey.FIELD_ID}, {ProtocolKey.ACTION_ID})
                VALUES
                    (%s, %s, %s,
                    %s, %s);
                """,
                (editor_id, product_id, field_value, field_id.value, action_id.value)
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
        Compares against aliases in the products table.
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
                SELECT
                    *
                FROM
                    {DatabaseTable.PRODUCT}
                WHERE
                    {ProtocolKey.ALIAS} = %s;
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
            ProtocolKey.BRAND_ID: self.brand_id,
            ProtocolKey.CREATOR_ID: self.creator_id,
            ProtocolKey.DESCRIPTION: self.description,
            ProtocolKey.ID: self.id,
            ProtocolKey.MAIN_COLOR_CODE: self.main_color_code,
            ProtocolKey.MATERIAL_ID: self.material_id,
            ProtocolKey.NAME: self.name,
            ProtocolKey.OVERRIDES_DISPLAY_NAME: self.display_name_override,
            ProtocolKey.PRODUCT_VARIANT_COUNT: self.variant_count,
            ProtocolKey.UPC: self.upc,
            ProtocolKey.URL: self.url
        }

        if self.brand:
            serialized[ProtocolKey.BRAND] = self.brand.as_dict()

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        if self.creator:
            serialized[ProtocolKey.CREATOR] = self.creator.as_dict()

        if self.edit_access_level:
            serialized[ProtocolKey.EDIT_ACCESS_LEVEL] = self.edit_access_level.value

        if self.main_color:
            serialized[ProtocolKey.MAIN_COLOR] = self.main_color.as_dict()

        if self.material:
            serialized[ProtocolKey.MATERIAL] = self.material.as_dict()

        if self.media:
            media_serialized = []

            for medium in self.media:
                media_serialized.append(medium.as_dict())

            serialized[ProtocolKey.MEDIA] = media_serialized

        if self.parent_product:
            serialized[ProtocolKey.PARENT_PRODUCT] = self.parent_product.as_dict()

        if self.parent_product_id:
            serialized[ProtocolKey.PARENT_PRODUCT_ID] = self.parent_product_id

        if self.preorder_timestamp:
            serialized[ProtocolKey.PREORDER_TIMESTAMP] = self.preorder_timestamp.astimezone().isoformat()

        if self.release_timestamp:
            serialized[ProtocolKey.RELEASE_TIMESTAMP] = self.release_timestamp.astimezone().isoformat()

        if self.status:
            serialized[ProtocolKey.STATUS] = self.status.value

        if self.tags:
            tags_serialized = []

            for tag in self.tags:
                tags_serialized.append(tag.as_dict())

            serialized[ProtocolKey.TAGS] = tags_serialized

        if self.variants:
            variants_serialized = []

            for variant in self.variants:
                variants_serialized.append(variant.as_dict())

            serialized[ProtocolKey.PRODUCT_VARIANTS] = variants_serialized

        if self.visibility:
            serialized[ProtocolKey.VISIBILITY] = self.visibility.value

        return serialized

    @classmethod
    def create(cls: Type[T],
               alias: str,
               brand_id: int,
               creator_id: int,
               name: str,
               parent_product_id: int,
               status: ProductStatus) -> T:
        if not isinstance(alias, str):
            raise TypeError(f"Argument 'alias' must be of type str, not {type(alias)}.")

        alias = "".join(char for char in alias if char in string.printable)

        if not alias:
            raise ValueError("Argument 'alias' must be a non-empty string.")

        if not isinstance(brand_id, int):
            raise TypeError(f"Argument 'brand_id' must be of type int, not {type(brand_id)}.")

        if brand_id <= 0:
            raise ValueError("Argument 'brand_id' must be a positive, non-zero integer.")

        if not isinstance(creator_id, int):
            raise TypeError(f"Argument 'creator_id' must be of type int, not {type(creator_id)}.")

        if creator_id <= 0:
            raise ValueError("Argument 'creator_id' must be a positive, non-zero integer.")

        if not isinstance(name, str):
            raise TypeError(f"Argument 'name' must be of type str, not {type(name)}.")

        if not name:
            raise ValueError("Argument 'name' must be a non-empty string.")

        if parent_product_id:
            if not isinstance(parent_product_id, int):
                raise TypeError(f"Argument 'parent_product_id' must be of type int, not {type(parent_product_id)}.")

            if parent_product_id <= 0:
                raise ValueError("Argument 'parent_product_id' must be a positive, non-zero integer.")

        if not isinstance(status, ProductStatus):
            raise TypeError(f"Argument 'status' must be of type ProductStatus, not {type(status)}.")

        ret: Type[T] = None
        conn = None
        cursor = None
        alias = alias.lower()

        try:
            conn = db.connect()
            cursor = conn.cursor()

            if parent_product_id:
                cursor.execute(
                    f"""
                    INSERT INTO {DatabaseTable.PRODUCT}
                        ({ProtocolKey.ALIAS}, {ProtocolKey.BRAND_ID}, {ProtocolKey.CREATOR_ID},
                        {ProtocolKey.NAME}, {ProtocolKey.PARENT_PRODUCT_ID}, {ProtocolKey.STATUS})
                    VALUES
                        (%s, %s, %s,
                        %s, %s, %s)
                    RETURNING *;
                    """,
                    (alias, brand_id, creator_id,
                     name, parent_product_id, status.value)
                )
            else:
                cursor.execute(
                    f"""
                    INSERT INTO {DatabaseTable.PRODUCT}
                        ({ProtocolKey.ALIAS}, {ProtocolKey.BRAND_ID}, {ProtocolKey.CREATOR_ID},
                        {ProtocolKey.NAME}, {ProtocolKey.STATUS})
                    VALUES
                        (%s, %s, %s, 
                        %s, %s)
                    RETURNING *;
                    """,
                    (alias, brand_id, creator_id,
                     name, status.value)
                )

            result = cursor.fetchone()
            conn.commit()

            if result:
                ret = cls(result)

                cursor.execute(
                    f"""
                    INSERT INTO {DatabaseTable.ALIAS}
                        ({ProtocolKey.ID}, {ProtocolKey.ALIAS}, {ProtocolKey.ENTITY_TYPE})
                    VALUES
                        (%s, %s, %s);
                    """,
                    (ret.id, alias, EntityType.PRODUCT)
                )

                ret.brand = Brand.get_by_id(ret.brand_id)
                ret.creator = UserAccount.get_by_id(ret.creator_id)

                if ret.main_color_code:
                    ret.main_color = ProductColor.get_by_code(ret.main_color_code)

                if ret.material_id:
                    ret.material = ProductMaterial.get_by_id(ret.material_id)

                if ret.parent_product_id:
                    ret.parent_product = Product.get_by_id(ret.parent_product_id)

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
            raise Exception("Product has no ID associated with it.")

        if not Product.is_manager(account_id, self.id):
            conn = None
            cursor = None

            try:
                conn = db.connect()
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    INSERT INTO {DatabaseTable.PRODUCT_MANAGER}
                        ({ProtocolKey.USER_ACCOUNT_ID}, {ProtocolKey.PRODUCT_ID})
                    VALUES
                        (%s, %s);
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
            raise Exception("Creating a product tag requires a product ID.")

        if not isinstance(tag_id, int):
            raise TypeError(f"Argument 'tag_id' must be of type int, not {type(tag_id)}.")

        if tag_id <= 0:
            raise ValueError("Argument 'tag_id' must be a positive, non-zero integer.")

        if not Product.get_tag(self.id, tag_id):
            conn = None
            cursor = None

            try:
                conn = db.connect()
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    INSERT INTO {DatabaseTable.PRODUCT_TAG}
                        ({ProtocolKey.PRODUCT_ID}, {ProtocolKey.TAG_ID})
                    VALUES
                        (%s, %s);
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
        [NOTE] This method erases the product's record from the database.
        """

        if not self.id and not self.alias:
            raise Exception("Deletion requires either a product ID or alias.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()

            if self.id:
                cursor.execute(
                    f"""
                    DELETE FROM
                        {DatabaseTable.PRODUCT}
                    WHERE
                        {ProtocolKey.ID} = %s;
                    """,
                    (self.id,)
                )
            else:
                cursor.execute(
                    f"""
                    DELETE FROM
                        {DatabaseTable.PRODUCT}
                    WHERE
                        {ProtocolKey.ALIAS} = %s;
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
            raise Exception("Creating a product tag requires a product ID.")

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
                DELETE FROM
                    {DatabaseTable.PRODUCT_TAG}
                WHERE
                    {ProtocolKey.PRODUCT_ID} = %s
                AND
                    {ProtocolKey.TAG_ID} = %s;
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
                query: str = None,
                brand_id: int = None,
                offset: int = 0) -> list[T]:
        """
        This method does not return product variants unless in response to a query.
        """

        if query and not isinstance(query, str):
            raise TypeError(f"Argument 'query' must be of type str, not {type(query)}.")

        if brand_id:
            if not isinstance(brand_id, int):
                raise TypeError(f"Argument 'brand_id' must be of type int, not {type(brand_id)}.")

            if brand_id <= 0:
                raise ValueError("Argument 'brand_id' must be a positive, non-zero integer.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()

            if query:
                alias_pattern = f"%{query.replace(' ', '').lower()}%"

                cursor.execute(
                    f"""
                    SELECT
                        *, ts_rank(match.{ProtocolKey.POSTGRES_SEARCH_NAME}, plainto_tsquery('english', %s)) AS rank
                    FROM
                    (
                        SELECT 
                            p.*,
                            b.{ProtocolKey.BRAND},
                            pp.{ProtocolKey.PARENT_PRODUCT}
                        FROM 
                            {DatabaseTable.PRODUCT} AS p
                        LEFT JOIN (
                            SELECT
                                {ProtocolKey.ID},
                                ROW_TO_JSON(b) AS {ProtocolKey.BRAND}
                            FROM 
                                {DatabaseTable.BRAND} AS b
                        ) AS b ON p.{ProtocolKey.BRAND_ID} = b.{ProtocolKey.ID}
                        LEFT JOIN (
                            SELECT
                                {ProtocolKey.ID},
                                ROW_TO_JSON(pp) AS {ProtocolKey.PARENT_PRODUCT}
                            FROM 
                                {DatabaseTable.PRODUCT} AS pp
                        ) AS pp ON p.{ProtocolKey.PARENT_PRODUCT_ID} = pp.{ProtocolKey.ID}
                        WHERE
                            (p.{ProtocolKey.POSTGRES_SEARCH_NAME} @@ plainto_tsquery('english', %s) OR p.{ProtocolKey.ALIAS} LIKE %s)
                        AND
                            p.{ProtocolKey.VISIBILITY} NOT IN ({ContentVisibility.DELETED.value}, {ContentVisibility.GHOSTED.value}, {ContentVisibility.REMOVED.value})
                    ) AS match
                    ORDER BY
                        rank DESC
                    LIMIT
                        20
                    OFFSET
                        %s;
                    """,
                    (query, query, alias_pattern, offset)
                )
            elif brand_id:
                cursor.execute(
                    f"""
                    SELECT 
                        p.*,
                        b.{ProtocolKey.BRAND}
                    FROM 
                        {DatabaseTable.PRODUCT} AS p
                    LEFT JOIN (
                        SELECT
                            {ProtocolKey.ID},
                            ROW_TO_JSON(b) AS {ProtocolKey.BRAND}
                        FROM 
                            {DatabaseTable.BRAND} AS b
                    ) AS b ON p.{ProtocolKey.BRAND_ID} = b.{ProtocolKey.ID}
                    WHERE 
                        p.{ProtocolKey.BRAND_ID} = %s 
                    AND 
                        p.{ProtocolKey.PARENT_PRODUCT_ID} IS NULL
                    AND 
                        p.{ProtocolKey.VISIBILITY} NOT IN ({ContentVisibility.DELETED.value}, {ContentVisibility.GHOSTED.value}, {ContentVisibility.REMOVED.value})
                    ORDER BY
                        b.{ProtocolKey.BRAND}->>'{ProtocolKey.NAME}', p.{ProtocolKey.NAME} ASC;
                    """,
                    (brand_id,)
                )
            else:
                cursor.execute(
                    f"""
                    SELECT 
                        p.*,
                        b.{ProtocolKey.BRAND}
                    FROM 
                        {DatabaseTable.PRODUCT} AS p
                    LEFT JOIN (
                        SELECT
                            {ProtocolKey.ID},
                            ROW_TO_JSON(b) AS {ProtocolKey.BRAND}
                        FROM 
                            {DatabaseTable.BRAND} AS b
                    ) AS b ON p.{ProtocolKey.BRAND_ID} = b.{ProtocolKey.ID}
                    WHERE
                        p.{ProtocolKey.PARENT_PRODUCT_ID} IS NULL
                    AND
                        p.{ProtocolKey.VISIBILITY} NOT IN ({ContentVisibility.DELETED.value}, {ContentVisibility.GHOSTED.value}, {ContentVisibility.REMOVED.value})
                    ORDER BY
                        b.{ProtocolKey.BRAND}->>'{ProtocolKey.NAME}', p.{ProtocolKey.NAME} ASC;
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
                        user_id: int,
                        offset: int = 0) -> list[T]:
        """
        This method does not return product variants.
        """

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
                SELECT 
                    p.*,
                    b.{ProtocolKey.BRAND},
                    pp.{ProtocolKey.PARENT_PRODUCT}
                FROM 
                    {DatabaseTable.PRODUCT} AS p
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(b) AS {ProtocolKey.BRAND}
                    FROM 
                        {DatabaseTable.BRAND} AS b
                ) AS b ON p.{ProtocolKey.BRAND_ID} = b.{ProtocolKey.ID}
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(pp) AS {ProtocolKey.PARENT_PRODUCT}
                    FROM 
                        {DatabaseTable.PRODUCT} AS pp
                ) AS pp ON p.{ProtocolKey.PARENT_PRODUCT_ID} = pp.{ProtocolKey.ID}
                WHERE
                    p.{ProtocolKey.CREATOR_ID} = %s
                ORDER BY
                    b.{ProtocolKey.BRAND}->>'{ProtocolKey.NAME}', p.{ProtocolKey.NAME} ASC
                LIMIT
                    20 
                OFFSET
                    %s;
                """,
                (user_id, offset)
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
    def get_all_variants(cls: Type[T],
                         parent_product_id: int,
                         offset: int = 0):
        if not isinstance(parent_product_id, int):
            raise TypeError(f"Argument 'parent_product_id' must be of type int, not {type(parent_product_id)}.")

        if parent_product_id <= 0:
            raise ValueError("Argument 'parent_product_id' must be a positive, non-zero integer.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT 
                    p.*,
                    b.{ProtocolKey.BRAND},
                    pp.{ProtocolKey.PARENT_PRODUCT}
                FROM 
                    {DatabaseTable.PRODUCT} AS p
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(b) AS {ProtocolKey.BRAND}
                    FROM 
                        {DatabaseTable.BRAND} AS b
                ) AS b ON p.{ProtocolKey.BRAND_ID} = b.{ProtocolKey.ID}
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(pp) AS {ProtocolKey.PARENT_PRODUCT}
                    FROM 
                        {DatabaseTable.PRODUCT} AS pp
                ) AS pp ON p.{ProtocolKey.PARENT_PRODUCT_ID} = pp.{ProtocolKey.ID}
                WHERE 
                    p.{ProtocolKey.PARENT_PRODUCT_ID} = %s
                AND
                    p.{ProtocolKey.VISIBILITY} NOT IN ({ContentVisibility.DELETED.value}, {ContentVisibility.GHOSTED.value}, {ContentVisibility.REMOVED.value})
                ORDER BY
                    b.{ProtocolKey.BRAND}->>'{ProtocolKey.NAME}', p.{ProtocolKey.NAME} ASC
                LIMIT
                    20
                OFFSET
                    %s;
                """,
                (parent_product_id, offset)
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
            # This query uses a recursive plpgsql function to nest the full parent product
            # hierarchy.
            cursor.execute(
                f"""
                SELECT
                    p.*,
                    b.{ProtocolKey.BRAND},
                    c.{ProtocolKey.CREATOR},
                    get_parent_product_hierarchy(p.{ProtocolKey.PARENT_PRODUCT_ID}) AS {ProtocolKey.PARENT_PRODUCT}
                FROM
                    {DatabaseTable.PRODUCT} p
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(b) AS {ProtocolKey.BRAND}
                    FROM
                        {DatabaseTable.BRAND} b
                ) b ON p.{ProtocolKey.BRAND_ID} = b.{ProtocolKey.ID}
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(c) AS {ProtocolKey.CREATOR}
                    FROM 
                        {DatabaseTable.USER_ACCOUNT} AS c
                ) AS c ON p.{ProtocolKey.CREATOR_ID} = c.{ProtocolKey.ID}
                WHERE
                    p.{ProtocolKey.ALIAS} = %s;
                """,
                (alias,)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                ret = cls(result)
                ret.brand = Brand.get_by_id(ret.brand_id)
                ret.creator = UserAccount.get_by_id(ret.creator_id)
                ret.tags = Product.get_tags(ret.id)
                ret.variant_count = ret.get_variant_count()

                if ret.main_color_code:
                    ret.main_color = ProductColor.get_by_code(ret.main_color_code)

                if ret.material_id:
                    ret.material = ProductMaterial.get_by_id(ret.material_id)

                if ret.parent_product_id:
                    ret.parent_product = Product.get_by_id(ret.parent_product_id)

                if ret.variant_count > 0:
                    ret.variants = Product.get_some_variants(ret.id)
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
                  product_id: int) -> T:
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
            # This query uses a recursive plpgsql function to nest the full parent product
            # hierarchy.
            cursor.execute(
                f"""
                SELECT
                    p.*,
                    b.{ProtocolKey.BRAND},
                    c.{ProtocolKey.CREATOR},
                    get_parent_product_hierarchy(p.{ProtocolKey.PARENT_PRODUCT_ID}) AS {ProtocolKey.PARENT_PRODUCT}
                FROM
                    {DatabaseTable.PRODUCT} p
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(b) AS {ProtocolKey.BRAND}
                    FROM
                        {DatabaseTable.BRAND} b
                ) b ON p.{ProtocolKey.BRAND_ID} = b.{ProtocolKey.ID}
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(c) AS {ProtocolKey.CREATOR}
                    FROM 
                        {DatabaseTable.USER_ACCOUNT} AS c
                ) AS c ON p.{ProtocolKey.CREATOR_ID} = c.{ProtocolKey.ID}
                WHERE
                    p.{ProtocolKey.ID} = %s;
                """,
                (product_id,)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                ret = cls(result)
                ret.tags = Product.get_tags(ret.id)
                ret.variant_count = ret.get_variant_count()

                if ret.main_color_code:
                    ret.main_color = ProductColor.get_by_code(ret.main_color_code)

                if ret.material_id:
                    ret.material = ProductMaterial.get_by_id(ret.material_id)

                if ret.variant_count > 0:
                    ret.variants = Product.get_some_variants(ret.id)
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
        alias = alias.lower()

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    *
                FROM
                    {DatabaseTable.PRODUCT}
                WHERE
                    {ProtocolKey.ALIAS} = %s;
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
    def get_product_count(brand_id: int) -> int:
        if not isinstance(brand_id, int):
            raise TypeError(f"Argument 'brand_id' must be of type int, not {type(brand_id)}.")

        if brand_id <= 0:
            raise ValueError("Argument 'brand_id' must be a positive, non-zero integer.")

        ret: int = 0
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    COUNT(*)
                FROM
                    {DatabaseTable.PRODUCT}
                WHERE
                    {ProtocolKey.BRAND_ID} = %s
                AND
                    {ProtocolKey.PARENT_PRODUCT_ID} IS NULL;
                """,
                (brand_id,)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                for item in result.values():
                    ret = item
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    @classmethod
    def get_some_products(cls: Type[T],
                          brand_id: int,
                          count: int = 3):
        if not isinstance(brand_id, int):
            raise TypeError(f"Argument 'brand_id' must be of type int, not {type(brand_id)}.")

        if brand_id <= 0:
            raise ValueError("Argument 'brand_id' must be a positive, non-zero integer.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT 
                    p.*,
                    b.{ProtocolKey.BRAND},
                    c.{ProtocolKey.CREATOR},
                    pp.{ProtocolKey.PARENT_PRODUCT}
                FROM 
                    {DatabaseTable.PRODUCT} AS p
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(b) AS {ProtocolKey.BRAND}
                    FROM 
                        {DatabaseTable.BRAND} AS b
                ) AS b ON p.{ProtocolKey.BRAND_ID} = b.{ProtocolKey.ID}
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(c) AS {ProtocolKey.CREATOR}
                    FROM 
                        {DatabaseTable.USER_ACCOUNT} AS c
                ) AS c ON p.{ProtocolKey.CREATOR_ID} = c.{ProtocolKey.ID}
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(pp) AS {ProtocolKey.PARENT_PRODUCT}
                    FROM 
                        {DatabaseTable.PRODUCT} AS pp
                ) AS pp ON p.{ProtocolKey.PARENT_PRODUCT_ID} = pp.{ProtocolKey.ID}
                WHERE
                    p.{ProtocolKey.BRAND_ID} = %s
                AND
                    p.{ProtocolKey.PARENT_PRODUCT_ID} IS NULL
                AND
                    p.{ProtocolKey.VISIBILITY} NOT IN ({ContentVisibility.DELETED.value}, {ContentVisibility.GHOSTED.value}, {ContentVisibility.REMOVED.value})
                ORDER BY
                    p.{ProtocolKey.NAME} ASC
                LIMIT
                    %s;
                """,
                (brand_id, count)
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
    def get_some_variants(cls: Type[T],
                          parent_product_id: int,
                          count: int = 3):
        if not isinstance(parent_product_id, int):
            raise TypeError(f"Argument 'parent_product_id' must be of type int, not {type(parent_product_id)}.")

        if parent_product_id <= 0:
            raise ValueError("Argument 'parent_product_id' must be a positive, non-zero integer.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT 
                    p.*,
                    b.{ProtocolKey.BRAND},
                    c.{ProtocolKey.CREATOR},
                    pp.{ProtocolKey.PARENT_PRODUCT}
                FROM 
                    {DatabaseTable.PRODUCT} AS p
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(b) AS {ProtocolKey.BRAND}
                    FROM 
                        {DatabaseTable.BRAND} AS b
                ) AS b ON p.{ProtocolKey.BRAND_ID} = b.{ProtocolKey.ID}
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(c) AS {ProtocolKey.CREATOR}
                    FROM 
                        {DatabaseTable.USER_ACCOUNT} AS c
                ) AS c ON p.{ProtocolKey.CREATOR_ID} = c.{ProtocolKey.ID}
                LEFT JOIN (
                    SELECT
                        {ProtocolKey.ID},
                        ROW_TO_JSON(pp) AS {ProtocolKey.PARENT_PRODUCT}
                    FROM 
                        {DatabaseTable.PRODUCT} AS pp
                ) AS pp ON p.{ProtocolKey.PARENT_PRODUCT_ID} = pp.{ProtocolKey.ID}
                WHERE
                    p.{ProtocolKey.PARENT_PRODUCT_ID} = %s
                AND
                    p.{ProtocolKey.VISIBILITY} NOT IN ({ContentVisibility.DELETED.value}, {ContentVisibility.GHOSTED.value}, {ContentVisibility.REMOVED.value})
                ORDER BY
                    b.{ProtocolKey.BRAND}->>'{ProtocolKey.NAME}', p.{ProtocolKey.NAME} ASC
                LIMIT
                    %s;
                """,
                (parent_product_id, count)
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
    def get_tag(product_id: int,
                tag_id: int) -> Tag:
        if not isinstance(product_id, int):
            raise TypeError(f"Argument 'product_id' must be of type int, not {type(product_id)}.")

        if product_id <= 0:
            raise ValueError("Argument 'product_id' must be a positive, non-zero integer.")

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
                SELECT
                    *
                FROM
                    {DatabaseTable.TAG}
                INNER JOIN
                    {DatabaseTable.PRODUCT_TAG}
                ON
                    {DatabaseTable.PRODUCT_TAG}.{ProtocolKey.TAG_ID} = {DatabaseTable.TAG}.{ProtocolKey.ID}
                WHERE
                    {DatabaseTable.PRODUCT_TAG}.{ProtocolKey.PRODUCT_ID} = %s AND {DatabaseTable.TAG}.{ProtocolKey.ID} = %s;
                """,
                (product_id, tag_id)
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
    def get_tags(product_id: int) -> list[Tag]:
        if not isinstance(product_id, int):
            raise TypeError(f"Argument 'product_id' must be of type int, not {type(product_id)}.")

        if product_id <= 0:
            raise ValueError("Argument 'product_id' must be a positive, non-zero integer.")

        ret: list[Tag] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    *
                FROM
                    {DatabaseTable.TAG}
                INNER JOIN
                    {DatabaseTable.PRODUCT_TAG}
                ON
                    {DatabaseTable.PRODUCT_TAG}.{ProtocolKey.TAG_ID} = {DatabaseTable.TAG}.{ProtocolKey.ID}
                WHERE
                    {DatabaseTable.PRODUCT_TAG}.{ProtocolKey.PRODUCT_ID} = %s;
                """,
                (product_id,)
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

    def get_variant_count(self) -> int:
        if not self.id:
            raise Exception("Product has no ID associated with it.")

        ret: int = 0
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    COUNT(*)
                FROM
                    {DatabaseTable.PRODUCT}
                WHERE
                    {ProtocolKey.PARENT_PRODUCT_ID} = %s;
                """,
                (self.id,)
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                for item in result.values():
                    ret = item
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return ret

    @staticmethod
    def id_exists(product_id: int) -> bool:
        if not isinstance(product_id, int):
            raise TypeError(f"Argument 'product_id' must be of type int, not {type(product_id)}.")

        if product_id <= 0:
            raise ValueError("Argument 'product_id' must be a positive, non-zero integer.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    *
                FROM
                    {DatabaseTable.PRODUCT}
                WHERE
                    {ProtocolKey.ID} = %s;
                """,
                (product_id,)
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
                   product_id: int) -> bool:
        if not isinstance(account_id, int):
            raise TypeError(f"Argument 'account_id' must be of type int, not {type(account_id)}.")

        if account_id <= 0:
            raise ValueError("Argument 'account_id' must be a positive, non-zero integer.")

        if not isinstance(product_id, int):
            raise TypeError(f"Argument 'product_id' must be of type int, not {type(product_id)}.")

        if product_id <= 0:
            raise ValueError("Argument 'product_id' must be a positive, non-zero integer.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    *
                FROM
                    {DatabaseTable.PRODUCT_MANAGER}
                WHERE
                    {ProtocolKey.USER_ACCOUNT_ID} = %s
                AND
                    {ProtocolKey.PRODUCT_ID} = %s;
                """,
                (account_id, product_id)
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
            raise Exception("Product has no ID associated with it.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    *
                FROM
                    {DatabaseTable.PRODUCT}
                RIGHT JOIN ON
                    {DatabaseTable.PRODUCT_MANAGER}.{ProtocolKey.USER_ACCOUNT_ID} = {DatabaseTable.USER_ACCOUNT}.{ProtocolKey.ID}
                WHERE
                    {ProtocolKey.ID} = %s;
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
            raise Exception("Product has no ID associated with it.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE
                    {DatabaseTable.PRODUCT}
                SET
                    {ProtocolKey.EDIT_ACCESS_LEVEL} = %s
                WHERE
                    {ProtocolKey.ID} = %s;
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
        [NOTE] This method does not delete the product's record from the database.
        """

        if not isinstance(visibility, ContentVisibility):
            raise TypeError(f"Argument 'visibility' must be of type ContentVisibility, not {type(visibility)}.")

        if not visibility:
            raise ValueError("Argument 'visibility' is None.")

        if not self.id:
            raise Exception("Product has no ID associated with it.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE
                    {DatabaseTable.PRODUCT}
                SET
                    {ProtocolKey.VISIBILITY} = %s
                WHERE
                    {ProtocolKey.ID} = %s;
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
            raise Exception("Product must have an alias associated with it.")

        if not self.id:
            raise Exception("Product has no ID associated with it.")

        if not self.name:
            raise Exception("Product must have a name associated with it.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE
                    {DatabaseTable.PRODUCT}
                SET
                    {ProtocolKey.DESCRIPTION} = %s, {ProtocolKey.OVERRIDES_DISPLAY_NAME} = %s, {ProtocolKey.MAIN_COLOR_CODE} = %s,
                    {ProtocolKey.MATERIAL_ID} = %s, {ProtocolKey.NAME} = %s, {ProtocolKey.PARENT_PRODUCT_ID} = %s,
                    {ProtocolKey.PREORDER_TIMESTAMP} = %s, {ProtocolKey.RELEASE_TIMESTAMP} = %s, {ProtocolKey.STATUS} = %s,
                    {ProtocolKey.UPC} = %s, {ProtocolKey.URL} = %s
                WHERE
                    {ProtocolKey.ID} = %s;
                """,
                (self.description, self.display_name_override, self.main_color_code,
                 self.material_id, self.name, self.parent_product_id,
                 self.preorder_timestamp, self.release_timestamp, self.status.value,
                 self.upc, self.url, self.id)
            )
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()


class ProductEditHistory:
    def __init__(self,
                 data: dict) -> None:
        self.action_id: UserAction = UserAction.UNDEFINED
        self.product_id: int = 0
        self.editor_id: int = 0
        self.field_id: Field = Field.UNDEFINED
        self.field_value: Any = None

        if data:
            if ProtocolKey.ACTION_ID in data:
                self.action_id: UserAction = UserAction(data[ProtocolKey.ACTION_ID])

            if ProtocolKey.PRODUCT_ID in data:
                self.product_id: int = data[ProtocolKey.PRODUCT_ID]

            if ProtocolKey.EDITOR_ID in data:
                self.editor_id: int = data[ProtocolKey.EDITOR_ID]

            if ProtocolKey.FIELD_ID in data:
                self.field_id: Field = Field(data[ProtocolKey.FIELD_ID])

            if ProtocolKey.FIELD_VALUE in data:
                self.field_value: Any = data[ProtocolKey.FIELD_VALUE]


####################
# MODULE FUNCTIONS #
####################


def allowed_media_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Configuration.ALLOWED_PRODUCT_MEDIA_FILE_EXTENSIONS


def create_product(alias: str,
                   brand_id: str,
                   name: str,
                   parent_product_id: str = None,
                   tags: str = None) -> tuple[dict, ResponseStatus]:
    if brand_id:
        try:
            brand_id = int(brand_id)

            if brand_id <= 0:
                brand_id = None
        except ValueError:
            brand_id = None
    else:
        brand_id = None

    if name:
        name = name.strip()
    else:
        name = None

    if parent_product_id:
        try:
            parent_product_id = int(parent_product_id)

            if parent_product_id <= 0:
                parent_product_id = None
        except ValueError:
            parent_product_id = None
    else:
        parent_product_id = None

    if tags:
        try:
            tags = json.loads(tags)
        except:
            tags = None
    else:
        tags = None

    if not alias or \
            not brand_id or \
            not name or \
            (parent_product_id and parent_product_id <= 0) or \
            (not parent_product_id and not tags):
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not alias:
            error_message += ": 'alias' must be an ASCII non-empty string."
        elif not brand_id:
            error_message += ": 'brand_id' must be a positive, non-zero integer."
        elif not name:
            error_message += ": 'code' must be a non-empty string."
        elif parent_product_id and parent_product_id <= 0:
            error_message += ": 'parent_product_id' must be a positive, non-zero integer."
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

        if response_status == ResponseStatus.OK and tags:
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

            if Product.alias_valid(alias):
                if not Product.alias_exists(alias):
                    brand = Brand.get_by_id(brand_id)

                    if brand and \
                            brand.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
                        if parent_product_id:
                            parent_product = Product.get_by_id(parent_product_id)

                            if not parent_product:
                                response_status = ResponseStatus.BAD_REQUEST
                                response = {
                                    ProtocolKey.ERROR: {
                                        ProtocolKey.ERROR_CODE: ResponseStatus.PRODUCT_NOT_FOUND.value,
                                        ProtocolKey.ERROR_MESSAGE: "Invalid parent product ID."
                                    }
                                }
                            elif parent_product.name.lower() == name.lower():
                                response_status = ResponseStatus.BAD_REQUEST
                                response = {
                                    ProtocolKey.ERROR: {
                                        ProtocolKey.ERROR_CODE: ResponseStatus.NAME_INVALID.value,
                                        ProtocolKey.ERROR_MESSAGE: "A variant can't have the same name as its parent product."
                                    }
                                }
                        else:
                            parent_product = None

                        if response_status == ResponseStatus.OK:
                            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
                            creator = UserAccount.get_by_session(session_id)
                            product = Product.create(
                                alias,
                                brand_id,
                                creator.id,
                                name,
                                parent_product_id,
                                ProductStatus.AVAILABLE
                            )

                            if product:
                                product.create_manager(creator.id)

                                if tags:
                                    for tag_name in tags:
                                        tag = Tag.get_by_name(tag_name)

                                        if not tag:
                                            tag = Tag.create(tag_name, creator.id)

                                        product.create_tag(tag.id)

                                product.tags = Product.get_tags(product.id)

                                response = {
                                    ProtocolKey.PRODUCT: product.as_dict()
                                }
                            else:
                                response_status = ResponseStatus.INTERNAL_SERVER_ERROR
                                response = {
                                    ProtocolKey.ERROR: {
                                        ProtocolKey.ERROR_CODE: response_status.value,
                                        ProtocolKey.ERROR_MESSAGE: "An error occurred while trying to add the product."
                                    }
                                }
                    else:
                        # Invalid brand ID.
                        response_status = ResponseStatus.BAD_REQUEST
                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: ResponseStatus.BRAND_NOT_FOUND.value,
                                ProtocolKey.ERROR_MESSAGE: "Invalid brand ID."
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


def delete_product(product_id: str) -> tuple[dict, ResponseStatus]:
    if product_id:
        try:
            product_id = int(product_id)

            if product_id <= 0:
                product_id = None
        except ValueError:
            product_id = None

    if not product_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'product_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}
        product = Product.get_by_id(product_id)

        if product:
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
            user_account = UserAccount.get_by_session(session_id)

            if user_account.is_admin:
                product.delete()

                response = {
                    ProtocolKey.PRODUCT_ID: product.id
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
                    ProtocolKey.ERROR_CODE: ResponseStatus.PRODUCT_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No product exists for this ID."
                }
            }

    return (response, response_status)


def get_product(alias: str = None,
                product_id: str = None) -> tuple[dict, ResponseStatus]:
    if product_id:
        try:
            product_id = int(product_id)

            if product_id <= 0:
                product_id = None
        except ValueError:
            product_id = None

    if not alias and \
            not product_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'alias' must be a non-empty string or 'product_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}

        if product_id:
            product = Product.get_by_id(product_id)
        else:
            if Product.alias_valid(alias):
                product = Product.get_by_alias(alias)
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
            if product and \
                    product.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
                product.media = ProductMedium.get_all(product.id)

                response = {
                    ProtocolKey.PRODUCT: product.as_dict()
                }
            else:
                response_status = ResponseStatus.NOT_FOUND
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.PRODUCT_NOT_FOUND.value,
                        ProtocolKey.ERROR_MESSAGE: "No product exists for this alias/product ID."
                    }
                }

    return (response, response_status)


def get_product_variants(offset: str = None,
                         parent_product_id: str = None) -> tuple[dict, ResponseStatus]:
    if parent_product_id:
        try:
            parent_product_id = int(parent_product_id)

            if parent_product_id <= 0:
                parent_product_id = None
        except ValueError:
            parent_product_id = None
    else:
        parent_product_id = None

    if offset:
        try:
            offset = int(offset)

            if offset <= 0:
                offset = None
        except ValueError:
            offset = 0
    else:
        offset = 0

    if not parent_product_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'parent_product_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        serialized = []

        variants = Product.get_all_variants(parent_product_id, offset=offset)

        for variant in variants:
            if variant.parent_product_id:
                variant.parent_product = Product.get_by_id(variant.parent_product_id)

            serialized.append(variant.as_dict())

        response = {
            ProtocolKey.PRODUCT_VARIANTS: serialized
        }

    return (response, response_status)


def get_products(query: str = None,
                 brand_id: str = None) -> tuple[dict, ResponseStatus]:
    response_status = ResponseStatus.OK
    serialized = []

    if isinstance(query, str):
        query = query.strip()
        results = Product.get_all(query=query)

        for result in results:
            serialized.append(result.as_dict())
    elif brand_id:
        try:
            brand_id = int(brand_id)

            if brand_id > 0:
                results = Product.get_all(brand_id=brand_id)

                for result in results:
                    serialized.append(result.as_dict())
        except ValueError:
            pass

    response = {
        ProtocolKey.PRODUCTS: serialized
    }

    return (response, response_status)


def remove_product(product_id: str) -> tuple[dict, ResponseStatus]:
    if product_id:
        try:
            product_id = int(product_id)

            if product_id <= 0:
                product_id = None
        except ValueError:
            product_id = None

    if not product_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'product_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}
        product = Product.get_by_id(product_id)

        if product and \
                product.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
            user_account = UserAccount.get_by_session(session_id)

            if user_account.is_admin or Product.is_manager(user_account.id, product_id):
                if user_account.id == product.creator_id:
                    visibility = ContentVisibility.DELETED
                else:
                    visibility = ContentVisibility.REMOVED

                product.set_visibility(visibility)

                response = {
                    ProtocolKey.VISIBILITY: visibility.value
                }
            else:
                response_status = ResponseStatus.FORBIDDEN
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: response_status.value,
                        ProtocolKey.ERROR_MESSAGE: "User account is neither an admin nor a manager of this product."
                    }
                }
        else:
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.PRODUCT_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No product exists for this ID."
                }
            }

    return (response, response_status)


def update_media(media_mode: str,
                 metadata: str,
                 product_id: str) -> tuple[dict, ResponseStatus]:
    if product_id:
        try:
            product_id = int(product_id)

            if product_id <= 0:
                product_id = None
        except ValueError:
            product_id = None
    else:
        product_id = None

    if media_mode:
        try:
            media_mode = MediaMode(int(media_mode))
        except ValueError:
            media_mode = None
    else:
        media_mode = None

    if metadata:
        try:
            metadata: dict = json.loads(metadata)
        except:
            metadata = None
    else:
        metadata = None

    if not product_id or \
            not media_mode:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not product_id:
            error_message += ": 'product_id' must be a positive, non-zero integer."
        if not media_mode:
            error_message += ": 'media_mode' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    elif len(request.files) > Configuration.PRODUCT_MEDIA_MAX_COUNT:
        response_status = ResponseStatus.PAYLOAD_TOO_LARGE
        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: f"A maximum of {Configuration.PRODUCT_MEDIA_MAX_COUNT} product media files is allowed."
            }
        }
    else:
        exists = Product.id_exists(product_id)

        if exists:
            response_status = ResponseStatus.OK
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
            user = UserAccount.get_by_session(session_id)
            existing_media = ProductMedium.get_all(product_id)
            uploaded_media: dict[str, ProductMedium] = {}

            # Pre-processing step.
            for key, medium_metadata in metadata.items():
                medium = ProductMedium(medium_metadata)
                medium.media_mode = media_mode

                if medium.attribution:
                    medium.attribution = medium.attribution.strip()

                    if len(medium.attribution) > Configuration.ATTRIBUTION_MAX_LEN:
                        response_status = ResponseStatus.BAD_REQUEST
                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: ResponseStatus.ATTRIBUTION_INVALID,
                                ProtocolKey.ERROR_MESSAGE: f"Attribution cannot exceed {Configuration.ATTRIBUTION_MAX_LEN} characters."
                            }
                        }
                        break

                uploaded_media[key] = medium

            if response_status == ResponseStatus.OK:
                for key, file in request.files.items():
                    if allowed_media_file(file.filename):
                        medium_bytes = file.read()
                        medium_hash = hashlib.sha256(medium_bytes).hexdigest()
                        # Not necessarily on the local filesystem.
                        medium_path = f"product/{product_id}/{medium_hash}_media_full.jpg"
                        # This is also the object key for S3.
                        medium_metadata = uploaded_media[key]
                        medium_metadata.file_path = medium_path

                        product_media_dir = os.path.join(Configuration.PRODUCT_MEDIA_DIR, f"{product_id}")
                        os.makedirs(product_media_dir, exist_ok=True)
                        # We'd like to standardize all product images to be in JPEG format.
                        file_path_final = os.path.join(product_media_dir, f"{medium_hash}_media_full.jpg")

                        medium_filename = secure_filename(file.filename)
                        file_path_tmp = os.path.join("/tmp", medium_filename)
                        file.stream.seek(0)
                        file.save(file_path_tmp)

                        try:
                            # Convert to JPEG.
                            pil_image = Image.open(file_path_tmp)
                            pil_image.save(file_path_final)
                        except IOError:
                            # File is not an image file.
                            response_status = ResponseStatus.BAD_REQUEST
                            response = {
                                ProtocolKey.ERROR: {
                                    ProtocolKey.ERROR_CODE: ResponseStatus.MEDIA_INVALID.value,
                                    ProtocolKey.ERROR_MESSAGE: f"Invalid file. Allowed media formats: {', '.join(Configuration.ALLOWED_PRODUCT_MEDIA_FILE_EXTENSIONS)}"
                                }
                            }
                        finally:
                            # Clean up.
                            os.remove(file_path_tmp)

                            if response_status != ResponseStatus.OK:
                                break

            if response_status == ResponseStatus.OK:
                final: list[ProductMedium] = []

                for key, medium in uploaded_media.items():
                    if key in request.files.keys():
                        # New upload.
                        new_medium = ProductMedium.create(
                            medium.attribution,
                            user.id,
                            medium.file_path,
                            medium.index,
                            media_mode,
                            medium.media_type,
                            product_id
                        )
                        final.append(new_medium)

                        if not app.debug:
                            file_path_final = os.path.join(Configuration.MEDIA_DIR, medium.file_path)
                            s3.upload_media(file_path_final, medium.file_path)
                            # Don't need the local file anymore.
                            os.remove(file_path_final)

                        Product.add_history(
                            product_id,
                            user.id,
                            UserAction.ADDED,
                            Field.PRODUCT_MEDIA,
                            medium.file_path
                        )
                    else:
                        # Update to an existing medium.
                        medium.update()
                        final.append(medium)
                        Product.add_history(
                            product_id,
                            user.id,
                            UserAction.UPDATED,
                            Field.PRODUCT_MEDIA_ATTRIBUTION,
                            medium.attribution
                        )

                # Check which media are in existing but not in upload.
                # These need to be deleted.
                for existing in existing_media:
                    exists = False

                    for uploaded in uploaded_media.values():
                        if uploaded.id == existing.id:
                            uploaded.creation_timestamp = existing.creation_timestamp
                            uploaded.creator = existing.creator
                            uploaded.creator_id = existing.creator_id
                            uploaded.file_path = existing.file_path
                            exists = True
                            break

                    if not exists:
                        existing.delete()

                        if app.debug:
                            # Delete the local file.
                            try:
                                os.remove(os.path.join(Configuration.MEDIA_DIR, existing.file_path))
                            except OSError:
                                pass
                        else:
                            s3.delete_media(existing.file_path)

                        Product.add_history(
                            product_id,
                            user.id,
                            UserAction.DELETED,
                            Field.PRODUCT_MEDIA,
                            existing.file_path
                        )

                final_serialized = []

                for medium in final:
                    final_serialized.append(medium.as_dict())

                response = {
                    ProtocolKey.MEDIA: final_serialized,
                    ProtocolKey.PRODUCT_ID: product_id
                }
        else:
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.PRODUCT_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No product exists for this ID."
                }
            }

    return (response, response_status)


def update_product(description: str,
                   display_name_override: str,
                   main_color_code: str,
                   material_id: str,
                   name: str,
                   parent_product_id: str,
                   preorder_timestamp: str,
                   product_id: str,
                   release_timestamp: str,
                   status: str,
                   upc: str,
                   tags: str,
                   url: str) -> tuple[dict, ResponseStatus]:
    if description:
        description = description.strip()
    else:
        description = None

    if display_name_override:
        display_name_override = display_name_override.lower()

        if display_name_override == "true" or display_name_override == "1":
            display_name_override = True
        else:
            display_name_override = False
    else:
        display_name_override = False

    if main_color_code:
        main_color_code = main_color_code.strip()
    else:
        main_color_code = None

    if material_id:
        try:
            material_id = int(material_id)

            if material_id <= 0:
                material_id = None
        except ValueError:
            material_id = None
    else:
        material_id = None

    if name:
        name = name.strip()
    else:
        name = None

    if parent_product_id:
        try:
            parent_product_id = int(parent_product_id)

            if parent_product_id <= 0:
                parent_product_id = None
        except ValueError:
            parent_product_id = None
    else:
        parent_product_id = None

    if preorder_timestamp:
        try:
            preorder_timestamp = date_parser.parse(preorder_timestamp.strip())
        except ValueError:
            preorder_timestamp = None
    else:
        preorder_timestamp = None

    if product_id:
        try:
            product_id = int(product_id)

            if product_id <= 0:
                product_id = None
        except ValueError:
            product_id = None
    else:
        product_id = None

    if release_timestamp:
        try:
            release_timestamp = date_parser.parse(release_timestamp.strip())
        except ValueError:
            release_timestamp = None
    else:
        release_timestamp = None

    if status:
        try:
            status = ProductStatus(int(status))
        except ValueError:
            status = None
    else:
        status = None

    if tags:
        try:
            tags: list = json.loads(tags)
        except:
            tags = None
    else:
        tags = None

    if upc:
        upc = upc.strip()
    else:
        upc = None

    if url:
        url = "".join(char for char in url if char in string.printable)

        try:
            url_test = urlparse(url)

            if not url_test.scheme:
                url = "http://" + url
        except Exception:
            url = None
    else:
        url = None

    if not name or \
            (parent_product_id and parent_product_id <= 0) or \
            not product_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not name:
            error_message += ": 'name' must be a non-empty string."
        elif not product_id:
            error_message += ": 'product_id' must be a positive, non-zero integer."
        elif parent_product_id and parent_product_id <= 0:
            error_message += ": 'parent_product_id' must be a positive, non-zero integer."

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

        if response_status == ResponseStatus.OK and tags:
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

        if response_status == ResponseStatus.OK and url:
            if url and len(url) > Configuration.URL_MAX_LEN:
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.URL_INVALID.value,
                        ProtocolKey.ERROR_MESSAGE: f"URL can't be more than {Configuration.URL_MAX_LEN} characters long."
                    }
                }

        if response_status == ResponseStatus.OK:
            product = Product.get_by_id(product_id)

            if product and \
                    product.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
                session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
                user_account = UserAccount.get_by_session(session_id)

                if parent_product_id:
                    parent_product = Product.get_by_id(parent_product_id)

                    if not parent_product:
                        response_status = ResponseStatus.BAD_REQUEST
                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: ResponseStatus.PRODUCT_NOT_FOUND.value,
                                ProtocolKey.ERROR_MESSAGE: "Invalid parent product ID."
                            }
                        }
                    elif parent_product.name.lower() == name.lower():
                        response_status = ResponseStatus.BAD_REQUEST
                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: ResponseStatus.NAME_INVALID.value,
                                ProtocolKey.ERROR_MESSAGE: "A variant can't have the same name as its parent product."
                            }
                        }
                else:
                    parent_product = None

                if response_status == ResponseStatus.OK:
                    if product.edit_access_level == EditAccessLevel.OPEN or \
                            (product.edit_access_level == EditAccessLevel.PUBLICLY_ACCESSIBLE and Product.is_manager(user_account.id, product_id)) or \
                            user_account.is_admin:
                        auditEntries = []

                        if description != product.description:
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.UPDATED,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.DESCRIPTION,
                                ProtocolKey.FIELD_VALUE: description,
                                ProtocolKey.PRODUCT_ID: product.id
                            })

                        if display_name_override != product.display_name_override:
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.UPDATED,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.DISPLAY_NAME_OVERRIDE,
                                ProtocolKey.FIELD_VALUE: display_name_override,
                                ProtocolKey.PRODUCT_ID: product.id
                            })

                        if main_color_code != product.main_color_code:
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.UPDATED,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.MAIN_COLOR,
                                ProtocolKey.FIELD_VALUE: main_color_code,
                                ProtocolKey.PRODUCT_ID: product.id
                            })

                        if material_id != product.material_id:
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.UPDATED,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.MATERIAL,
                                ProtocolKey.FIELD_VALUE: material_id,
                                ProtocolKey.PRODUCT_ID: product.id
                            })

                        if name != product.name:
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.UPDATED,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.NAME,
                                ProtocolKey.FIELD_VALUE: name,
                                ProtocolKey.PRODUCT_ID: product.id
                            })

                        if parent_product_id != product.parent_product_id:
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.UPDATED,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.PARENT_PRODUCT,
                                ProtocolKey.FIELD_VALUE: parent_product_id,
                                ProtocolKey.PRODUCT_ID: product.id
                            })

                        if preorder_timestamp != product.preorder_timestamp:
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.UPDATED,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.PREORDER_TIMESTAMP,
                                ProtocolKey.FIELD_VALUE: preorder_timestamp,
                                ProtocolKey.PRODUCT_ID: product.id
                            })

                        if release_timestamp != product.release_timestamp:
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.UPDATED,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.RELEASE_TIMESTAMP,
                                ProtocolKey.FIELD_VALUE: release_timestamp,
                                ProtocolKey.PRODUCT_ID: product.id
                            })

                        if status != product.status:
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.UPDATED,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.STATUS,
                                ProtocolKey.FIELD_VALUE: status,
                                ProtocolKey.PRODUCT_ID: product.id
                            })

                        if upc != product.upc:
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.UPDATED,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.UPC,
                                ProtocolKey.FIELD_VALUE: upc,
                                ProtocolKey.PRODUCT_ID: product.id
                            })

                        if url != product.url:
                            auditEntries.append({
                                ProtocolKey.ACTION_ID: UserAction.UPDATED,
                                ProtocolKey.EDITOR_ID: user_account.id,
                                ProtocolKey.FIELD_ID: Field.WEBSITE,
                                ProtocolKey.FIELD_VALUE: url,
                                ProtocolKey.PRODUCT_ID: product.id
                            })

                        # Make sure to always inherit the brand of the parent.
                        if parent_product:
                            product.brand = parent_product.brand
                            product.brand_id = parent_product.brand_id

                        product.description = description
                        product.display_name_override = display_name_override
                        product.main_color_code = main_color_code
                        product.material_id = material_id
                        product.name = name
                        product.parent_product = parent_product
                        product.parent_product_id = parent_product_id
                        product.preorder_timestamp = preorder_timestamp
                        product.release_timestamp = release_timestamp
                        product.status = status
                        product.upc = upc
                        product.url = url
                        product.update()

                        if main_color_code:
                            product.main_color = ProductColor.get_by_code(main_color_code)
                        else:
                            product.main_color = None

                        if material_id:
                            product.material = ProductMaterial.get_by_id(material_id)
                        else:
                            product.material = None

                        if product.parent_product_id:
                            product.parent_product = Product.get_by_id(product.parent_product_id)
                        else:
                            product.parent_product = None

                        if tags:
                            for tag_name in tags:
                                exists = False

                                for tag in product.tags:
                                    if tag_name == tag.name:
                                        exists = True
                                        break

                                if not exists:
                                    tag = Tag.get_by_name(tag_name)

                                    if not tag:
                                        tag = Tag.create(tag_name, user_account.id)

                                    product.create_tag(tag.id)
                                    auditEntries.append({
                                        ProtocolKey.ACTION_ID: UserAction.ADDED,
                                        ProtocolKey.EDITOR_ID: user_account.id,
                                        ProtocolKey.FIELD_ID: Field.TAGS,
                                        ProtocolKey.FIELD_VALUE: tag.id,
                                        ProtocolKey.PRODUCT_ID: product.id
                                    })

                        for tag in product.tags:
                            exists = False

                            if tags:
                                for tag_name in tags:
                                    if tag_name == tag.name:
                                        exists = True
                                        break

                            if not exists:
                                product.delete_tag(tag.id)
                                auditEntries.append({
                                    ProtocolKey.ACTION_ID: UserAction.DELETED,
                                    ProtocolKey.EDITOR_ID: user_account.id,
                                    ProtocolKey.FIELD_ID: Field.TAGS,
                                    ProtocolKey.FIELD_VALUE: tag.id,
                                    ProtocolKey.PRODUCT_ID: product.id
                                })

                        product.tags = Product.get_tags(product.id)

                        for entry in auditEntries:
                            product.add_history(**entry)

                        response = {
                            ProtocolKey.PRODUCT: product.as_dict()
                        }
                    else:
                        response_status = ResponseStatus.FORBIDDEN
                        response = {
                            ProtocolKey.ERROR: {
                                ProtocolKey.ERROR_CODE: response_status.value,
                                ProtocolKey.ERROR_MESSAGE: "User account is neither an admin nor a manager of this product."
                            }
                        }
            else:
                response_status = ResponseStatus.NOT_FOUND
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.PRODUCT_NOT_FOUND.value,
                        ProtocolKey.ERROR_MESSAGE: "No product exists for this ID."
                    }
                }

    return (response, response_status)
