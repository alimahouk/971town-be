import psycopg2
from psycopg2.extras import RealDictCursor

from app import app
from app.config import Configuration


def connect():
    if app.debug:
        host = "localhost"
        password = ""
    else:
        host = Configuration.AWS_EC2_PROD_DATABASE_HOST
        password = Configuration.AWS_EC2_PROD_PASSWORD

    conn = psycopg2.connect(host=host,
                            database=Configuration.DATABASE_NAME,
                            user=Configuration.DATABASE_USER,
                            password=password,
                            cursor_factory=RealDictCursor)

    return conn
