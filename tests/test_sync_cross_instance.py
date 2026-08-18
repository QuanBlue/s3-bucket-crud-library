"""
Tests for sync_buckets_unidirectional/bidirectional WITH dest_s3/other_s3 - i.e. source
and destination buckets live on two independent S3Utils instances (different MinIO
containers here, standing in for two different S3-compatible providers such as
Viettel Cloud and MinIO). This exercises the streamed GET+PUT copy path.
"""
import os

from conftest import put_object


def test_cross_unidirectional_copies_new_objects(cross_instance_buckets):
    s3_a, bucket1, s3_b, bucket2 = cross_instance_buckets

    put_object(s3_a, bucket1, "a.txt", body=b"content-a")
    put_object(s3_a, bucket1, "b.txt", body=b"content-b")

    s3_a.sync_buckets_unidirectional(source_bucket=bucket1, dest_bucket=bucket2, dest_s3=s3_b)

    keys, _, _ = s3_b.list_objects_batch(bucket2)
    assert set(keys) == {"a.txt", "b.txt"}
    assert s3_b.s3_client.get_object(Bucket=bucket2, Key="a.txt")["Body"].read() == b"content-a"


def test_cross_unidirectional_preserves_content_type(cross_instance_buckets):
    s3_a, bucket1, s3_b, bucket2 = cross_instance_buckets

    put_object(s3_a, bucket1, "data.json", body=b'{"k": "v"}', content_type="application/json")

    s3_a.sync_buckets_unidirectional(source_bucket=bucket1, dest_bucket=bucket2, dest_s3=s3_b)

    head = s3_b.s3_client.head_object(Bucket=bucket2, Key="data.json")
    assert head["ContentType"] == "application/json"


def test_cross_unidirectional_preserves_metadata(cross_instance_buckets):
    s3_a, bucket1, s3_b, bucket2 = cross_instance_buckets

    put_object(s3_a, bucket1, "meta.txt", body=b"x", metadata={"custom-key": "custom-value"})

    s3_a.sync_buckets_unidirectional(source_bucket=bucket1, dest_bucket=bucket2, dest_s3=s3_b)

    head = s3_b.s3_client.head_object(Bucket=bucket2, Key="meta.txt")
    assert head["Metadata"].get("custom-key") == "custom-value"


def test_cross_unidirectional_skips_existing_keys(cross_instance_buckets):
    s3_a, bucket1, s3_b, bucket2 = cross_instance_buckets

    put_object(s3_a, bucket1, "shared.txt", body=b"from-source")
    put_object(s3_b, bucket2, "shared.txt", body=b"already-in-dest")

    s3_a.sync_buckets_unidirectional(source_bucket=bucket1, dest_bucket=bucket2, dest_s3=s3_b)

    body = s3_b.s3_client.get_object(Bucket=bucket2, Key="shared.txt")["Body"].read()
    assert body == b"already-in-dest"


def test_cross_unidirectional_prefix_filter(cross_instance_buckets):
    s3_a, bucket1, s3_b, bucket2 = cross_instance_buckets

    put_object(s3_a, bucket1, "foo/a.txt", body=b"in-prefix")
    put_object(s3_a, bucket1, "bar/b.txt", body=b"outside-prefix")

    s3_a.sync_buckets_unidirectional(source_bucket=bucket1, dest_bucket=bucket2, prefix="foo/", dest_s3=s3_b)

    keys, _, _ = s3_b.list_objects_batch(bucket2)
    assert keys == ["foo/a.txt"]


def test_cross_bidirectional_merges_both_ways(cross_instance_buckets):
    s3_a, bucket1, s3_b, bucket2 = cross_instance_buckets

    put_object(s3_a, bucket1, "only-in-1.txt", body=b"1")
    put_object(s3_b, bucket2, "only-in-2.txt", body=b"2")

    s3_a.sync_buckets_bidirectional(bucket1=bucket1, bucket2=bucket2, other_s3=s3_b)

    keys1, _, _ = s3_a.list_objects_batch(bucket1)
    keys2, _, _ = s3_b.list_objects_batch(bucket2)
    assert set(keys1) == {"only-in-1.txt", "only-in-2.txt"}
    assert set(keys2) == {"only-in-1.txt", "only-in-2.txt"}


def test_cross_instance_streams_moderately_large_object(cross_instance_buckets):
    s3_a, bucket1, s3_b, bucket2 = cross_instance_buckets

    payload = os.urandom(5 * 1024 * 1024)  # 5 MB, exercises the streaming path end-to-end
    put_object(s3_a, bucket1, "big.bin", body=payload)

    s3_a.sync_buckets_unidirectional(source_bucket=bucket1, dest_bucket=bucket2, dest_s3=s3_b)

    dest_body = s3_b.s3_client.get_object(Bucket=bucket2, Key="big.bin")["Body"].read()
    assert dest_body == payload
