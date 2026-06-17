from datetime import datetime
import csv
from insert import insert_batch_order


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


def process_csv_file(file_path: str, batch_size: int = 500) -> dict:
    valid_buffer = []
    failed_rows = []
    total_read = 0
    total_inserted = 0

    with open(file_path, mode="r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            total_read += 1
            is_valid, reason = validate_row(row)

            if is_valid:
                valid_buffer.append(row)
            else:
                failed_rows.append({"row": row, "reason": reason})

            if len(valid_buffer) == batch_size:
                try:
                    insert_batch_order(valid_buffer)
                    total_inserted += len(valid_buffer)
                except Exception as e:
                    failed_rows.append({"row": "BATCH_FAILURE", "reason": str(e)})
                valid_buffer.clear()

        if valid_buffer:
            try:
                insert_batch_order(valid_buffer)
                total_inserted += len(valid_buffer)
            except Exception as e:
                failed_rows.append({"row": "BATCH_FAILURE", "reason": str(e)})
            valid_buffer.clear()

    summary = {
        "total_rows_read": total_read,
        "total_rows_inserted": total_inserted,
        "total_rows_failed": len(failed_rows),
        "failures": failed_rows
    }

    print("\nProcessing Summary")
    print(f"Total Rows Read:       {summary['total_rows_read']}")
    print(f"Successfully Inserted: {summary['total_rows_inserted']}")
    print(f"Failed Validation:     {summary['total_rows_failed']}")

    return summary


if __name__ == "__main__":
    result = process_csv_file("sample_orders.csv", batch_size=2)