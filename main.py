import os
from dotenv import load_dotenv
from utils import S3Utils

# Load environment variables
load_dotenv()
ENDPOINT_URL = os.getenv("ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_KEY_ID = os.getenv("S3_SECRET_KEY_ID")

os.environ["AWS_REQUEST_CHECKSUM_CALCULATION"] = "when_required"
os.environ["AWS_RESPONSE_CHECKSUM_VALIDATION"] = "when_required"

s3 = S3Utils(ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_KEY_ID)
# print(s3.object.list_view('tessel', max_depth=4))
# s3.upload_to_s3('test-s3', source_path='./utils')
# print(s3.list_objects_batch('test-s3', prefix='utils/'))
s3.print_objects_tree(bucket_name="tessel")

# s3.delete_objects('test-s3', prefix='utils/')

# s3.object.download_folder(
#     'test-s3', folder_prefix="a/")
# s3.object.list_view('tessel')
