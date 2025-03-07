from datetime import datetime
from flask import request
from typing import Any, TypeVar, Type

from app.config import DatabaseTable, ProtocolKey, ResponseStatus, UserAccountReportType
from app.modules import db
from app.modules.user_account import UserAccount


###########
# CLASSES #
###########


T = TypeVar("T", bound="UserAccountReport")


class UserAccountReport:
    def __init__(self,
                 data: dict) -> None:
        self.comment: str = None
        self.creation_timestamp: datetime = None
        self.id: int = 0
        self.reporter: UserAccount = None
        self.type: UserAccountReportType = None
        self.user_account: UserAccount = None

        if data:
            if ProtocolKey.COMMENT in data and data[ProtocolKey.COMMENT]:
                self.comment: str = data[ProtocolKey.COMMENT]

            if ProtocolKey.CREATION_TIMESTAMP in data and data[ProtocolKey.CREATION_TIMESTAMP]:
                self.creation_timestamp: datetime = data[ProtocolKey.CREATION_TIMESTAMP]

            if ProtocolKey.ID in data and data[ProtocolKey.ID]:
                self.id: int = data[ProtocolKey.ID]

            if ProtocolKey.REPORTER_ID in data and data[ProtocolKey.REPORTER_ID]:
                self.reporter = UserAccount.get_by_id(data[ProtocolKey.REPORTER_ID])

            if ProtocolKey.TYPE in data and data[ProtocolKey.TYPE]:
                self.type: UserAccountReportType = UserAccountReportType(data[ProtocolKey.TYPE])

            if ProtocolKey.USER_ACCOUNT_ID in data and data[ProtocolKey.USER_ACCOUNT_ID]:
                self.user_account = UserAccount.get_by_id(data[ProtocolKey.USER_ACCOUNT_ID])

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
        return "User Account Report " + self.id.__str__()

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.COMMENT: self.comment,
            ProtocolKey.ID: self.id
        }

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        if self.reporter:
            serialized[ProtocolKey.REPORTER_ID] = self.reporter.id

        if self.user_account:
            serialized[ProtocolKey.USER_ACCOUNT_ID] = self.user_account.id

        if self.type:
            serialized[ProtocolKey.TYPE] = self.type.value

        return serialized

    @classmethod
    def create(cls: Type[T],
               comment: str,
               reporter_id: int,
               account_id: int,
               report_type: UserAccountReportType) -> T:
        if not comment:
            raise ValueError("Argument 'comment' must be a non-empty string.")

        if not isinstance(reporter_id, int):
            raise TypeError(f"Argument 'reporter_id' must be of type int, not {type(reporter_id)}.")

        if reporter_id <= 0:
            raise ValueError("Argument 'reporter_id' must be a positive, non-zero integer.")

        if not isinstance(account_id, int):
            raise TypeError(f"Argument 'account_id' must be of type int, not {type(account_id)}.")

        if account_id <= 0:
            raise ValueError("Argument 'account_id' must be a positive, non-zero integer.")

        if not isinstance(report_type, UserAccountReportType):
            raise TypeError(f"Argument 'report_type' must be of type UserAccountReportType, not {type(report_type)}.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.USER_ACCOUNT_REPORT}
                ({ProtocolKey.COMMENT}, {ProtocolKey.REPORTER_ID}, {ProtocolKey.USER_ACCOUNT_ID},
                  {ProtocolKey.TYPE})
                VALUES (%s, %s, %s, %s) RETURNING *;
                """,
                (comment, reporter_id, account_id, report_type.value)
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
        [NOTE] This method erases the report's record from the database.
        """

        if not self.id:
            raise Exception("Deletion requires a report ID.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.USER_ACCOUNT_REPORT}
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
    def get_all_by_user_account(cls: Type[T],
                                account_id: int) -> list[T]:
        if not isinstance(account_id, int):
            raise TypeError(f"Argument 'account_id' must be of type int, not {type(account_id)}.")

        if account_id <= 0:
            raise ValueError("Argument 'account_id' must be a positive, non-zero integer.")

        ret: list[T] = []
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_ACCOUNT_REPORT}
                WHERE {ProtocolKey.USER_ACCOUNT_ID} = %s;
                """,
                (account_id,)
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
                  report_id: int) -> T:
        if not isinstance(report_id, int):
            raise TypeError(f"Argument 'report_id' must be of type int, not {type(report_id)}.")

        if report_id <= 0:
            raise ValueError("Argument 'report_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_ACCOUNT_REPORT}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (report_id,)
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


def report_account(comment: str,
                   account_id: str,
                   report_type: str) -> tuple[dict, ResponseStatus]:
    if account_id:
        try:
            account_id = int(account_id)

            if account_id <= 0:
                account_id = None
        except ValueError:
            account_id = None

    if report_type:
        try:
            report_type = UserAccountReportType(int(report_type))
        except ValueError:
            report_type = None

    if not account_id or \
            not report_type:
        response_status = ResponseStatus.BAD_REQUEST
        error_message = "Invalid or missing parameter"

        if not account_id:
            error_message += ": 'account_id' must be a positive, non-zero integer."
        elif not report_type:
            error_message += ": 'report_type' must be an integer and a valid user account report type."

        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: response_status.value,
                ProtocolKey.ERROR_MESSAGE: error_message
            }
        }
    else:
        response_status = ResponseStatus.OK
        response = {}

        if UserAccount.id_exists(account_id):
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)
            reporter = UserAccount.get_by_session(session_id)

            if reporter.id != account_id:
                report = UserAccountReport.create(comment, reporter.id, account_id, report_type)

                response = report.as_dict()
            else:
                # Invalid ID.
                response_status = ResponseStatus.BAD_REQUEST
                response = {
                    ProtocolKey.ERROR: {
                        ProtocolKey.ERROR_CODE: response_status.value,
                        ProtocolKey.ERROR_MESSAGE: "Invalid account ID."
                    }
                }
        else:
            # Invalid ID.
            response_status = ResponseStatus.NOT_FOUND
            response = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.USER_ACCOUNT_NOT_FOUND.value,
                    ProtocolKey.ERROR_MESSAGE: "No user account exists for this ID."
                }
            }

    return (response, response_status)
