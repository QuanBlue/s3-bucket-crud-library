import os
from dotenv import load_dotenv
from s3_library import S3Utils


# Load environment variables
load_dotenv()
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_KEY_ID = os.getenv("S3_SECRET_KEY_ID")

os.environ["AWS_REQUEST_CHECKSUM_CALCULATION"] = "when_required"
os.environ["AWS_RESPONSE_CHECKSUM_VALIDATION"] = "when_required"

s3 = S3Utils(S3_ACCESS_KEY_ID, S3_SECRET_KEY_ID, S3_ENDPOINT_URL)

# [ Your code here ... ]