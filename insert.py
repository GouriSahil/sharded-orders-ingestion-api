import psycopg2.extras
from database import release_shard_connection
from database import get_shard_index , get_shard_connection
from collections import  defaultdict

order_data = {
    "order_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "customer_id": "CUST-123",
    "order_date": "2024-05-01T10:00:00",
    "order_amount": 250.75,
    "status": "completed"
}

def insert_batch_order(orders: list[dict]):

    if not orders:
        print("No order provided")
        return
    shard_bucket = defaultdict(list)
    for order in orders:
        shard_index = get_shard_index(order["customer_id"])
        order_tuple = (
            order["order_id"],
            order["customer_id"],
            order["order_date"],
            order["order_amount"],
            order["status"]
        )
        shard_bucket[shard_index].append(order_tuple)
    for shard_index, records in shard_bucket.items():
        if not records:
            continue
        connection = get_shard_connection(shard_index)
        cursor = None
        try:
            cursor = connection.cursor()
            query = """
                            INSERT INTO orders (order_id, customer_id, order_date, order_amount, status) 
                            VALUES %s
                            ON CONFLICT (order_id) DO NOTHING
                        """
            psycopg2.extras.execute_values(cursor, query, records)
            connection.commit()
            print(f"Batch written successfully: {len(records)} orders to Shard {shard_index}.")

        except Exception as error:
            connection.rollback()
            print(f" Batch insertion failed on Shard {shard_index}: {error}")
            raise error

        finally:
            if cursor:
                cursor.close()
            release_shard_connection(shard_index, connection)

def insert_order(order_data : dict):
    shard_index = get_shard_index(order_data["customer_id"])
    connection = get_shard_connection(shard_index)
    cursor = None

    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO orders (order_id , customer_id , order_date , order_amount , status) 
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(query, (
            order_data["order_id"],
            order_data["customer_id"],
            order_data["order_date"],
            order_data["order_amount"],
            order_data["status"]
        ))
        connection.commit()
        print(f" Order {order_data['order_id']} committed successfully to Shard {shard_index}.")

    except Exception as error:
        connection.rollback()
        print(f" Error inserting order into Shard {shard_index}: {error}")
        raise error

    finally:
        if cursor:
            cursor.close()
        release_shard_connection(shard_index, connection)

if __name__ == "__main__":
    test_orders = [
        {"order_id": "11111111-1111-1111-1111-111111111111", "customer_id": "CUST-123",
         "order_date": "2024-05-01T10:00:00", "order_amount": 100.00, "status": "pending"},
        {"order_id": "22222222-2222-2222-2222-222222222222", "customer_id": "CUST-456",
         "order_date": "2024-05-02T10:00:00", "order_amount": 200.00, "status": "completed"},
        {"order_id": "33333333-3333-3333-3333-333333333333", "customer_id": "CUST-789",
         "order_date": "2024-05-03T10:00:00", "order_amount": 300.00, "status": "completed"},
    ]
    insert_batch_order(test_orders)