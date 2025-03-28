from botocore.exceptions import ClientError
from . import helpers

def copy_object(s3_resource, source_bucket, dest_bucket, key):
    """
    Copy object từ source_bucket sang dest_bucket với key cho trước.
    """
    copy_source = {"Bucket": source_bucket, "Key": key}
    try:
        s3_resource.Object(dest_bucket, key).copy_from(
            CopySource=copy_source)
        print(f"[INFO] Copied {key} from {source_bucket} to {dest_bucket}")
    except ClientError as e:
        print(f"[ERROR] {e}")


def sync_objects(s3_client, s3_resource, source_bucket, dest_bucket, prefix=""):
    """Đồng bộ object từ source sang destination."""
    copied_count = 0
    source_keys, _, _ = helpers.list_objects_batch(s3_client, source_bucket, prefix)
    dest_keys, _, _ = helpers.list_objects_batch(
        s3_client, dest_bucket, prefix)

    new_keys = set(source_keys) - set(dest_keys)
    if not new_keys:
        print(
            f"✅ Không có object mới để đồng bộ từ {source_bucket} → {dest_bucket}.")
        return 0

    for key in new_keys:
        try:
            copy_object(
                s3_resource, source_bucket, dest_bucket, key)
            copied_count += 1
            print(f"📤 Đã sao chép: {key}")
        except ClientError as e:
            print(f"[ERROR] Lỗi sao chép {key}: {e}")

    return copied_count
