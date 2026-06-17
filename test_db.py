from database import get_shard_index, get_shard_connection, release_shard_connection

# Test 1: shard index logic
print("Shard for CUST-123:", get_shard_index("CUST-123"))
print("Shard for CUST-123 again (should match):", get_shard_index("CUST-123"))
print("Shard for CUST-456:", get_shard_index("CUST-456"))

# Test 2: actual database connection
shard_index = 0
conn = get_shard_connection(shard_index)
cursor = conn.cursor()
cursor.execute("SELECT 1;")
result = cursor.fetchone()
print(f"Connection to shard {shard_index} works, result:", result)

cursor.close()
release_shard_connection(shard_index, conn)
print("Connection released back to pool successfully.")