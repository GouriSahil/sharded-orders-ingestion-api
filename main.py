from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
import uuid

from gcs_upload import gcs_file_upload
from process_order import process_csv_file

app = FastAPI()


@app.post("/upload-orders")
async def upload_orders(file: UploadFile = File(...)):
    unique_filename = f"{uuid.uuid4()}_{file.filename}"

    with open(unique_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        gcs_path = gcs_file_upload(unique_filename, f"backups/{unique_filename}")
        summary = process_csv_file(unique_filename)

        return {
            "message": "File processed successfully!",
            "gcs_backup_location": gcs_path,
            "total_rows_read": summary["total_rows_read"],
            "inserted_successfully": summary["total_rows_inserted"],
            "failed_validation": summary["total_rows_failed"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something failed: {str(e)}")

    finally:
        if os.path.exists(unique_filename):
            os.remove(unique_filename)