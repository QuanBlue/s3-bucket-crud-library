from botocore.exceptions import ClientError
from . import helpers


def copy_object(s3_resource, source_bucket: str, dest_bucket: str, key: str) -> None:
    """
    Copy an object from the source bucket to the destination bucket with the given key.

    :param s3_resource: Boto3 S3 resource object.
    :param source_bucket: Name of the source S3 bucket.
    :param dest_bucket: Name of the destination S3 bucket.
    :param key: Object key to be copied.
    """
    copy_source = {"Bucket": source_bucket, "Key": key}
    try:
        s3_resource.Object(dest_bucket, key).copy_from(
            CopySource=copy_source)
        print(f"[INFO] Copied {key} from {source_bucket} to {dest_bucket}")
    except ClientError as e:
        print(f"[ERROR] {e}")


def sync_objects(s3_client, s3_resource, source_bucket: str, dest_bucket: str, prefix: str = "") -> int:
    """
    Synchronize objects from the source bucket to the destination bucket.

    :param s3_client: Boto3 S3 client object.
    :param s3_resource: Boto3 S3 resource object.
    :param source_bucket: Name of the source S3 bucket.
    :param dest_bucket: Name of the destination S3 bucket.
    :param prefix: Prefix to filter objects (default is an empty string).
    """
    copied_count = 0
    source_keys, _, _ = helpers.list_objects_batch(s3_client, source_bucket, prefix)
    dest_keys, _, _ = helpers.list_objects_batch(s3_client, dest_bucket, prefix)

    new_keys = set(source_keys) - set(dest_keys)
    if not new_keys:
        print(f"[INFO] No new objects to sync from {source_bucket} → {dest_bucket}.")

        return 0

    for key in new_keys:
        try:
            copy_object(s3_resource, source_bucket, dest_bucket, key)
            copied_count += 1
        except ClientError as e:
            print(f"[ERROR] Failed to copy {key}: {e}")

    return copied_count
