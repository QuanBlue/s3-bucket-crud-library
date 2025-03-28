from botocore.exceptions import ClientError
from .utils import sync_utils


class S3Bucket:
    """
    A class that provides functionalities for managing S3 buckets.
    """

    def create_bucket(self, bucket_name: str) -> None:
        """
        Creates a new S3 bucket.

        :param bucket_name: Name of the S3 bucket to be created.
        """
        try:
            self.s3_resource.create_bucket(Bucket=bucket_name)
            print(f"[INFO] Bucket '{bucket_name}' created!")
        except ClientError as e:
            print(f"[ERROR] {e}")


    def list_bucket(self) -> list[str]:
        """
        Lists all available S3 buckets.
        """
        return [bucket.name for bucket in self.s3_resource.buckets.all()]


    def delete_bucket(self, bucket_name: str) -> None:
        """
        Deletes an S3 bucket (only if the bucket is empty).

        :param bucket_name: Name of the S3 bucket to be deleted.
        """
        try:
            self.s3_resource.Bucket(bucket_name).delete()
            print(f"[INFO] Bucket '{bucket_name}' deleted!")
        except ClientError as e:
            print(f"[ERROR] {e}")
            
            
    def sync_buckets_unidirectional(self, source_bucket: str, dest_bucket: str, prefix: str = "") -> None:
        """
        Performs one-way synchronization from the source bucket to the destination bucket.

        :param source_bucket: Name of the source S3 bucket.
        :param dest_bucket: Name of the destination S3 bucket.
        :param prefix: Prefix to filter objects for synchronization.
        """
        print(f"[INFO] Syncing one-way from {source_bucket} → {dest_bucket} ...")
        copied_count = sync_utils.sync_objects(self.s3_client, self.s3_resource, source_bucket, dest_bucket, prefix)
        print(f"[INFO] Completed! {copied_count} objects copied.")


    def sync_buckets_bidirectional(self, bucket1: str, bucket2: str, prefix: str = "") -> None:
        """
        Performs bidirectional synchronization between two S3 buckets.

        :param bucket1: Name of the first S3 bucket.
        :param bucket2: Name of the second S3 bucket.
        :param prefix: Prefix to filter objects for synchronization.
        """
        print(f"[INFO] Syncing bidirectionally between {bucket1} ↔ {bucket2} ...")
        copied_1_to_2 = sync_utils.sync_objects(self.s3_client, self.s3_resource, bucket1, bucket2, prefix)
        copied_2_to_1 = sync_utils.sync_objects(self.s3_client, self.s3_resource, bucket2, bucket1, prefix)
        print(f"[INFO] Completed! {copied_1_to_2 + copied_2_to_1} objects copied.")
