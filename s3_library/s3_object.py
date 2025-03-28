import csv
import os
import mimetypes
from treelib import Tree
from .utils import helpers, tree_utils


class S3Object:
    """Class tổng hợp cả S3Bucket và S3Object."""

    def upload_to_s3(self, bucket_name: str, source_path: str = "", s3_prefix: str = "", csv_file: str = None):
        """
        Tải lên một file hoặc toàn bộ thư mục lên S3.

        :param bucket_name: Tên bucket S3.
        :param source_path: Đường dẫn đến file hoặc folder cần upload.
        :param s3_prefix: Đường dẫn trên S3 (mặc định là root).
        :param csv_file: Đường dẫn đến file CSV chứa danh sách file path vaf prefix can up.
        """
        if csv_file:
            file_list = helpers.read_csv(csv_file)
            for file_info in file_list:
                path = file_info["path"]  # Đường dẫn file
                prefix = file_info["prefix"]

                self.upload_to_s3(bucket_name, path, prefix)
            
        else:
            # Chuẩn hóa s3_prefix để đảm bảo luôn có "/"
            if s3_prefix and not s3_prefix.endswith("/"):
                s3_prefix += "/"

            if os.path.isfile(source_path):
                # Upload file đơn lẻ
                file_name = os.path.basename(source_path)
                s3_key = os.path.join(s3_prefix, file_name).replace("\\", "/")
                helpers.upload_file_to_s3(self.s3_resource, bucket_name, source_path, s3_key)

            elif os.path.isdir(source_path):
                # Lấy tên folder cần tạo trên S3
                folder_name = os.path.basename(os.path.normpath(source_path))
                s3_folder_path = os.path.join(
                    s3_prefix, folder_name).replace("\\", "/") + "/"

                # 🟢 Tạo "folder" trên S3 bằng cách đặt một object rỗng
                self.s3_resource.Object(
                    bucket_name, s3_folder_path).put(Body="")
                print(
                    f"[INFO] Created folder: s3://{bucket_name}/{s3_folder_path}")

                # Upload tất cả các file bên trong folder
                for root, _, files in os.walk(source_path):
                    for file in files:
                        local_file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(local_file_path, source_path)
                        s3_key = os.path.join(
                            s3_folder_path, relative_path).replace("\\", "/")
                        helpers.upload_file_to_s3(self.s3_resource, bucket_name, local_file_path, s3_key)

            else:
                print(
                    f"[ERROR] {source_path} không tồn tại hoặc không hợp lệ.")
    
    

    def list_objects_batch(self, bucket_name, prefix="", batch_size=1000, continuation_token=None):
        """
        Lấy danh sách object trong S3 theo batch.

        :param bucket_name: Tên bucket S3.
        :param prefix: Prefix để lọc object.
        :param batch_size: Số lượng object tối đa trong mỗi lần gọi API.
        :param continuation_token: Token để phân trang.
        :return: Tuple (danh sách object keys, continuation_token tiếp theo, danh sách kích thước file).
        """

        object_keys, next_token, object_sizes = helpers.list_objects_batch(
            self.s3_client, bucket_name, prefix, batch_size, continuation_token
        )

        return object_keys, next_token, object_sizes

    def show_tree(self, bucket_name, node_id="/", depth=0, max_depth=5, max_items_per_level=5, prefix="", show_folder_size=False):
        tree = tree_utils.build_tree_from_s3(self.s3_client,
            bucket_name, prefix=prefix, show_folder_size=show_folder_size)

        tree_utils.display_s3_tree(tree=tree, node_id=node_id, depth=depth, max_depth=max_depth,
                   max_items_per_level=max_items_per_level, prefix=prefix, show_folder_size=show_folder_size)

    def download_objects(self, bucket_name, prefix, local_dir="./"):
        """
        Tải toàn bộ 'folder' từ S3 về máy, giữ nguyên cấu trúc thư mục và đặt trong folder có tên bucket_name.

        :param bucket_name: Tên bucket trên S3.
        :param prefix: Tên folder hoặc prefix trên S3, nhập file path để download object (ví dụ: 'myfolder/', 'a/b/c.png').
        :param local_dir: Thư mục gốc lưu file về máy (mặc định là './').
        """
        # Thư mục đích chứa toàn bộ nội dung bucket
        bucket_local_dir = os.path.join(local_dir, bucket_name)
        os.makedirs(bucket_local_dir, exist_ok=True)

        for obj in self.s3_resource.Bucket(bucket_name).objects.filter(Prefix=prefix):
            if obj.key.endswith("/"):  # Bỏ qua thư mục rỗng
                continue

            # Đường dẫn lưu file trong thư mục bucket_name
            local_path = os.path.join(bucket_local_dir, obj.key)

            # Tạo thư mục nếu chưa có
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Tải file về
            self.s3_resource.Bucket(
                bucket_name).download_file(obj.key, local_path)
            print(f"[INFO] Downloaded: {obj.key} -> {local_path}")

    # Done
    def delete_objects(self, bucket_name: str, prefix: str = "", csv_file: str = None):
        """
        Xóa một object hoặc tất cả objects có prefix trong S3, bao gồm cả "thư mục" nếu bị bỏ trống.

        :param bucket_name: Tên bucket trên S3.
        :param prefix: Tên object cụ thể hoặc prefix của các objects cần xóa (nếu không dùng CSV).
        :param csv_file: Đường dẫn đến file CSV chứa danh sách objects cần xóa.
        """
        bucket = self.s3_resource.Bucket(bucket_name)
        objects_to_delete = []

        if csv_file:
            file_list = helpers.read_csv(csv_file)
            for file_info in file_list:
                objects_to_delete.append({"Key": file_info["path"]})
                for obj in bucket.objects.filter(Prefix=file_info["path"]):
                    objects_to_delete.append({"Key": obj.key})
        else:
            # 🔵 Xóa theo prefix nếu không có file CSV
            objects_to_delete = [{"Key": obj.key}
                                 for obj in bucket.objects.filter(Prefix=prefix)]
            if not objects_to_delete:
                print(f"[INFO] No objects found with prefix: {prefix}")
                return

        # 🛠 Xóa theo batch (1000 object mỗi lần)
        helpers.delete_objects_batch(self.s3_resource, bucket_name, objects_to_delete)
