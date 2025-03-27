import boto3
import csv
import os
from botocore.exceptions import NoCredentialsError, ClientError
import mimetypes


class S3Bucket:
    """Class tổng hợp cả S3Bucket và S3Object."""
    def create_bucket(self, bucket_name):
        """Tạo bucket mới."""
        try:
            self.s3_resource.create_bucket(Bucket=bucket_name)
            print(f"[INFO] Bucket '{bucket_name}' created!")
        except ClientError as e:
            print(f"[ERROR] {e}")

    def list_bucket(self):
        """Liệt kê tất cả bucket."""
        buckets = [bucket.name for bucket in self.s3_resource.buckets.all()]
        return buckets  

    def delete_bucket(self, bucket_name):
        """Xóa bucket (chỉ xóa được nếu bucket rỗng)."""
        try:
            self.s3_resource.Bucket(bucket_name).delete()
            print(f"[INFO] Bucket '{bucket_name}' deleted!")
        except ClientError as e:
            print(f"[ERROR] {e}")
    
    def list_objects(self, bucket_name, prefix=""):
        """
        Liệt kê các object trong bucket với prefix (trả về dict key: metadata).
        Metadata chứa 'Size' và 'LastModified'
        """
        objects = {}
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    objects[key] = {
                        "Size": obj["Size"],
                        "LastModified": obj["LastModified"]
                    }
        except ClientError as e:
            print(f"[ERROR] {e}")
        return objects

    def copy_object(self, source_bucket, dest_bucket, key):
        """
        Copy object từ source_bucket sang dest_bucket với key cho trước.
        """
        copy_source = {"Bucket": source_bucket, "Key": key}
        try:
            self.s3_resource.Object(dest_bucket, key).copy_from(
                CopySource=copy_source)
            print(f"[INFO] Copied {key} from {source_bucket} to {dest_bucket}")
        except ClientError as e:
            print(f"[ERROR] {e}")

    def sync_buckets_unidirectional(self, source_bucket, dest_bucket, prefix=""):
        """
        One-way sync: Copy các object từ source_bucket sang dest_bucket nếu:
         - Object không tồn tại ở dest_bucket
         - Hoặc (nếu kích thước khác hoặc LastModified mới hơn)
        
        :param source_bucket: Bucket nguồn
        :param dest_bucket: Bucket đích
        :param prefix: Prefix để lọc object (nếu có)
        """
        print(
            f"[SYNC ONE-WAY] Syncing from '{source_bucket}' to '{dest_bucket}' with prefix '{prefix}'")
        source_objs = self.list_objects(source_bucket, prefix)
        dest_objs = self.list_objects(dest_bucket, prefix)

        for key, metadata in source_objs.items():
            src_size = metadata["Size"]
            src_last_modified = metadata["LastModified"]

            dest_meta = dest_objs.get(key)
            need_copy = False

            if not dest_meta:
                # Object chưa tồn tại ở dest
                need_copy = True
            else:
                dest_size = dest_meta["Size"]
                dest_last_modified = dest_meta["LastModified"]
                # Nếu kích thước khác hoặc source mới hơn
                if src_size != dest_size or src_last_modified > dest_last_modified:
                    need_copy = True

            if need_copy:
                self.copy_object(source_bucket, dest_bucket, key)

    def sync_buckets_bidirectional(self, bucket1, bucket2, prefix=""):
        """
        Two-way sync: Đồng bộ dữ liệu giữa bucket1 và bucket2.
        Các object sẽ được copy từ bucket nào thiếu, hoặc cập nhật nếu source mới hơn.
        
        :param bucket1: Bucket thứ nhất
        :param bucket2: Bucket thứ hai
        :param prefix: Prefix để lọc object (nếu có)
        """
        print(
            f"[SYNC TWO-WAY] Syncing between '{bucket1}' and '{bucket2}' with prefix '{prefix}'")
        objs1 = self.list_objects(bucket1, prefix)
        objs2 = self.list_objects(bucket2, prefix)

        # Đồng bộ từ bucket1 sang bucket2
        for key, meta1 in objs1.items():
            obj2 = objs2.get(key)
            need_copy = False
            if not obj2:
                need_copy = True
            else:
                if meta1["Size"] != obj2["Size"] or meta1["LastModified"] > obj2["LastModified"]:
                    need_copy = True
            if need_copy:
                self.copy_object(bucket1, bucket2, key)

        # Đồng bộ từ bucket2 sang bucket1
        for key, meta2 in objs2.items():
            obj1 = objs1.get(key)
            need_copy = False
            if not obj1:
                need_copy = True
            else:
                if meta2["Size"] != obj1["Size"] or meta2["LastModified"] > obj1["LastModified"]:
                    need_copy = True
            if need_copy:
                self.copy_object(bucket2, bucket1, key)
