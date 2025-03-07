from datetime import datetime
from flask import request
from geoip import open_database
import hashlib
import ipaddress
import os
import re
import sys
from typing import Any, TypeVar, Type
from ua_parser import user_agent_parser
import uuid

from app import app
from app.config import ClientDeviceType, DatabaseTable, ProtocolKey, ResponseStatus
from app.modules import db
from app.modules.user_client import UserClient
from app.modules.user_os import UserOS


###########
# CLASSES #
###########


T = TypeVar("T", bound="UserAccountSession")


class UserAccountSession:
    def __init__(self,
                 data: dict) -> None:
        self.client: UserClient = None
        self.device_name: str = None
        self.device_type: ClientDeviceType = ClientDeviceType.UNDEFINED
        self.creation_timestamp: datetime = None
        self.id: str = None
        self.ip_address: ipaddress = None
        self.last_activity: datetime = None
        self.location: str = None
        self.mac_address: str = None
        self.mobile_carrier: str = None
        self.os: UserOS = None
        self.screen_resolution: str = None
        self.time_zone: str = None
        self.user_account_id: int = 0

        if data:
            if ProtocolKey.CLIENT_ID in data and data[ProtocolKey.CLIENT_ID]:
                self.client = UserClient.get_by_id(data[ProtocolKey.CLIENT_ID])

                if self.client and ProtocolKey.CLIENT_VERSION in data:
                    self.client.version: str = data[ProtocolKey.CLIENT_VERSION]

            if ProtocolKey.DEVICE_NAME in data:
                self.device_name: str = data[ProtocolKey.DEVICE_NAME]

            if ProtocolKey.DEVICE_TYPE in data and data[ProtocolKey.DEVICE_TYPE]:
                self.device_type = ClientDeviceType(data[ProtocolKey.DEVICE_TYPE])

            if ProtocolKey.CREATION_TIMESTAMP in data:
                self.creation_timestamp: datetime = data[ProtocolKey.CREATION_TIMESTAMP]

            if ProtocolKey.ID in data:
                self.id: str = data[ProtocolKey.ID]

            if ProtocolKey.IP_ADDRESS in data:
                self.ip_address: ipaddress = data[ProtocolKey.IP_ADDRESS]

            if ProtocolKey.LAST_ACTIVITY in data:
                self.last_activity: datetime = data[ProtocolKey.LAST_ACTIVITY]

            if ProtocolKey.LOCATION in data:
                self.location: str = data[ProtocolKey.LOCATION]

            if ProtocolKey.MAC_ADDRESS in data:
                self.mac_address: str = data[ProtocolKey.MAC_ADDRESS]

            if ProtocolKey.MOBILE_CARRIER in data:
                self.mobile_carrier: str = data[ProtocolKey.MOBILE_CARRIER]

            if ProtocolKey.OS_ID in data and data[ProtocolKey.OS_ID]:
                self.os = UserOS.get_by_id(data[ProtocolKey.OS_ID])

                if ProtocolKey.OS_VERSION in data:
                    self.os.version: str = data[ProtocolKey.OS_VERSION]

            if ProtocolKey.SCREEN_RESOLUTION in data:
                self.screen_resolution: str = data[ProtocolKey.SCREEN_RESOLUTION]

            if ProtocolKey.TIME_ZONE in data:
                self.time_zone: str = data[ProtocolKey.TIME_ZONE]

            if ProtocolKey.USER_ACCOUNT_ID in data:
                self.user_account_id: int = data[ProtocolKey.USER_ACCOUNT_ID]

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
            ret += f"User Account {self.user_account_id} Session {self.id}"

        return ret

    def as_dict(self) -> dict[ProtocolKey, Any]:
        serialized = {
            ProtocolKey.DEVICE_NAME: self.device_name,
            ProtocolKey.ID: self.id,
            ProtocolKey.LOCATION: self.location,
            ProtocolKey.TIME_ZONE: self.time_zone,
            ProtocolKey.USER_ACCOUNT_ID: self.user_account_id
        }

        if self.client:
            serialized[ProtocolKey.CLIENT] = self.client.as_dict()

        if self.device_type:
            serialized[ProtocolKey.DEVICE_TYPE] = self.device_type.value

        if self.creation_timestamp:
            serialized[ProtocolKey.CREATION_TIMESTAMP] = self.creation_timestamp.astimezone().isoformat()

        if self.ip_address:
            serialized[ProtocolKey.IP_ADDRESS] = str(self.ip_address)

        if self.last_activity:
            serialized[ProtocolKey.LAST_ACTIVITY] = self.last_activity.astimezone().isoformat()

        if self.os:
            serialized[ProtocolKey.OS] = self.os.as_dict()

        return serialized

    @classmethod
    def create(cls: Type[T],
               client_id: str,
               user_account_id: int) -> T:
        """
        Call this method to create a session object then populate its
        fields and call its update() method.
        """

        if not isinstance(client_id, str):
            raise TypeError(f"Argument 'client_id' must be of type str, not {type(client_id)}.")

        if not client_id:
            raise ValueError("Argument 'client_id' must be a non-empty string.")

        if not isinstance(user_account_id, int):
            raise TypeError(f"Argument 'user_account_id' must be of type int, not {type(user_account_id)}.")

        if user_account_id <= 0:
            raise ValueError("Argument 'user_account_id' must be a positive, non-zero integer.")

        ret: Type[T] = None
        conn = None
        cursor = None

        try:
            session_id = cls.generate_id()

            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {DatabaseTable.USER_ACCOUNT_SESSION}
                ({ProtocolKey.ID}, {ProtocolKey.USER_ACCOUNT_ID}, {ProtocolKey.CLIENT_ID})
                VALUES (%s, %s, %s) RETURNING *;
                """,
                (session_id, user_account_id, client_id)
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
            raise Exception("Deletion requires a session ID.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.USER_ACCOUNT_SESSION}
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
    def delete_all_for_account(user_account_id: int) -> None:
        if not isinstance(user_account_id, int):
            raise TypeError(f"Argument 'user_account_id' must be of type int, not {type(user_account_id)}.")

        if user_account_id <= 0:
            raise ValueError("Argument 'user_account_id' must be a positive, non-zero integer.")

        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {DatabaseTable.USER_ACCOUNT_SESSION}
                WHERE {ProtocolKey.USER_ACCOUNT_ID} = %s;
                """,
                (user_account_id,)
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
    def get_all_for_account(cls: Type[T],
                            user_account_id: int) -> list[T]:
        if not isinstance(user_account_id, int):
            raise TypeError(f"Argument 'user_account_id' must be of type int, not {type(user_account_id)}")

        if user_account_id <= 0:
            raise ValueError("Argument 'user_account_id' must be a positive, non-zero integer.")

        ret = []

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_ACCOUNT_SESSION}
                WHERE {ProtocolKey.USER_ACCOUNT_ID} = %s;
                """,
                (user_account_id,)
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
                  session_id: str) -> T:
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
                WHERE {ProtocolKey.ID} = %s;
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

    @staticmethod
    def generate_id() -> str:
        """
        Generates a session ID.
        """
        
        rand = uuid.uuid4().hex

        return hashlib.sha256(rand.encode("utf-8")).hexdigest()

    @staticmethod
    def session_exists(session_id: str) -> bool:
        if not isinstance(session_id, str):
            raise TypeError(f"Argument 'session_id' must be of type str, not {type(session_id)}.")

        if not session_id:
            raise ValueError("Argument 'session_id' must be a non-empty string.")

        ret = False
        conn = None
        cursor = None

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {DatabaseTable.USER_ACCOUNT_SESSION}
                WHERE {ProtocolKey.ID} = %s;
                """,
                (session_id,)
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
        if not self.id or not self.user_account_id:
            raise Exception("Updating requires a session ID and user account ID.")

        conn = None
        cursor = None

        try:
            client_id = None
            client_version = None
            ip_address = str(self.ip_address)
            os_id = None
            os_version = None

            if self.client:
                client_id = self.client.id
                client_version = self.client.version

            if self.os:
                os_id = self.os.id
                os_version = self.os.version

            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {DatabaseTable.USER_ACCOUNT_SESSION}
                SET {ProtocolKey.LAST_ACTIVITY} = %s, {ProtocolKey.IP_ADDRESS} = %s, {ProtocolKey.MAC_ADDRESS} = %s,
                  {ProtocolKey.DEVICE_TYPE} = %s, {ProtocolKey.DEVICE_NAME} = %s, {ProtocolKey.CLIENT_ID} = %s,
                  {ProtocolKey.CLIENT_VERSION} = %s, {ProtocolKey.MOBILE_CARRIER} = %s, {ProtocolKey.LOCATION} = %s,
                  {ProtocolKey.TIME_ZONE} = %s, {ProtocolKey.SCREEN_RESOLUTION} = %s, {ProtocolKey.OS_ID} = %s,
                  {ProtocolKey.OS_VERSION} = %s
                WHERE {ProtocolKey.ID} = %s AND {ProtocolKey.USER_ACCOUNT_ID} = %s;
                """,
                (self.last_activity, ip_address, self.mac_address,
                 self.device_type.value, self.device_name, client_id,
                 client_version, self.mobile_carrier, self.location,
                 self.time_zone, self.screen_resolution, os_id,
                 os_version, self.id, self.user_account_id)
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

def create_session(client_id: str,
                   user_account_id: int) -> UserAccountSession:
    if not isinstance(client_id, str):
        raise TypeError(f"Argument 'client_id' must be of type str, not {type(client_id)}")

    if not client_id:
        raise ValueError("Argument 'client_id' must be a non-empty string")

    if not isinstance(user_account_id, int):
        raise TypeError(f"Argument 'user_account_id' must be of type int, not {type(user_account_id)}")

    if user_account_id <= 0:
        raise ValueError("Argument 'user_account_id' must be a positive, non-zero integer.")

    if UserClient.id_exists(client_id):
        new_session = UserAccountSession.create(client_id, user_account_id)
    else:
        new_session = None

    return new_session


def determine_location(ip_address: str) -> str:
    if not isinstance(ip_address, str):
        raise TypeError(f"Argument 'ip_address' must be of type str, not {type(ip_address)}")

    if not ip_address:
        raise ValueError("Argument 'ip_address' must be a non-empty string")

    ret: str = None
    geoip_db_path = os.path.join(app.root_path, "db", "GeoLite2-Country.mmdb")

    with open_database(geoip_db_path) as db:
        match = db.lookup(ip_address)

        if match:
            ret = match.country

    return ret


def determine_mac_address(ip_address: str) -> str:
    """
    Get MAC address for a given IP address by looking it up in the host's ARP table

    :param ip: IP address to look up
    :type ip: str
    :return: MAC address
    :rtype: str
    """

    ret: str = None
    arp_table = get_arp_table()

    if ip_address in arp_table:
        ret = arp_table[ip_address]

    return ret


def get_arp_table_darwin() -> dict[str, str]:
    """
    Parse the host's ARP table on a macOS machine.

    :return: Machine readable ARP table (by running the "arp -a -n" command)
    :rtype: dict {'ip_address': 'mac_address'}
    """

    ret: dict[str, str] = {}
    devices = os.popen("arp -an")

    for device in devices:
        # Example output: xxxx (192.168.1.254) at xx:xx:xx:xx:xx:xx [ether] on wlp
        _, ip_address, _, phyical_address, _ = device.split(maxsplit=4)
        # Remove the paranthesis around the IP address.
        ip_address = ip_address.strip("()")
        ret[ip_address] = phyical_address

    return ret


def get_arp_table_linux() -> dict[str, str]:
    """
    Parse the host's ARP table on a Linux machine.

    :return: Machine readable ARP table (see the Linux Kernel documentation on /proc/net/arp for more information)
    :rtype: dict {'ip_address': 'mac_address'}
    """

    with open("/proc/net/arp") as proc_net_arp:
        arp_data_raw = proc_net_arp.read(-1).split("\n")[1:-1]

    parsed_arp_table = (dict(zip(("ip_address", "type", "flags", "hw_address", "mask", "device"), v))
                        for v in (re.split("\s+", i) for i in arp_data_raw))

    return {d["ip_address"]: d["hw_address"] for d in parsed_arp_table}


def get_arp_table() -> dict[str, str]:
    """
    Parse the host's ARP table.

    :return: Machine readable ARP table (see the Linux Kernel documentation on /proc/net/arp for more information)
    :rtype: dict {'ip_address': 'mac_address'}
    """

    ret: dict[str, str] = {}

    if sys.platform in ("linux", "linux2"):
        ret = get_arp_table_linux()
    elif sys.platform == "darwin":
        ret = get_arp_table_darwin()

    return ret


def update_session() -> tuple[dict, ResponseStatus]:
    """
    Gather details about the current session and update
    them in the database.
    """

    session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)

    if session_id:
        session = UserAccountSession.get_by_id(session_id)
        user_agent = user_agent_parser.Parse(request.user_agent.string)

        if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
            ip_address = request.environ["REMOTE_ADDR"]
        else:
            ip_address = request.remote_addr

        session.device_name = request.form.get(ProtocolKey.DEVICE_NAME)
        session.ip_address = ipaddress.ip_address(ip_address)
        session.last_activity = datetime.utcnow()
        session.location = determine_location(ip_address)
        session.mac_address = determine_mac_address(ip_address)
        session.mobile_carrier = request.form.get(ProtocolKey.MOBILE_CARRIER)

        # client_name = user_agent["user_agent"]["family"]
        client_version = ".".join(
            part
            for key in ("major", "minor", "patch")
            if (part := user_agent["user_agent"][key]) is not None
        )

        if client_version and session.client:
            session.client.version = client_version

        os_name = user_agent["os"]["family"]
        os_version = ".".join(
            part
            for key in ("major", "minor", "patch")
            if (part := user_agent["os"][key]) is not None
        )

        if not session.os:
            session.os = UserOS.get_by_name(os_name)

            if not session.os:
                session.os = UserOS.create(os_name)

            if os_version:
                session.os.version = os_version

        session.update()

        response_status = ResponseStatus.OK
        response = {
            ProtocolKey.USER_ACCOUNT_ID: session.user_account_id
        }
    else:
        response_status = ResponseStatus.UNAUTHORIZED
        response = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: ResponseStatus.SESSION_INVALID.value,
                ProtocolKey.ERROR_MESSAGE: "Invalid session."
            }
        }

    return (response, response_status)
