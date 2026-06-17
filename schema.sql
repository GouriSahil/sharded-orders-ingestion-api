-- DDL Schema for Shard Database
-- Execute this script on all active shard databases (e.g. shard0, shard1, shard2)

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS orders (
    order_id UUID PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    order_date TIMESTAMPTZ(6) NOT NULL,
    order_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ(6) DEFAULT CURRENT_TIMESTAMP
);

-- Index on customer_id: Critical for fast single-shard lookup queries of a customer's orders
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);

-- Index on order_date: Useful for time-range lookups, ordering, and analytical aggregations
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
