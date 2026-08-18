from botocore.exceptions import ClientError
from . import helpers


def copy_object(s3_resource, source_bucket: str, dest_bucket: str, key: str) -> None:
    """
    Server-side copy of an object between two buckets reachable by the same s3_resource
    (i.e. same S3Utils instance / same endpoint + credentials).
    """
    copy_source = {"Bucket": source_bucket, "Key": key}
    try:
        s3_resource.Object(dest_bucket, key).copy_from(
            CopySource=copy_source)
        print(f"[INFO] Copied {key} from {source_bucket} to {dest_bucket}")
    except ClientError as e:
        print(f"[ERROR] {e}")


def copy_object_stream(source_client, dest_resource, source_bucket: str, dest_bucket: str, key: str) -> None:
    """
    Stream an object from source_bucket (via source_client.get_object) directly into
    dest_bucket (via dest_resource upload_fileobj), without buffering the whole object
    in memory or writing it to local disk. Used when source and destination live on two
    different S3Utils instances (different endpoint/credentials), where server-side
    CopyObject is not possible because the destination service cannot reach into an
    unrelated provider's storage.

    Only ContentType and custom Metadata are preserved from the source object; other
    metadata (e.g. CacheControl, ContentEncoding) is not currently copied.
    """
    try:
        response = source_client.get_object(Bucket=source_bucket, Key=key)

        extra_args = {
            "ContentType": response.get("ContentType") or "application/octet-stream"}
        metadata = response.get("Metadata")
        if metadata:
            extra_args["Metadata"] = metadata

        dest_resource.Bucket(dest_bucket).upload_fileobj(
            response["Body"], key, ExtraArgs=extra_args)
        print(f"[INFO] Copied {key} from {source_bucket} to {dest_bucket} (cross-instance)")
    except ClientError as e:
        print(f"[ERROR] {e}")


def list_all_keys(s3_client, bucket_name: str, prefix: str = "", batch_size: int = 1000) -> list[str]:
    """
    Retrieve ALL object keys under a prefix in a bucket, looping through every page via
    NextContinuationToken. Unlike helpers.list_objects_batch (a single page, the public
    manual-pagination API), this exhausts pagination internally so callers never silently
    miss objects beyond the first batch_size keys.

    :param s3_client: Boto3 S3 client instance.
    :param bucket_name: Name of the S3 bucket.
    :param prefix: Prefix to filter objects.
    :param batch_size: Page size per underlying list_objects_v2 call.
    """
    keys = []
    continuation_token = None

    while True:
        page_keys, continuation_token, _sizes = helpers.list_objects_batch(
            s3_client, bucket_name, prefix, batch_size, continuation_token)
        keys.extend(page_keys)

        if not continuation_token:
            break

    return keys


def sync_objects(source_client, source_resource, source_bucket: str,
                  dest_client, dest_resource, dest_bucket: str,
                  prefix: str = "", cross_instance: bool = False) -> int:
    """
    Copy every object present in source_bucket but missing (by key) from dest_bucket.
    Only compares object keys - a key existing on both sides is never re-copied even if
    its content differs, and keys removed from the source are never deleted from the
    destination.

    :param source_client: Boto3 S3 client for the source bucket.
    :param source_resource: Boto3 S3 resource for the source bucket.
    :param source_bucket: Name of the source bucket.
    :param dest_client: Boto3 S3 client for the destination bucket.
    :param dest_resource: Boto3 S3 resource for the destination bucket.
    :param dest_bucket: Name of the destination bucket.
    :param prefix: Prefix to filter objects.
    :param cross_instance: True when source and destination belong to two different
        S3Utils instances (different endpoint/credentials) - uses streamed GET+PUT copy
        instead of server-side CopyObject.
    """
    copied_count = 0
    source_keys = list_all_keys(source_client, source_bucket, prefix)
    dest_keys = list_all_keys(dest_client, dest_bucket, prefix)

    new_keys = set(source_keys) - set(dest_keys)
    if not new_keys:
        print(f"[INFO] No new objects to sync from {source_bucket} → {dest_bucket}.")
        return 0

    for key in new_keys:
        try:
            if cross_instance:
                copy_object_stream(source_client, dest_resource, source_bucket, dest_bucket, key)
            else:
                copy_object(dest_resource, source_bucket, dest_bucket, key)
            copied_count += 1
        except ClientError as e:
            print(f"[ERROR] Failed to copy {key}: {e}")

    return copied_count
