# Sharded Order Ingestion Backend System

A high-performance, horizontally scalable order ingestion backend built with Python, FastAPI, and PostgreSQL. The system processes high-volume order datasets, backs them up securely to Google Cloud Storage (GCS), validates records in a memory-efficient stream, and distributes them across a sharded database cluster.

---

## 1. System Architecture & Design Decisions

### Streaming File Processing (O(1) Memory Complexity)
- **Problem**: Loading large order files (e.g., 10,000+ records or multi-gigabyte files) entirely into memory can crash backend processes under load.
- **Solution**: The CSV parser processes rows as a stream using a Python generator (`csv.DictReader`). The application maintains a small in-memory buffer of size `batch_size` (default: 500). Once the buffer fills, it flushes the records to the database in a single batch insert before continuing to read. This keeps the memory footprint low and constant, regardless of file size.

### Batch Database Inserts
- **Problem**: Inserting records one-by-one results in high network round-trip overhead and database locks.
- **Solution**: The database module utilizes `psycopg2.extras.execute_values` to perform bulk inserts. Records destined for the same shard are grouped together and committed inside a single transaction per batch, reducing commit overhead and maximizing throughput.

### Connection Pooling
- Each shard database is managed via a dedicated `ThreadedConnectionPool`. This minimizes connection establishment latency and allows the backend to handle concurrent API requests safely across multiple threads.

---

## 2. Database Sharding Strategy

The database layer is horizontally scaled using **Application-Level Sharding** across 3 PostgreSQL shard databases.

### Shard Key Selection: `customer_id`
- **Rationale**: In e-commerce systems, operational and analytical queries are heavily centered around the customer (e.g., fetching order history, calculating loyalty points, calculating customer lifetime value). By sharding on `customer_id`, all orders for a given customer are guaranteed to live on the same physical shard database.
- **Trade-off**:
  - **Pros (Single-Shard Queries)**: Fetching order histories via `GET /orders?customerId=CUST-123` executes a direct lookup on a single shard database. This eliminates cross-shard joins and scatter-gather overhead.
  - **Cons (Scatter-Gather Queries)**: Fetching an individual order by `order_id` without a `customer_id` (e.g., `GET /orders/{order_id}`) requires querying all shards in parallel to locate the record, as the system does not know which shard holds the order.

### Routing Algorithm: MD5 Hash Modulo
To distribute orders deterministically and evenly across shards:
1. Apply an **MD5 cryptographic hash** to the `customer_id` string:
   `Hash = MD5(customer_id)`
2. Convert the MD5 digest to a large integer.
3. Compute the modulo of this integer with the total number of shards (3):
   `Shard Index = Hash Integer % 3`

This ensures a highly uniform distribution of customers across the database cluster and guarantees that a customer's data is always routed to the same database.

---

## 3. Database Schema

The following PostgreSQL DDL schema is applied to each of the three shard databases:

```sql
CREATE TABLE IF NOT EXISTS orders (
    order_id UUID PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    order_date TIMESTAMPTZ(6) NOT NULL,
    order_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ(6) DEFAULT CURRENT_TIMESTAMP
);

-- Indexing for optimized lookups
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
```

### Column Design Choices
- **`order_id` (UUID)**: Enforces global uniqueness across all shards.
- **`order_amount` (NUMERIC(10, 2))**: Avoids floating-point rounding errors typical of `FLOAT` or `DOUBLE PRECISION` types, ensuring financial accuracy. Supports up to 10 total digits, with 2 digits after the decimal point.
- **`customer_id` Index**: Optimized for single-shard queries searching for customer orders.
- **`order_date` Index**: Optimized for chronological filtering and sorting of orders.
- **`created_at` (TIMESTAMPTZ(6))**: Automatically records the timestamp of when the order was stored.

---

## 4. Google Application Default Credentials (ADC)

Authentication with Google Cloud Storage (GCS) uses **Google Application Default Credentials (ADC)**. This configuration guarantees that no static service account keys or sensitive credentials are committed to the codebase.

