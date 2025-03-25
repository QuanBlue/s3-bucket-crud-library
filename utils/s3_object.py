import boto3
import csv
import os
from botocore.exceptions import NoCredentialsError, ClientError
import mimetypes


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
        if csv_file and os.path.isfile(csv_file):
            # 🟢 Đọc danh sách object từ file CSV
            with open(csv_file, mode="r", encoding="utf-8") as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) < 2:
                        print(f"[WARN] Dòng không hợp lệ (bỏ qua): {row}")
                        continue

                    src_path, prefix = row[0].strip(), row[1].strip()
                    if os.path.exists(src_path):
                        self.upload_to_s3(bucket_name, src_path, prefix)
                    else:
                        print(f"[ERROR] File không tồn tại: {src_path}")
        else:
            # Chuẩn hóa s3_prefix để đảm bảo luôn có "/"
            if s3_prefix and not s3_prefix.endswith("/"):
                s3_prefix += "/"

            if os.path.isfile(source_path):
                # Upload file đơn lẻ
                file_name = os.path.basename(source_path)
                s3_key = os.path.join(s3_prefix, file_name).replace("\\", "/")
                content_type = mimetypes.guess_type(
                    source_path)[0] or "application/octet-stream"

                with open(source_path, "rb") as f:
                    self.s3_resource.Bucket(bucket_name).upload_fileobj(
                        f, s3_key, ExtraArgs={"ContentType": content_type}
                    )

                print(
                    f"[INFO] Uploaded: {source_path} -> s3://{bucket_name}/{s3_key}")

            elif os.path.isdir(source_path):
                # Lấy tên folder cần tạo trên S3
                folder_name = os.path.basename(os.path.normpath(source_path))
                s3_folder_path = os.path.join(
                    s3_prefix, folder_name).replace("\\", "/") + "/"

                # 🟢 Tạo "folder" trên S3 bằng cách đặt một object rỗng
                self.s3_resource.Object(bucket_name, s3_folder_path).put(Body="")
                print(
                    f"[INFO] Created folder: s3://{bucket_name}/{s3_folder_path}")

                # Upload tất cả các file bên trong folder
                for root, _, files in os.walk(source_path):
                    for file in files:
                        local_file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(
                            local_file_path, source_path)
                        s3_key = os.path.join(
                            s3_folder_path, relative_path).replace("\\", "/")
                        content_type = mimetypes.guess_type(local_file_path)[
                            0] or "application/octet-stream"

                        with open(local_file_path, "rb") as f:
                            self.s3_resource.Bucket(bucket_name).upload_fileobj(
                                f, s3_key, ExtraArgs={"ContentType": content_type}
                            )

                        print(
                            f"[INFO] Uploaded: {local_file_path} -> s3://{bucket_name}/{s3_key}")

            else:
                print(f"[ERROR] {source_path} không tồn tại hoặc không hợp lệ.")
    

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
    def print_objects_tree(self, bucket_name, prefix="", max_depth=3, max_items_per_level=5):
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

                response = self.s3_client.list_objects_v2(
                    **operation_parameters)

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

    # Done
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

        if csv_file and os.path.isfile(csv_file):
            # 🟢 Đọc danh sách object từ file CSV
            with open(csv_file, mode="r", encoding="utf-8") as file:
                reader = csv.reader(file)
                object_keys = [row[0].strip() for row in reader if row]

            if not object_keys:
                print("[ERROR] CSV file is empty or invalid.")
                return

            # 🔹 Thêm object vào danh sách xóa
            # objects_to_delete = [{"Key": key} for key in object_keys]
            for key in object_keys:
                for obj in bucket.objects.filter(Prefix=key):
                    objects_to_delete.append({"Key": obj.key})

                # objects_to_delete = [{"Key": key}]

            print(
                f"[INFO] Read {len(objects_to_delete)} objects (including folders) from CSV: {csv_file}")

        else:
            # 🔵 Xóa theo prefix nếu không có file CSV
            objects_to_delete = [{"Key": obj.key}
                                 for obj in bucket.objects.filter(Prefix=prefix)]
            if not objects_to_delete:
                print(f"[INFO] No objects found with prefix: {prefix}")
                return

        # 🛠 Xóa theo batch (1000 object mỗi lần)
        total_deleted = 0
        batch = 1000
        for i in range(0, len(objects_to_delete), batch):
            batch = objects_to_delete[i:i + batch]
            response = bucket.delete_objects(Delete={"Objects": batch})
            deleted = response.get("Deleted", [])

            for obj in deleted:
                print(f"[INFO] Deleted: {obj['Key']}")

            total_deleted += len(deleted)

        print(
            f"[INFO] Successfully deleted {total_deleted} objects from {bucket_name}.")
