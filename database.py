import  os
from dotenv import load_dotenv
from psycopg2 import pool
import hashlib

SHARD_COUNT = 3


load_dotenv()
SHARD_URLS={
    0:os.getenv("SHARD_0_URL"),
    1:os.getenv("SHARD_1_URL"),
    2:os.getenv("SHARD_2_URL")
}

SHARD_POOL = {
    0:pool.ThreadedConnectionPool(minconn=1, maxconn=10, dsn=SHARD_URLS[0]),
    1:pool.ThreadedConnectionPool(minconn=1 , maxconn=10 , dsn=SHARD_URLS[1]),
    2:pool.ThreadedConnectionPool(minconn=1 , maxconn=10 , dsn=SHARD_URLS[2])
}

def get_shard_index(customer_id: str) -> int:
    hash_bytes = hashlib.md5(customer_id.encode('utf-8')).digest()
    hash_integer = int.from_bytes(hash_bytes, byteorder='big')
    return hash_integer % SHARD_COUNT

def get_shard_connection(shard_index : int):
    connection = SHARD_POOL[shard_index].getconn()
    return connection

def release_shard_connection(shard_index:int, connection):
    SHARD_POOL[shard_index].putconn(connection)
