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
            
            
    def sync_buckets_unidirectional(self, source_bucket: str, dest_bucket: str, prefix: str = "", dest_s3: "S3Utils" = None) -> None:
        """
        Performs one-way synchronization from the source bucket to the destination bucket.

        By default source and destination are assumed to live on this same S3Utils
        instance (same endpoint/credentials) and are copied server-side. Pass another
        already-initialized S3Utils instance as `dest_s3` to sync into a bucket hosted
        on a different S3-compatible provider (e.g. Viettel Cloud -> MinIO) - the
        objects are then streamed (GET from source, PUT to destination) instead.

        :param source_bucket: Name of the source S3 bucket.
        :param dest_bucket: Name of the destination S3 bucket.
        :param prefix: Prefix to filter objects for synchronization.
        :param dest_s3: Optional S3Utils instance hosting dest_bucket, when it lives on
            a different endpoint/credentials than this instance.
        """
        target = dest_s3 if dest_s3 is not None else self
        cross_instance = dest_s3 is not None

        print(f"[INFO] Syncing one-way from {source_bucket} → {dest_bucket} ...")
        copied_count = sync_utils.sync_objects(
            self.s3_client, self.s3_resource, source_bucket,
            target.s3_client, target.s3_resource, dest_bucket,
            prefix, cross_instance=cross_instance)
        print(f"[INFO] Completed! {copied_count} objects copied.")


    def sync_buckets_bidirectional(self, bucket1: str, bucket2: str, prefix: str = "", other_s3: "S3Utils" = None) -> None:
        """
        Performs bidirectional synchronization between two S3 buckets.

        By default both buckets are assumed to live on this same S3Utils instance (same
        endpoint/credentials) and are copied server-side. Pass another already-initialized
        S3Utils instance as `other_s3` to sync with a bucket hosted on a different
        S3-compatible provider - bucket1 is read from this instance, bucket2 from
        `other_s3`, and objects are streamed (GET from one side, PUT to the other)
        instead of using server-side copy.

        :param bucket1: Name of the first S3 bucket (on this instance).
        :param bucket2: Name of the second S3 bucket (on `other_s3`, if provided).
        :param prefix: Prefix to filter objects for synchronization.
        :param other_s3: Optional S3Utils instance hosting bucket2, when it lives on a
            different endpoint/credentials than this instance.
        """
        target = other_s3 if other_s3 is not None else self
        cross_instance = other_s3 is not None

        print(f"[INFO] Syncing bidirectionally between {bucket1} ↔ {bucket2} ...")
        copied_1_to_2 = sync_utils.sync_objects(
            self.s3_client, self.s3_resource, bucket1,
            target.s3_client, target.s3_resource, bucket2,
            prefix, cross_instance=cross_instance)
        copied_2_to_1 = sync_utils.sync_objects(
            target.s3_client, target.s3_resource, bucket2,
            self.s3_client, self.s3_resource, bucket1,
            prefix, cross_instance=cross_instance)
        print(f"[INFO] Completed! {copied_1_to_2 + copied_2_to_1} objects copied.")
