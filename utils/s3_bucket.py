import boto3
import csv
import os
from botocore.exceptions import NoCredentialsError, ClientError
import mimetypes


class S3Bucket:
    """Class tổng hợp cả S3Bucket và S3Object."""
    def create_bucket(self, bucket_name):
        """Tạo bucket mới."""
        try:
            self.s3_resource.create_bucket(Bucket=bucket_name)
            print(f"[INFO] Bucket '{bucket_name}' created!")
        except ClientError as e:
            print(f"[ERROR] {e}")

    def list_bucket(self):
        """Liệt kê tất cả bucket."""
        buckets = [bucket.name for bucket in self.s3_resource.buckets.all()]
        return buckets  

    def delete_bucket(self, bucket_name):
        """Xóa bucket (chỉ xóa được nếu bucket rỗng)."""
        try:
            self.s3_resource.Bucket(bucket_name).delete()
            print(f"[INFO] Bucket '{bucket_name}' deleted!")
        except ClientError as e:
            print(f"[ERROR] {e}")