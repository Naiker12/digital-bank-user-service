import boto3
import os
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION")
)

table = dynamodb.Table(os.getenv("USERS_TABLE"))
