import os
from botocore.exceptions import NoCredentialsError, ClientError
import concurrent.futures


class _S3Object:
    """Class hỗ trợ CRUD cho object trên AWS S3."""

    def __init__(self, s3_resource, s3_client):
        self.s3_resource = s3_resource
        self.s3_client = s3_client

    # add upload folder
    def upload(self, bucket_name, s3_file_path, file):
        """Upload một file lên S3."""
        try:
            self.s3_resource.Object(
                bucket_name, s3_file_path).upload_file(file)
            print(
                f"[INFO] Uploaded '{s3_file_path}' on bucket '{bucket_name}' with key '{file}'")
        except (NoCredentialsError, ClientError) as e:
            print(f"[ERROR] {e}")

    # Done
    def list_objects_batch(self, bucket_name, prefix="", batch_size=1000, continuation_token=None):
        """
        Lấy một batch object từ S3 bằng paginator.

        :param bucket_name: Tên bucket
        :param prefix: Chỉ lấy object bắt đầu bằng prefix (thư mục)
        :param batch_size: Số object tối đa trong mỗi lần query
        :param continuation_token: Token để tiếp tục query (pagination)
        :return: (Danh sách object keys, Token tiếp theo)
        """
        operation_parameters = {
            "Bucket": bucket_name,
            "Prefix": prefix,
            "MaxKeys": batch_size,
        }
        if continuation_token:
            operation_parameters["ContinuationToken"] = continuation_token

        response = self.s3_client.list_objects_v2(**operation_parameters)
        object_keys = [obj["Key"] for obj in response.get("Contents", [])]

        next_token = response.get("NextContinuationToken")
        return object_keys, next_token


    # Done
    def list_view(self, bucket_name, prefix="", max_depth=3, max_items_per_level=5):
        """
        Hiển thị danh sách object dưới dạng cây thư mục sử dụng prefix.

        :param bucket_name: Tên bucket
        :param max_depth: Số level thư mục tối đa để hiển thị
        :param max_items_per_level: Số file/thư mục tối đa trong một level
        :param prefix: Thư mục gốc để bắt đầu quét (ví dụ: 'common/')
        """
        def list_folders_and_files(bucket_name, prefix, max_items_per_level):
            """
            Lấy danh sách thư mục và file ngay dưới `prefix` mà không duyệt sâu.
            Giới hạn số lượng kết quả để tránh query quá lâu nếu có quá nhiều object.

            :param bucket_name: Tên bucket
            :param prefix: Đường dẫn thư mục trên S3
            :param max_items_per_level: Số thư mục/file tối đa cần lấy (giới hạn hiển thị)
            :return: (Danh sách thư mục, Danh sách file)
            """
            folders = set()
            files = set()
            continuation_token = None

            while True:
                operation_parameters = {
                    "Bucket": bucket_name,
                    "Prefix": prefix,
                    "Delimiter": "/",  # Giúp S3 tự nhóm thư mục
                    "MaxKeys": 1000,  # Giới hạn mỗi batch lấy tối đa 1000 object
                }
                if continuation_token:
                    operation_parameters["ContinuationToken"] = continuation_token

                response = self.s3_client.list_objects_v2(**operation_parameters)

                if len(files) >= max_items_per_level:
                    break
                
                # S3 tự nhóm thư mục vào "CommonPrefixes"
                for common_prefix in response.get("CommonPrefixes", []):
                    folders.add(common_prefix["Prefix"][len(prefix):])
                    if len(folders) >= max_items_per_level:
                        break  # Dừng sớm nếu đủ số lượng

                # Các file riêng lẻ không nằm trong thư mục
                for obj in response.get("Contents", []):
                    relative_key = obj["Key"][len(prefix):]
                    if relative_key and "/" not in relative_key:
                        files.add(relative_key)
                        if len(files) >= max_items_per_level:
                            break  # Dừng sớm nếu đủ số lượng

                # Nếu đã đủ số lượng hiển thị, không query thêm nữa
                if len(folders) >= max_items_per_level and len(files) >= max_items_per_level:
                    break

                continuation_token = response.get("NextContinuationToken")
                if not continuation_token:
                    break  # Nếu không còn dữ liệu, dừng lại

            # Sắp xếp danh sách và giới hạn số lượng hiển thị
            folders = sorted(folders)[:max_items_per_level]
            files = sorted(files)[:max_items_per_level]

            # Nếu còn object nhưng đã giới hạn max_items_per_level, thêm "..."
            if len(folders) == max_items_per_level:
                folders.append("...")
            if len(files) == max_items_per_level:
                files.append("...")

            return folders, files

        def print_tree(bucket_name, prefix="", depth=0, indent=""):
            """
            Đệ quy in cây thư mục với các giới hạn.
            """
            if depth >= max_depth:
                return

            folders, files = list_folders_and_files(
                bucket_name, prefix, max_items_per_level)

            # Hiển thị thư mục
            folders = folders[:max_items_per_level] + \
                (["..."] if len(folders) > max_items_per_level else [])
            for idx, folder in enumerate(folders):
                connector = "└─ " if idx == len(
                    folders) - 1 and not files else "├─ "
                print(f"{indent}{connector}📂 {folder}")
                if folder != "...":
                    print_tree(bucket_name, prefix + folder, depth + 1, indent +
                               ("    " if idx == len(folders) - 1 and not files else "│   "))

            # Hiển thị file (chỉ in nếu có file trong thư mục)
            if files:
                files = files[:max_items_per_level] + \
                    (["..."] if len(files) > max_items_per_level else [])
                for idx, file in enumerate(files):
                    connector = "└── " if idx == len(files) - 1 else "├── "
                    print(f"{indent}{connector}📄 {file}")

        # Nếu prefix không rỗng, hiển thị từ thư mục con thay vì toàn bộ bucket
        print(f"📂 {bucket_name}/{prefix or ''}")
        print_tree(bucket_name, prefix)

    # Add download folder (add param prefix) merge with download folder func bellow
    def download_file(self, bucket_name, object_key, download_dir="./"):
        """Download một object từ S3."""
        try:
            file_name = os.path.basename(object_key)
            file_path = os.path.join(download_dir, file_name)

            self.s3_resource.Bucket(bucket_name).download_file(
                object_key, file_path)
            print(
                f"[INFO] Downloaded '{object_key}' from bucket '{bucket_name}' to '{file_path}'")
        except (NoCredentialsError, ClientError) as e:
            print(f"[ERROR] {e}")

    # Done 
    def download_folder(self, bucket_name, folder_prefix, local_dir="./"):
        """
        Tải toàn bộ 'folder' từ S3 về máy, giữ nguyên cấu trúc thư mục.

        :param s3: Đối tượng boto3.resource('s3')
        :param bucket_name: Tên bucket
        :param folder_prefix: Tên folder trên S3 (ví dụ: 'myfolder/')
        :param local_dir: Thư mục lưu file về máy (mặc định là './')
        """
        for obj in self.s3_resource.Bucket(bucket_name).objects.filter(Prefix=folder_prefix):
            # Bỏ qua folder rỗng
            if obj.key.endswith("/"):
                continue

            # Tạo đường dẫn file đích
            local_path = os.path.join(local_dir, obj.key)

            # Tạo thư mục nếu chưa có
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Tải file về
            self.s3_resource.Bucket(
                bucket_name).download_file(obj.key, local_path)
            print(f"[INFO] Downloaded: {obj.key} -> {local_path}")

    def delete(self, bucket_name, object_key):
        """Xóa một object trong S3."""
        try:
            self.s3_resource.Object(bucket_name, object_key).delete()
            print(
                f"[INFO] Deleted object '{object_key}' from bucket '{bucket_name}'")
        except ClientError as e:
            print(f"[ERROR] {e}")
