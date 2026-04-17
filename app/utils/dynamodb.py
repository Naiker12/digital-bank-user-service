import boto3
import os

dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

# No load_dotenv() - environment variables must be provided by the runtime
table = dynamodb.Table(os.getenv("USERS_TABLE", "bank-users"))
