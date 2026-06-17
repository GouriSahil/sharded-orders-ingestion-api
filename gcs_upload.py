from google.cloud import storage
import os
from dotenv import load_dotenv

load_dotenv()
def gcs_file_upload(file_path: str, destination_blob_name: str):
    bucket_name = os.getenv("GCS_BUCKET_NAME")  # this is the STRING name from .env
    client = storage.Client()
    bucket = client.bucket(bucket_name)          # call ONCE, with the string
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    return f"gs://{bucket_name}/{destination_blob_name}"

if __name__ == "__main__":
    result = gcs_file_upload("sample_orders.csv", "test_upload.csv")
    print(f" Uploaded successfully: {result}")