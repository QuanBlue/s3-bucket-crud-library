import boto3
from .s3_bucket import S3Bucket
from .s3_object import S3Object


class S3Utils(S3Bucket, S3Object):
    """
    A unified class that integrates both S3Bucket and S3Object functionalities.
    """
    viettel_cloud_endpoint = "https://os.viettelcloud.vn/"
    
    def __init__(self, s3_access_key: str, s3_secret_key: str, s3_endpoint_url: str = viettel_cloud_endpoint):
        """
        Initializes the S3Utils class with S3 credentials and sets up S3 resource and client.

        :param s3_endpoint_url: s3 endpoint
        :param s3_access_key: s3 access key ID.
        :param s3_secret_key: s3 secret access key.
        """
        self.s3_resource = boto3.resource(
            's3',
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
            endpoint_url=s3_endpoint_url
        )

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
            endpoint_url=s3_endpoint_url
        )

        S3Bucket.__init__(self)
        S3Object.__init__(self)

