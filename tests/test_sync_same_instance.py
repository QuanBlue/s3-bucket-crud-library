"""
Regression tests for sync_buckets_unidirectional/bidirectional WITHOUT dest_s3/other_s3
(i.e. both buckets on the same S3Utils instance) - confirms the pre-existing behavior,
plus the new full-pagination fix, is untouched by the cross-instance feature.
"""
from conftest import put_object


def test_unidirectional_copies_new_objects(same_instance_buckets):
    s3, bucket1, bucket2 = same_instance_buckets

    put_object(s3, bucket1, "a.txt", body=b"content-a")
    put_object(s3, bucket1, "b.txt", body=b"content-b")
    put_object(s3, bucket1, "c.txt", body=b"content-c")

    s3.sync_buckets_unidirectional(source_bucket=bucket1, dest_bucket=bucket2)

    keys, _, _ = s3.list_objects_batch(bucket2)
    assert set(keys) == {"a.txt", "b.txt", "c.txt"}
    assert s3.s3_client.get_object(Bucket=bucket2, Key="a.txt")["Body"].read() == b"content-a"


def test_unidirectional_skips_existing_keys(same_instance_buckets):
    s3, bucket1, bucket2 = same_instance_buckets

    put_object(s3, bucket1, "shared.txt", body=b"from-source")
    put_object(s3, bucket2, "shared.txt", body=b"already-in-dest")

    s3.sync_buckets_unidirectional(source_bucket=bucket1, dest_bucket=bucket2)

    body = s3.s3_client.get_object(Bucket=bucket2, Key="shared.txt")["Body"].read()
    assert body == b"already-in-dest"


def test_unidirectional_prefix_filter(same_instance_buckets):
    s3, bucket1, bucket2 = same_instance_buckets

    put_object(s3, bucket1, "foo/a.txt", body=b"in-prefix")
    put_object(s3, bucket1, "bar/b.txt", body=b"outside-prefix")

    s3.sync_buckets_unidirectional(source_bucket=bucket1, dest_bucket=bucket2, prefix="foo/")

    keys, _, _ = s3.list_objects_batch(bucket2)
    assert keys == ["foo/a.txt"]


def test_bidirectional_merges_both_ways(same_instance_buckets):
    s3, bucket1, bucket2 = same_instance_buckets

    put_object(s3, bucket1, "only-in-1.txt", body=b"1")
    put_object(s3, bucket2, "only-in-2.txt", body=b"2")

    s3.sync_buckets_bidirectional(bucket1=bucket1, bucket2=bucket2)

    keys1, _, _ = s3.list_objects_batch(bucket1)
    keys2, _, _ = s3.list_objects_batch(bucket2)
    assert set(keys1) == {"only-in-1.txt", "only-in-2.txt"}
    assert set(keys2) == {"only-in-1.txt", "only-in-2.txt"}
