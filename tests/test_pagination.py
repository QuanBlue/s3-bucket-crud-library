"""
Confirms the sync helpers fully paginate through NextContinuationToken instead of only
looking at the first page (the pre-existing bug: sync_objects used to call
helpers.list_objects_batch once, silently missing anything beyond the first
`batch_size` keys). Uses a small `batch_size` override so the multi-page path is
exercised without needing >1000 real objects.
"""
from conftest import put_object
from s3_library.utils import sync_utils

OBJECT_COUNT = 25
SMALL_BATCH_SIZE = 5


def test_list_all_keys_paginates_across_multiple_pages(same_instance_buckets):
    s3, bucket1, _bucket2 = same_instance_buckets

    expected_keys = {f"key-{i:03d}.txt" for i in range(OBJECT_COUNT)}
    for key in expected_keys:
        put_object(s3, bucket1, key, body=b"x")

    keys = sync_utils.list_all_keys(s3.s3_client, bucket1, batch_size=SMALL_BATCH_SIZE)

    assert len(keys) == OBJECT_COUNT  # no duplicates
    assert set(keys) == expected_keys  # nothing missing


def test_sync_objects_syncs_beyond_first_page(same_instance_buckets):
    s3, bucket1, bucket2 = same_instance_buckets

    expected_keys = {f"key-{i:03d}.txt" for i in range(OBJECT_COUNT)}
    for key in expected_keys:
        put_object(s3, bucket1, key, body=b"x")

    copied_count = sync_utils.sync_objects(
        s3.s3_client, s3.s3_resource, bucket1,
        s3.s3_client, s3.s3_resource, bucket2,
        cross_instance=False,
    )

    assert copied_count == OBJECT_COUNT
    dest_keys, _, _ = s3.list_objects_batch(bucket2, batch_size=1000)
    assert set(dest_keys) == expected_keys
