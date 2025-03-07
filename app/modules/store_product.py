from datetime import datetime
from decimal import Decimal
import string
from flask import request
from typing import Any, TypeVar, Type
from urllib.parse import urlparse

from app.config import ContentVisibility, DatabaseTable, EditAccessLevel, \
    ProtocolKey, ResponseStatus, StoreProductStatus
from app.modules import db
from app.modules.product import Product
from app.modules.store import Store
from app.modules.user_account import UserAccount


###########
# CLASSES #
###########


T = TypeVar("T", bound="StoreProduct")


class StoreProduct:
    def __init__(self,
                 data: dict) -> None:
        self.condition: str = None
        self.creation_timestamp: datetime = None
        self.creator_id: int = 0
        self.description: str = None
        self.id: int = 0
        self.price: Decimal = 0.0
        self.product: Product = None
        self.status: StoreProductStatus = StoreProductStatus.AVAILABLE
        self.store_id: int = 0
        self.url: str = None

        if data:
            if ProtocolKey.CONDITION in data:
                self.condition: str = data[ProtocolKey.CONDITION]

            if ProtocolKey.CREATION_TIMESTAMP in data:
                self.creation_timestamp: datetime = data[ProtocolKey.CREATION_TIMESTAMP]

            if ProtocolKey.CREATOR_ID in data:
                self.creator_id: int = data[ProtocolKey.CREATOR_ID]

            if ProtocolKey.DESCRIPTION in data:
                self.description: str = data[ProtocolKey.DESCRIPTION]

            if ProtocolKey.ID in data:
                self.id: int = data[ProtocolKey.ID]

            if ProtocolKey.PRICE in data:
                self.price: Decimal = Decimal(data[ProtocolKey.PRICE])

            if ProtocolKey.PRODUCT_ID in data and data[ProtocolKey.PRODUCT_ID]:
                self.product = Product.get_by_id(data[ProtocolKey.PRODUCT_ID])

            if ProtocolKey.STATUS in data and data[ProtocolKey.STATUS]:
                self.status = StoreProductStatus(data[ProtocolKey.STATUS])

            if ProtocolKey.STORE_ID in data:
                self.store_id: int = data[ProtocolKey.STORE_ID]

            if ProtocolKey.URL in data:
                self.url: str = data[ProtocolKey.URL]

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
        ret = "Store Product " + self.id.__str__()

        if self.product:
            ret += f" ({self.product.name})"

        return ret

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.CONDITION: self.condition,
            ProtocolKey.CREATOR_ID: self.creator_id,
            ProtocolKey.DESCRIPTION: self.description,
            ProtocolKey.ID: self.id,
            ProtocolKey.PRICE: self.price,
            ProtocolKey.STORE_ID: self.store_id,
            ProtocolKey.URL: self.url
        }

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        if self.product:
            serialized[ProtocolKey.PRODUCT] = self.product.as_dict()

        if self.status:
            serialized[ProtocolKey.STATUS] = self.status.value

        return serialized

    @classmethod
    def create(cls: Type[T],
               creator_id: int,
               price: Decimal,
               product_id: int,
               status: StoreProductStatus,
               store_id: int) -> T:
        if not isinstance(creator_id, int):
            raise TypeError(f"Argument 'creator_id' must be of type int, not {type(creator_id)}.")

        if creator_id <= 0:
            raise ValueError("Argument 'creator_id' must be a positive, non-zero integer.")

        if not isinstance(price, Decimal):
            raise TypeError(f"Argument 'price' must be of type Decimal, not {type(price)}.")

        if price < 0:
            raise ValueError("Argument 'price' must be greater than or equal to zero.")

        if not isinstance(product_id, int):
            raise TypeError(f"Argument 'product_id' must be of type int, not {type(product_id)}.")

        if product_id <= 0:
            raise ValueError("Argument 'product_id' must be a positive, non-zero integer.")

        if not isinstance(store_id, int):
            raise TypeError(f"Argument 'store_id' must be of type int, not {type(store_id)}.")

        if store_id <= 0:
            raise ValueError("Argument 'store_id' must be a positive, non-zero integer.")

        if not isinstance(status, StoreProductStatus):
            raise TypeError(f"Argument 'status' must be of type StoreProductStatus, not {type(status)}.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.STORE_PRODUCT}
                ({ProtocolKey.CREATOR_ID}, {ProtocolKey.PRICE}, {ProtocolKey.PRODUCT_ID},
                  {ProtocolKey.STATUS}, {ProtocolKey.STORE_ID})
                VALUES
                (%s, %s, %s,
                 %s)
                 RETURNING *;
                """,
                (creator_id, price, product_id, status.value, store_id)
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
        """
        [NOTE] This method erases the store product's record from the database.
        """

        if not self.id:
            raise Exception("Deletion requires a store product ID.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.STORE_PRODUCT}
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
    def get_all_by_store(cls: Type[T],
                         store_id: int) -> list[T]:
        if not isinstance(store_id, int):
            raise TypeError(f"Argument 'store_id' must be of type int, not {type(store_id)}.")

        if store_id <= 0:
            raise ValueError("Argument 'store_id' must be a positive, non-zero integer.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.STORE_PRODUCT}
                WHERE {ProtocolKey.STORE_ID} = %s;
                """,
                (store_id,)
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
                SELECT * FROM {DatabaseTable.STORE_PRODUCT}
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
                  store_product_id: int) -> T:
        if not isinstance(store_product_id, int):
            raise TypeError(f"Argument 'store_product_id' must be of type int, not {type(store_product_id)}.")

        if store_product_id <= 0:
            raise ValueError("Argument 'store_product_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.STORE_PRODUCT}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (store_product_id,)
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
    def id_exists(store_product_id: int) -> bool:
        if not isinstance(store_product_id, int):
            raise TypeError(f"Argument 'store_product_id' must be of type int, not {type(store_product_id)}.")

        if store_product_id <= 0:
            raise ValueError("Argument 'store_product_id' must be a positive, non-zero integer.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.STORE_PRODUCT}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (store_product_id,)
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
            raise Exception("Store Product has no ID associated with it.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.STORE_PRODUCT}
                SET {ProtocolKey.CONDITION} = %s, {ProtocolKey.DESCRIPTION} = %s, {ProtocolKey.PRICE} = %s,
                {ProtocolKey.STATUS} = %s, {ProtocolKey.URL} = %s
                WHERE {ProtocolKey.ID} = %s;
                """,
                (self.condition, self.description, self.price,
                 self.status.value, self.url, self.id)
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


def create_store_product(price: str,
                         product_id: str,
                         store_id: str) -> tuple[dict, ResponseStatus]:
    if price:
        try:
            price = Decimal(price)
        except ValueError:
            price = None
    else:
        price = None

    if product_id:
        try:
            product_id = int(product_id)

            if product_id <= 0:
                product_id = None
        except ValueError:
            product_id = None
    else:
        product_id = None

    if store_id:
        try:
            store_id = int(store_id)

            if store_id <= 0:
                store_id = None
        except ValueError:
            store_id = None
    else:
        store_id = None

    if not price or \
            not product_id or \
            not store_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not price:
            error_message += ": 'price' must be a floating point value greater than or equal to zero."
        elif not product_id:
            error_message += ": 'product_id' must be a positive, non-zero integer."
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
        product = Product.get_by_id(product_id)

        if product and \
                product.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
            store = Store.get_by_id(store_id)

            if store and \
                    store.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
                session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
                creator = UserAccount.get_by_session(session_id)
                store_product = StoreProduct.create(
                    creator.id,
                    price,
                    product_id,
                    store_id,
                    StoreProductStatus.AVAILABLE
                )

                if store_product:
                    response = {
                        ProtocolKey.STORE_PRODUCT: store_product.as_dict()
                    }
                else:
                    response_status = ResponseStatus.INTERNAL_SERVER_ERROR
                    response = {
                        ProtocolKey.ERROR: {
                            ProtocolKey.ERROR_CODE: response_status.value,
                            ProtocolKey.ERROR_MESSAGE: "An error occurred while trying to add the store product."
                        }
                    }
            else:
                # Invalid store ID.
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.STORE_NOT_FOUND.value,
                        ProtocolKey.ERROR_MESSAGE: "Invalid store ID."
                    }
                }
        else:
            # Invalid product ID.
            response_status = ResponseStatus.BAD_REQUEST
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.PRODUCT_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "Invalid product ID."
                }
            }

    return (response, response_status)


def delete_store_product(store_product_id: str) -> tuple[dict, ResponseStatus]:
    if store_product_id:
        try:
            store_product_id = int(store_product_id)

            if store_product_id <= 0:
                store_product_id = None
        except ValueError:
            store_product_id = None
    else:
        store_product_id = None

    if not store_product_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'store_product_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}
        store_product = StoreProduct.get_by_id(store_product_id)

        if store_product:
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
            user_account = UserAccount.get_by_session(session_id)

            if user_account.is_admin:
                store_product.delete()

                response = {
                    ProtocolKey.STORE_PRODUCT_ID: store_product.id
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
                    ProtocolKey.ERROR_CODE: ResponseStatus.STORE_PRODUCT_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No store product exists for this ID."
                }
            }

    return (response, response_status)


def get_store_product(store_product_id: str) -> tuple[dict, ResponseStatus]:
    if store_product_id:
        try:
            store_product_id = int(store_product_id)

            if store_product_id <= 0:
                store_product_id = None
        except ValueError:
            store_product_id = None

    if not store_product_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'store_product_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}
        store_product = StoreProduct.get_by_id(store_product_id)

        if store_product:
            store = Store.get_by_id(store_product.store_id)

            if store and \
                    store.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
                response = {
                    ProtocolKey.STORE_PRODUCT: store_product.as_dict()
                }
            else:
                # Invalid store ID.
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.STORE_NOT_FOUND.value,
                        ProtocolKey.ERROR_MESSAGE: "Invalid store ID."
                    }
                }
        else:
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.STORE_PRODUCT_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No store product exists for this ID."
                }
            }

    return (response, response_status)


def get_store_products(store_id: str) -> tuple[dict, ResponseStatus]:
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
        store = Store.get_by_id(store_id)

        if store and \
                store.visibility not in frozenset([ContentVisibility.DELETED, ContentVisibility.REMOVED]):
            response_status = ResponseStatus.OK
            serialized = []
            results = StoreProduct.get_all_by_store(store_id)

            for result in results:
                serialized.append(result.as_dict())

            response = {
                ProtocolKey.STORE_PRODUCTS: serialized
            }
        else:
            # Invalid store ID.
            response_status = ResponseStatus.BAD_REQUEST
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.STORE_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "Invalid store ID."
                }
            }

    return (response, response_status)


def update_store_product(condition: str,
                         description: str,
                         price: str,
                         status: str,
                         store_product_id: str,
                         url: str) -> tuple[dict, ResponseStatus]:
    if condition:
        condition = condition.strip()
    else:
        condition = None

    if description:
        description = description.strip()
    else:
        description = None

    if price:
        try:
            price = Decimal(price)
        except ValueError:
            price = None
    else:
        price = None

    if status:
        try:
            status = StoreProductStatus(int(status))
        except ValueError:
            status = None
    else:
        status = None

    if store_product_id:
        try:
            store_product_id = int(store_product_id)

            if store_product_id <= 0:
                store_product_id = None
        except ValueError:
            store_product_id = None
    else:
        store_product_id = None

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

    if not price or \
            not store_product_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not price:
            error_message += ": 'price' must be a floating point value greater than or equal to zero."
        elif not store_product_id:
            error_message += ": 'store_product_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}
        store_product = StoreProduct.get_by_id(store_product_id)

        if store_product:
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
            user_account = UserAccount.get_by_session(session_id)
            store = Store.get_by_id(store_product.store_id)

            if store:
                if store.edit_access_level == EditAccessLevel.OPEN or \
                        (store.edit_access_level == EditAccessLevel.PUBLICLY_ACCESSIBLE and Store.is_manager(user_account.id, store.id)) or \
                        user_account.is_admin:
                    store_product.condition = condition
                    store_product.description = description
                    store_product.price = price
                    store_product.status = status
                    store_product.url = url
                    store_product.update()

                    response = {
                        ProtocolKey.STORE_PRODUCT: store_product.as_dict()
                    }
                else:
                    response_status = ResponseStatus.FORBIDDEN
                    response = {
                        ProtocolKey.ERROR: {
                            ProtocolKey.ERROR_CODE: response_status.value,
                            ProtocolKey.ERROR_MESSAGE: "User account is neither an admin nor a manager of the store listing this product."
                        }
                    }
            else:
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.STORE_NOT_FOUND.value,
                        ProtocolKey.ERROR_MESSAGE: "No store exists for this product's store ID."
                    }
                }
        else:
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.PRODUCT_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No store product exists for this ID."
                }
            }

    return (response, response_status)
