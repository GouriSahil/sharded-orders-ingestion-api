from google.cloud import storage
import os
from dotenv import load_dotenv

load_dotenv()

def gcs_file_upload(file_path:str , destination_blob_name:str):
   client = storage.Client()
   bucket_name = client.bucket(os.getenv("GCS_BUCKET_NAME"))
   bucket = client.bucket(bucket_name)
   blob = bucket.blob(destination_blob_name)
   blob.upload_from_filename(file_path)
   return f"gs://{bucket_name}/{destination_blob_name}"

if __name__ =="__main__":
    gcs_file_upload("sample_orders.csv", "test_upload.csv")