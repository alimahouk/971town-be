from datetime import datetime
from dateutil import parser as date_parser
from flask import request
import re
from typing import Any, TypeVar, Type

from app.config import Configuration, DatabaseTable, EntityType, \
    ProtocolKey, ResponseStatus
from app.modules import db
from app.modules.user_account_session import UserAccountSession


###########
# CLASSES #
###########


T = TypeVar("T", bound="UserAccount")


class UserAccount:
    def __init__(self,
                 data: dict) -> None:
        self.alias: str = None
        self.bio: str = None
        self.creation_timestamp: datetime = None
        self.id: int = 0
        self.is_admin: bool = False
        self.rep: int = 0
        self.sessions: list[UserAccountSession] = []
        self.user_id: int = 0
        self.website: str = None

        if data:
            if ProtocolKey.ALIAS in data and data[ProtocolKey.ALIAS]:
                self.alias: str = data[ProtocolKey.ALIAS]

            if ProtocolKey.BIO in data and data[ProtocolKey.BIO]:
                self.bio: str = data[ProtocolKey.BIO]

            if ProtocolKey.CREATION_TIMESTAMP in data and data[ProtocolKey.CREATION_TIMESTAMP]:
                creation_timestamp = data[ProtocolKey.CREATION_TIMESTAMP]

                if isinstance(creation_timestamp, datetime):
                    self.creation_timestamp: datetime = creation_timestamp
                elif isinstance(creation_timestamp, str):
                    self.creation_timestamp: datetime = date_parser.parse(creation_timestamp)

            if ProtocolKey.ID in data and data[ProtocolKey.ID]:
                self.id: int = data[ProtocolKey.ID]
                self.is_admin = UserAccount.is_admin(self.id)
                self.sessions = UserAccountSession.get_all_for_account(self.id)

            if ProtocolKey.REP in data and data[ProtocolKey.REP]:
                self.rep: int = data[ProtocolKey.REP]

            if ProtocolKey.USER_ID in data and data[ProtocolKey.USER_ID]:
                self.user_id: int = data[ProtocolKey.USER_ID]

            if ProtocolKey.WEBSITE in data and data[ProtocolKey.WEBSITE]:
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
        ret = ""

        if self.id:
            ret += "User Account " + self.id.__str__()

        return ret

    @staticmethod
    def alias_exists(alias: str) -> bool:
        """
        Compares against aliases in the user accounts table.
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
                SELECT * FROM {DatabaseTable.USER_ACCOUNT}
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
            # REGEX EXPLANATION:
            #
            # ^(?=.{8,20}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._-]+(?<![_.])$
            # └─────┬─────┘└───┬──┘└─────┬─────┘└──────┬─────┘ └───┬───┘
            #       │          │         │             │           no _ or . at the end
            #       │          │         │             │
            #       │          │         │             allowed characters
            #       │          │         │
            #       │          │         no __ or _. or ._ or .. inside
            #       │          │
            #       │          no _ or . at the beginning
            #       │
            #       username is 8-20 characters long

            pattern = re.compile(
                f"^(?=.{{{Configuration.ALIAS_MIN_LEN},{Configuration.ALIAS_MAX_LEN}}}$)(?![_.])[a-zA-Z0-9._-]+(?<![_.])$")
            ret = pattern.match(alias)

        return ret

    def as_dict(self,
                is_public=True) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.ALIAS: self.alias,
            ProtocolKey.BIO: self.bio,
            ProtocolKey.ID: self.id,
            ProtocolKey.IS_ADMIN: self.is_admin,
            ProtocolKey.REP: self.rep,
            ProtocolKey.USER_ID: self.user_id,
            ProtocolKey.WEBSITE: self.website
        }

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        if not is_public and self.sessions:
            sessions_serialized = []

            for session in self.sessions:
                sessions_serialized.append(session.as_dict())

            serialized[ProtocolKey.SESSIONS] = sessions_serialized

        return serialized

    @classmethod
    def create(cls: Type[T],
               alias: str,
               user_id: int) -> T:
        if not isinstance(alias, str):
            raise TypeError(f"Argument 'alias' must be of type str, not {type(alias)}.")

        if not alias:
            raise ValueError("Argument 'alias' must be a non-empty string.")

        if not isinstance(user_id, int):
            raise TypeError(f"Argument 'user_id' must be of type int, not {type(user_id)}.")

        if user_id <= 0:
            raise ValueError("Argument 'user_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None
        alias = alias.lower()

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.USER_ACCOUNT}
                ({ProtocolKey.ALIAS}, {ProtocolKey.USER_ID})
                VALUES (%s, %s) RETURNING *;
                """,
                (alias, user_id)
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
                    (ret.id, alias, EntityType.USER_ACCOUNT)
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

    def create_admin(self,
                     account_id: int) -> None:
        if not isinstance(account_id, int):
            raise TypeError(f"Argument 'account_id' must be of type int, not {type(account_id)}.")

        if account_id <= 0:
            raise ValueError("Argument 'account_id' must be a positive, non-zero integer.")

        if not self.id:
            raise Exception("User account has no ID associated with it.")

        if not UserAccount.is_admin(self.id):
            conn = None
            cursor = None

            try:
                conn = db.connect()
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    INSERT INTO {DatabaseTable.ADMIN_USER_ACCOUNT}
                    ({ProtocolKey.USER_ACCOUNT_ID})
                    VALUES (%s);
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

    def delete(self) -> None:
        """
        [NOTE] This method erases the user account's record from the database.
        """

        if not self.id and not self.alias:
            raise Exception("Deletion requires either a user account ID or alias.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()

            if self.id:
                cursor.execute(
                    f"""
                    DELETE FROM {DatabaseTable.USER_ACCOUNT}
                    WHERE {ProtocolKey.ID} = %s;
                    """,
                    (self.id,)
                )
            else:
                cursor.execute(
                    f"""
                    DELETE FROM {DatabaseTable.USER_ACCOUNT}
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

    @staticmethod
    def get_account_id_for_alias(alias: str) -> int:
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
                SELECT * FROM {DatabaseTable.USER_ACCOUNT}
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
                SELECT *, ts_rank(match.{ProtocolKey.POSTGRES_SEARCH_ALIAS}, plainto_tsquery('english', %s)) AS rank FROM
                (SELECT * FROM {DatabaseTable.USER_ACCOUNT}
                WHERE {ProtocolKey.POSTGRES_SEARCH_ALIAS} @@ plainto_tsquery('english', %s))
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
                SELECT * FROM {DatabaseTable.USER_ACCOUNT}
                WHERE {ProtocolKey.USER_ID} = %s;
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
                SELECT * FROM {DatabaseTable.USER_ACCOUNT}
                WHERE {ProtocolKey.ALIAS} = %s;
                """,
                (alias,)
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
    def get_by_id(cls: Type[T],
                  account_id: int) -> T:
        if not isinstance(account_id, int):
            raise TypeError(f"Argument 'account_id' must be of type int, not {type(account_id)}.")

        if account_id <= 0:
            raise ValueError("Argument 'account_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_ACCOUNT}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (account_id,)
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
    def get_by_session(cls: Type[T],
                       session_id: int) -> T:
        if not isinstance(session_id, str):
            raise TypeError(f"Argument 'session_id' must be of type str, not {type(session_id)}.")

        if not session_id:
            raise ValueError("Argument 'session_id' must be a non-empty string.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_ACCOUNT_SESSION}
                LEFT JOIN {DatabaseTable.USER_ACCOUNT} ON {DatabaseTable.USER_ACCOUNT_SESSION}.{ProtocolKey.USER_ACCOUNT_ID} = {DatabaseTable.USER_ACCOUNT}.{ProtocolKey.ID}
                WHERE {DatabaseTable.USER_ACCOUNT_SESSION}.{ProtocolKey.ID} = %s;
                """,
                (session_id,)
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
    def get_count(cls: Type[T],
                  user_id: int) -> int:
        if not isinstance(user_id, int):
            raise TypeError(f"Argument 'user_id' must be of type int, not {type(user_id)}.")

        if user_id <= 0:
            raise ValueError("Argument 'user_id' must be a positive, non-zero integer.")

        ret: int = 0
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM {DatabaseTable.USER_ACCOUNT}
                WHERE {ProtocolKey.USER_ID} = %s;
                """,
                (user_id,)
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
    def id_exists(account_id: int) -> bool:
        if not isinstance(account_id, int):
            raise TypeError(f"Argument 'account_id' must be of type int, not {type(account_id)}.")

        if account_id <= 0:
            raise ValueError("Argument 'account_id' must be a positive, non-zero integer.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_ACCOUNT}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (account_id,)
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
    def is_admin(account_id: int) -> bool:
        if not isinstance(account_id, int):
            raise TypeError(f"Argument 'account_id' must be of type int, not {type(account_id)}.")

        if account_id <= 0:
            raise ValueError("Argument 'account_id' must be a positive, non-zero integer.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.ADMIN_USER_ACCOUNT}
                WHERE {ProtocolKey.USER_ACCOUNT_ID} = %s;
                """,
                (account_id,)
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
        """
        This method does not update sessions or admin status.
        Those properties need to be updated separately by their
        respective classes.
        """

        if not self.id and not self.alias:
            raise Exception("Updating requires either a user account ID or a user account alias.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()

            if self.id:
                cursor.execute(
                    f"""
                    UPDATE {DatabaseTable.USER_ACCOUNT}
                    SET {ProtocolKey.BIO} = %s, {ProtocolKey.REP} = %s,
                    {ProtocolKey.WEBSITE} = %s
                    WHERE {ProtocolKey.ID} = %s;
                    """,
                    (self.bio, self.rep, self.website, self.id)
                )
            else:
                cursor.execute(
                    f"""
                    UPDATE {DatabaseTable.USER_ACCOUNT}
                    SET {ProtocolKey.BIO} = %s, {ProtocolKey.REP} = %s,
                    {ProtocolKey.WEBSITE} = %s
                    WHERE {ProtocolKey.ALIAS} = %s;
                    """,
                    (self.bio, self.rep, self.website, self.alias)
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


def delete_account(account_id: str) -> tuple[dict, ResponseStatus]:
    if account_id:
        try:
            account_id = int(account_id)

            if account_id <= 0:
                account_id = None
        except ValueError:
            account_id = None

    if not account_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'account_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}
        user_account = UserAccount.get_by_id(account_id)

        if user_account:
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
            user_account = UserAccount.get_by_session(session_id)

            if user_account.is_admin:
                user_account.delete()

                response = {
                    ProtocolKey.USER_ACCOUNT_ID: user_account.id
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
                    ProtocolKey.ERROR_CODE: ResponseStatus.USER_ACCOUNT_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No user account exists for this ID."
                }
            }

    return (response, response_status)


def get_account(alias: str = None,
                account_id: str = None) -> tuple[dict, ResponseStatus]:
    if account_id:
        try:
            account_id = int(account_id)

            if account_id <= 0:
                account_id = None
        except ValueError:
            account_id = None

    if not alias and \
            not account_id:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter: 'alias' must be a non-empty string or 'account_id' must be a positive, non-zero integer."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}

        if account_id:
            user_account = UserAccount.get_by_id(account_id)
        else:
            if UserAccount.alias_valid(alias):
                user_account = UserAccount.get_by_alias(alias)
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
            if user_account:
                response = {
                    ProtocolKey.USER_ACCOUNT: user_account.as_dict()
                }
            else:
                response_status = ResponseStatus.NOT_FOUND
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: ResponseStatus.USER_ACCOUNT_NOT_FOUND.value,
                        ProtocolKey.ERROR_MESSAGE: "No user account exists for this ID."
                    }
                }

    return (response, response_status)


def get_accounts(query: str) -> tuple[dict, ResponseStatus]:
    query = query.strip()
    response_status = ResponseStatus.OK
    serialized = []

    if query:
        results = UserAccount.get_all(query)

        for result in results:
            serialized.append(result.as_dict())

    response = {
        ProtocolKey.USER_ACCOUNTS: serialized
    }

    return (response, response_status)


def get_current_account() -> tuple[dict, ResponseStatus]:
    session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)

    if session_id:
        current_account = UserAccount.get_by_session(session_id)

        if current_account:
            response_status = ResponseStatus.OK
            response = {
                ProtocolKey.USER_ACCOUNT: current_account.as_dict(is_public=False)
            }
        else:
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.USER_ACCOUNT_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No user account exists for this ID."
                }
            }
    else:
        response_status = ResponseStatus.BAD_REQUEST
        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: "Invalid session."
            }
        }

    return (response, response_status)
