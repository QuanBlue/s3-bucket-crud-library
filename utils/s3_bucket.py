from botocore.exceptions import ClientError

class _S3Bucket:
    """Class hỗ trợ CRUD cho bucket trên AWS S3."""

    def __init__(self, s3_resource, s3_client):
        self.s3_resource = s3_resource
        self.s3_client = s3_client
        

    def create(self, bucket_name):
        """Tạo bucket mới."""
        try:
            self.s3_resource.create_bucket(Bucket=bucket_name)
            print(f"[INFO] Bucket '{bucket_name}' created!")
        except ClientError as e:
            print(f"[ERROR] {e}")

    def list(self):
        """Liệt kê tất cả bucket."""
        buckets = [bucket.name for bucket in self.s3_resource.buckets.all()]
        return buckets

    def delete(self, bucket_name):
        """Xóa bucket (chỉ xóa được nếu bucket rỗng)."""
        try:
            self.s3_resource.Bucket(bucket_name).delete()
            print(f"[INFO] Bucket '{bucket_name}' deleted!")
        except ClientError as e:
            print(f"[ERROR] {e}")