### Local Development Authentication
To authenticate locally:
1. Install the Google Cloud SDK (for macOS, this can be done via Homebrew: `brew install --cask google-cloud-sdk`).
2. Run the login command in your terminal:
   ```bash
   gcloud auth application-default login
   ```
3. This command generates a local credential JSON file stored securely in your user profile. The `google-cloud-storage` Python library automatically detects this file at runtime via default environment paths.

### Production Environment Authentication
When deploying to GCP (e.g., Google Kubernetes Engine, Cloud Run, or Compute Engine):
- Enable **Workload Identity** (on GKE) or bind a **Service Account** to the runtime resource.
- The GCP metadata server automatically supplies temporary, auto-rotating IAM credentials, which are transparently loaded by ADC.

---

## 5. Environment Variables Configuration

Create a `.env` file in the root of the project.

```env
# Google Cloud Configuration
GCS_BUCKET_NAME=your-gcs-bucket-name
GCS_PROJECT_ID=your-gcp-project-id

# Shard Database Connection Strings (psycopg2 DSN format)
SHARD_0_URL=postgresql://username:password@localhost:5432/shard0
SHARD_1_URL=postgresql://username:password@localhost:5432/shard1
SHARD_2_URL=postgresql://username:password@localhost:5432/shard2
```

---

## 6. Setup & Execution Instructions

### Prerequisites
- **Python**: version `3.12` or higher.
- **uv**: Fast Python package installer and resolver.
- **PostgreSQL**: Three active databases named `shard0`, `shard1`, and `shard2`.

### Step 1: Install Dependencies
Run the following command using `uv` to sync dependencies and initialize the virtual environment:
```bash
uv sync
```

### Step 2: Initialize Database Schemas
Connect to each database shard and execute the DDL queries in the `schema.sql` file.

### Step 3: Run the Application
Start the FastAPI server using `uv`:
```bash
uv run uvicorn main:app --reload --port 8000
```
The server will start, and the interactive API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 7. API Endpoints

### 1. Ingest Orders
* **Endpoint**: `POST /upload-orders`
* **Content-Type**: `multipart/form-data`
* **Request Body**: File parameter `file` (CSV format)
* **Behavior**:
  1. Accepts the uploaded CSV file.
  2. Uploads the raw file to the GCS bucket under `backups/`.
  3. Streams and validates the rows.
  4. Inserts valid records into their mapped database shards.
* **Response**:
  ```json
  {
    "message": "File processed successfully!",
    "gcs_backup_location": "gs://sahil-order-assessment-2026/backups/571cd16a-d71e-4e1c-990a-660842f96102_orders_10000.csv",
    "total_rows_read": 10005,
    "inserted_successfully": 10000,
    "failed_validation": 5
  }
  ```

---

## 8. Verification & Testing Proof

The database shards and Google Cloud Storage configurations have been verified and tested successfully.

### Google Cloud Storage Upload Verification
* **Bucket Name**: `sahil-order-assessment-2026`
* **Google Project ID**: `order-assessment`
* The files are successfully backed up to the bucket inside the `backups/` directory under a unique UUID-prefixed file name (e.g., `backups/571cd16a-d71e-4e1c-990a-660842f96102_orders_10000.csv`).
* Validation of raw integration can also be verified via bucket contents, which successfully houses target records and test logs.

### Database Shard Verification
* Tested and confirmed that client-side MD5 hashing correctly routes records to the corresponding PostgreSQL connection pools representing:
  - `SHARD_0_URL` (`shard0`)
  - `SHARD_1_URL` (`shard1`)
  - `SHARD_2_URL` (`shard2`)

### Test Dataset (`orders_10000.csv`)
* The file `orders_10000.csv` in the root directory contains a dummy dataset of 10,005 rows.
* Out of these, 10,000 are valid orders and 5 are deliberately malformed/invalid order rows (containing invalid statuses or negative amounts) to test gracefulness.
* Running the ingestion pipeline registers:
  - **Total Rows Read**: 10005
  - **Successfully Inserted**: 10000
  - **Failed Validation**: 5 (logged and skipped without failing the entire batch transaction).

