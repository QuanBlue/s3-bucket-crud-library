import pytest
from botocore.exceptions import ClientError
from s3_library import S3Utils

def test_create_bucket(same_instance_buckets):
    s3, _, _ = same_instance_buckets
    bucket_name = "test-create-bucket-new"
    
    # Create the bucket
    s3.create_bucket(bucket_name)
    
    # Verify it exists
    buckets = s3.list_bucket()
    assert bucket_name in buckets
    
    # Cleanup
    s3.delete_bucket(bucket_name)

def test_list_bucket(same_instance_buckets):
    s3, bucket1, bucket2 = same_instance_buckets
    
    buckets = s3.list_bucket()
    assert bucket1 in buckets
    assert bucket2 in buckets

def test_delete_bucket(same_instance_buckets):
    s3, _, _ = same_instance_buckets
    bucket_name = "test-delete-bucket-tmp"
    
    s3.create_bucket(bucket_name)
    buckets = s3.list_bucket()
    assert bucket_name in buckets
    
    s3.delete_bucket(bucket_name)
    buckets = s3.list_bucket()
    assert bucket_name not in buckets

from unittest.mock import patch

def test_create_bucket_error(same_instance_buckets, capsys):
    s3, bucket1, _ = same_instance_buckets
    
    with patch.object(s3.s3_resource, 'create_bucket') as mock_create:
        mock_create.side_effect = ClientError(
            {"Error": {"Code": "BucketAlreadyExists", "Message": "Bucket already exists"}},
            "CreateBucket"
        )
        s3.create_bucket("some-bucket")
        
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.out

def test_delete_bucket_error(same_instance_buckets, capsys):
    s3, _, _ = same_instance_buckets
    # Try deleting a non-existent bucket
    s3.delete_bucket("non-existent-bucket-12345")
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.out
