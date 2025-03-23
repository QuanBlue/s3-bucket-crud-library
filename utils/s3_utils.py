import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from .s3_bucket import _S3Bucket
from .s3_object import _S3Object


class S3Utils:
    """Class tổng hợp cả S3Bucket và S3Object."""

    def __init__(self, aws_access_key, aws_secret_key):
        self.s3_resource = boto3.resource(
            's3',
            endpoint_url="https://os.viettelcloud.vn/",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
        )
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url="https://os.viettelcloud.vn/",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
        )

        self.bucket = _S3Bucket(self.s3_resource, self.s3_client)
        self.object = _S3Object(self.s3_resource, self.s3_client)
