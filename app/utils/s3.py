import boto3
import os

s3 = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

# No load_dotenv()
BUCKET = os.getenv("S3_BUCKET")
