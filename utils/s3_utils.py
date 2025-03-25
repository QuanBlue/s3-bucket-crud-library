import boto3
from .s3_bucket import S3Bucket
from .s3_object import S3Object


class S3Utils(S3Bucket, S3Object):
    """Tích hợp cả S3Bucket và S3Object vào một class duy nhất."""

    def __init__(self, endpoint_url, aws_access_key, aws_secret_key):
        self.s3_resource = boto3.resource(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
        )

        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
        )

        # Kế thừa tất cả phương thức của S3Bucket & S3Object
        S3Bucket.__init__(self)
        S3Object.__init__(self)
