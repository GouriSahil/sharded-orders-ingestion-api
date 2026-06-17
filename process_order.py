from datetime import datetime


def validate_row(row: dict) -> tuple[bool, str | None]:
    order_id = row.get("order_id", "").strip()
    if not order_id:
        return False, "Missing or empty order_id"


    customer_id = row.get("customer_id", "").strip()
    if not customer_id:
        return False, "Missing or empty customer_id"


    order_date_raw = row.get("order_date", "").strip()
    try:

        datetime.fromisoformat(order_date_raw)
    except (ValueError, TypeError):
        return False, f"Invalid or poorly formatted order_date: '{order_date_raw}'"


    order_amount_raw = row.get("order_amount", "").strip()
    try:
        amount = float(order_amount_raw)
        if amount < 0:
            return False, f"Negative order_amount not allowed: {amount}"
    except (ValueError, TypeError):
        return False, f"Invalid numeric order_amount: '{order_amount_raw}'"

    status = row.get("status", "").strip().lower()
    valid_statuses = {"pending", "completed", "cancelled"}
    if status not in valid_statuses:
        return False, f"Invalid status '{status}'. Must be one of {valid_statuses}"

    return True, None

if __name__ == "__main__":
    test_rows = [
        {"order_id": "1", "customer_id": "CUST-1", "order_date": "2024-05-01T10:00:00", "order_amount": "100.50", "status": "completed"},
        {"order_id": "", "customer_id": "CUST-1", "order_date": "2024-05-01T10:00:00", "order_amount": "100", "status": "completed"},
        {"order_id": "2", "customer_id": "CUST-1", "order_date": "not-a-date", "order_amount": "100", "status": "completed"},
        {"order_id": "3", "customer_id": "CUST-1", "order_date": "2024-05-01T10:00:00", "order_amount": "abc", "status": "completed"},
        {"order_id": "4", "customer_id": "CUST-1", "order_date": "2024-05-01T10:00:00", "order_amount": "-5", "status": "completed"},
        {"order_id": "5", "customer_id": "CUST-1", "order_date": "2024-05-01T10:00:00", "order_amount": "50", "status": "weird_status"},
    ]
    for r in test_rows:
        print(validate_row(r))