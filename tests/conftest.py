import os
import time
import uuid

import pytest
from botocore.exceptions import ClientError

from s3_library import S3Utils

# Two independent local MinIO instances (see docker-compose.yml), simulating two
# different S3-compatible providers with different endpoints/credentials.
# Overridable via env vars so CI can point at differently-configured containers.
MINIO1_ENDPOINT = os.environ.get("MINIO1_ENDPOINT", "http://localhost:19000")
MINIO1_ACCESS_KEY = os.environ.get("MINIO1_ACCESS_KEY", "minioadmin1")
MINIO1_SECRET_KEY = os.environ.get("MINIO1_SECRET_KEY", "minioadmin1pass")

MINIO2_ENDPOINT = os.environ.get("MINIO2_ENDPOINT", "http://localhost:19010")
MINIO2_ACCESS_KEY = os.environ.get("MINIO2_ACCESS_KEY", "minioadmin2")
MINIO2_SECRET_KEY = os.environ.get("MINIO2_SECRET_KEY", "minioadmin2pass")


def _wait_for_minio(s3: S3Utils, timeout: float = 30.0) -> None:
    """
    Poll a MinIO instance until it accepts requests, or raise after `timeout` seconds.
    Avoids depending on Docker Compose healthcheck timing, since pytest is invoked as a
    separate step from `docker compose up`.
    """
    deadline = time.monotonic() + timeout
    last_error = None

    while time.monotonic() < deadline:
        try:
            s3.list_bucket()
            return
        except ClientError as e:
            last_error = e
        except Exception as e:  # connection refused while container is still starting
            last_error = e
        time.sleep(0.5)

    raise RuntimeError(f"MinIO did not become ready in time: {last_error}")


@pytest.fixture(scope="session")
def s3_instance_1() -> S3Utils:
    s3 = S3Utils(MINIO1_ACCESS_KEY, MINIO1_SECRET_KEY, MINIO1_ENDPOINT)
    _wait_for_minio(s3)
    return s3


@pytest.fixture(scope="session")
def s3_instance_2() -> S3Utils:
    s3 = S3Utils(MINIO2_ACCESS_KEY, MINIO2_SECRET_KEY, MINIO2_ENDPOINT)
    _wait_for_minio(s3)
    return s3


def _unique_bucket_name(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _cleanup_bucket(s3: S3Utils, bucket_name: str) -> None:
    """Delete all objects then the bucket itself, using the library's own methods."""
    s3.delete_objects(bucket_name=bucket_name, prefix="")
    s3.delete_bucket(bucket_name)


def put_object(s3: S3Utils, bucket_name: str, key: str, body: bytes = b"test-data",
               content_type: str = None, metadata: dict = None) -> None:
    """Seed a single object directly (bypassing upload_to_s3) for fast test setup."""
    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type
    if metadata:
        extra_args["Metadata"] = metadata
    s3.s3_resource.Object(bucket_name, key).put(Body=body, **extra_args)


@pytest.fixture
def same_instance_buckets(s3_instance_1):
    """Two buckets living on the SAME S3Utils instance."""
    bucket1 = _unique_bucket_name("test-same-1")
    bucket2 = _unique_bucket_name("test-same-2")

    s3_instance_1.create_bucket(bucket1)
    s3_instance_1.create_bucket(bucket2)

    yield s3_instance_1, bucket1, bucket2

    _cleanup_bucket(s3_instance_1, bucket1)
    _cleanup_bucket(s3_instance_1, bucket2)


@pytest.fixture
def cross_instance_buckets(s3_instance_1, s3_instance_2):
    """bucket1 lives on s3_instance_1, bucket2 lives on s3_instance_2 (different provider)."""
    bucket1 = _unique_bucket_name("test-cross-1")
    bucket2 = _unique_bucket_name("test-cross-2")

    s3_instance_1.create_bucket(bucket1)
    s3_instance_2.create_bucket(bucket2)

    yield s3_instance_1, bucket1, s3_instance_2, bucket2

    _cleanup_bucket(s3_instance_1, bucket1)
    _cleanup_bucket(s3_instance_2, bucket2)
