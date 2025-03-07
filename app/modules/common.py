import re

from app.config import Configuration, DatabaseTable, ProtocolKey, \
    ResponseStatus
from app.modules import db


class Common:
    @staticmethod
    def alias_exists(alias: str) -> bool:
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


####################
# MODULE FUNCTIONS #
####################


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

        if Common.alias_valid(alias):
            if not Common.alias_exists(alias):
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
