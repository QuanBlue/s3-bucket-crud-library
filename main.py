import os
from dotenv import load_dotenv
from utils import S3Utils

# Load environment variables
load_dotenv()
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_KEY_ID = os.getenv("S3_SECRET_KEY_ID")

s3 = S3Utils(S3_ACCESS_KEY_ID, S3_SECRET_KEY_ID)
print(s3.object.list_view('tessel', max_depth=4))
# print(s3.object.list_view('tessel'))

# s3.object.download_folder(
#     'test-s3', folder_prefix="a/")
# s3.object.list_view('tessel')
