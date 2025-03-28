from botocore.exceptions import ClientError
from .utils import helpers, sync_utils


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
            
    def sync_buckets_unidirectional(self, source_bucket, dest_bucket, prefix=""):
        """Đồng bộ dữ liệu một chiều từ source_bucket → dest_bucket."""
        print(
            f"🔄 Đang đồng bộ một chiều từ {source_bucket} → {dest_bucket} ...")
        copied_count = sync_utils.sync_objects(self.s3_client, self.s3_resource, source_bucket, dest_bucket, prefix)
        print(f"✅ Hoàn tất! {copied_count} object đã sao chép.")

    def sync_buckets_bidirectional(self, bucket1, bucket2, prefix=""):
        """Đồng bộ hai chiều giữa bucket1 và bucket2."""
        print(f"🔄 Đang đồng bộ hai chiều giữa {bucket1} ↔ {bucket2} ...")

        copied_1_to_2 = sync_utils.sync_objects(self.s3_client, self.s3_resource, bucket1, bucket2, prefix)
        copied_2_to_1 = sync_utils.sync_objects(self.s3_client, self.s3_resource, bucket2, bucket1, prefix)

        print(
            f"✅ Hoàn tất! {copied_1_to_2 + copied_2_to_1} object đã sao chép.")
