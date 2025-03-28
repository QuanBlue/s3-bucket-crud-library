import csv
import os
import mimetypes
from botocore.exceptions import ClientError
from . import sync_utils

def list_objects_batch(s3_client, bucket_name, prefix="", batch_size=1000, continuation_token=None):
    """
    Lấy danh sách object trong S3 theo batch.

    :param bucket_name: Tên bucket S3.
    :param prefix: Prefix để lọc object.
    :param batch_size: Số lượng object tối đa trong mỗi lần gọi API.
    :param continuation_token: Token để phân trang.
    :return: Tuple (danh sách object keys, continuation_token tiếp theo, danh sách kích thước file).
    """

    list_params = {
        "Bucket": bucket_name,
        "Prefix": prefix,
        "MaxKeys": batch_size,
        }
    if continuation_token:
        list_params["ContinuationToken"] = continuation_token

    response = s3_client.list_objects_v2(**list_params)

    object_keys = []
    object_sizes = []

    if "Contents" in response:
        for obj in response["Contents"]:
            object_keys.append(obj["Key"])
            object_sizes.append(obj["Size"])  # Lấy kích thước file

    return object_keys, response.get("NextContinuationToken"), object_sizes


def delete_objects_batch(s3_resource, bucket_name, objects_to_delete):
    """Xóa danh sách objects theo batch 1000 object/lần."""
    bucket = s3_resource.Bucket(bucket_name)
    total_deleted = 0
    batch_size = 1000

    for i in range(0, len(objects_to_delete), batch_size):
        batch = objects_to_delete[i:i + batch_size]
        response = bucket.delete_objects(Delete={"Objects": batch})
        deleted = response.get("Deleted", [])

        for obj in deleted:
            print(f"[INFO] Deleted: {obj['Key']}")

        total_deleted += len(deleted)

    print(
        f"[INFO] Successfully deleted {total_deleted} objects from {bucket_name}.")


def human_readable_size(size, decimal_places=2):
    """
    Chuyển đổi kích thước từ bytes sang KB, MB, GB, TB theo cách đọc dễ hiểu.

    :param size: Kích thước file tính bằng bytes.
    :param decimal_places: Số chữ số thập phân muốn giữ.
    :return: Chuỗi biểu diễn kích thước file ở đơn vị phù hợp.
    """
    if size == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    idx = 0

    while size >= 1024 and idx < len(units) - 1:
        size /= 1024.0
        idx += 1

    return f"{size:.{decimal_places}f} {units[idx]}"


def list_folders_and_files(s3_client, bucket_name, prefix, max_items_per_level=5):
    """
    Lấy danh sách folder và file trực tiếp dưới `prefix`.
    Ưu tiên lấy folder trước, sau đó mới lấy file nếu chưa đủ `max_items_per_level`.
    """
    folders = {}
    files = {}

    continuation_token = None
    while True:
        operation_parameters = {
            "Bucket": bucket_name,
            "Prefix": prefix,
            "Delimiter": "/",
            "MaxKeys": 1000,
        }
        if continuation_token:
            operation_parameters["ContinuationToken"] = continuation_token

        response = s3_client.list_objects_v2(**operation_parameters)

        # Lấy danh sách thư mục
        for common_prefix in response.get("CommonPrefixes", []):
            folder_name = common_prefix["Prefix"][len(
                prefix):]  # Lấy tên folder
            folders[folder_name] = 0  # Chưa tính size (có thể tính sau)

            if max_items_per_level and len(folders) >= max_items_per_level:
                break

        # Lấy danh sách file (chỉ khi chưa đủ max_items_per_level)
        for obj in response.get("Contents", []):
            relative_key = obj["Key"][len(prefix):]
            if relative_key and "/" not in relative_key:
                files[relative_key] = obj["Size"]

                if max_items_per_level and len(folders) + len(files) >= max_items_per_level:
                    break

        continuation_token = response.get("NextContinuationToken")
        if not continuation_token or (max_items_per_level and len(folders) + len(files) >= max_items_per_level):
            break

    return folders, files


def get_max_name_length(tree, node_id="/", depth=0, max_depth=3):
    """ Xác định độ dài lớn nhất của tên file/thư mục để căn chỉnh cột size """
    if depth >= max_depth:
        return 0

    node = tree.get_node(node_id)
    max_length = len(node.data["name"])

    for child in tree.children(node_id):
        max_length = max(max_length, get_max_name_length(
            tree, child.identifier, depth+1, max_depth))

    return max_length


def read_csv(file_path):
    """
    Đọc file CSV và trả về danh sách dict.

    - Cột đầu tiên luôn là 'path'.
    - Cột thứ hai (nếu có) là 'prefix'.
    - Các cột còn lại sẽ có tên dạng 'col_3', 'col_4', ...

    :param file_path: Đường dẫn tới file CSV.
    :return: Danh sách dict chứa dữ liệu CSV.
    """
    if not os.path.isfile(file_path):
        print(f"[ERROR] File CSV không tồn tại: {file_path}")
        return []

    data = []

    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)

        # Xác định số cột nhiều nhất trong file CSV
        max_columns = max(len(row)
                          for row in reader if row)  # Tránh dòng trống
        file.seek(0)  # Đặt lại con trỏ file về đầu để đọc lại từ đầu

        # Định danh tiêu đề
        new_header = ["path", "prefix"] + \
            [f"col_{i+3}" for i in range(max_columns - 2)]

        for row in reader:
            if len(row) < 1:  # Bỏ qua dòng trống
                continue

            row_dict = {new_header[i]: row[i].strip() if i < len(
                row) else "" for i in range(len(new_header))}

            data.append(row_dict)

    return data


def upload_file_to_s3(s3_resource, bucket_name, file_path, s3_key):
    """Upload một file đơn lẻ lên S3 với content-type phù hợp."""
    content_type = mimetypes.guess_type(
        file_path)[0] or "application/octet-stream"

    with open(file_path, "rb") as f:
        s3_resource.Bucket(bucket_name).upload_fileobj(
            f, s3_key, ExtraArgs={"ContentType": content_type})

    print(f"[INFO] Uploaded: {file_path} -> s3://{bucket_name}/{s3_key}")




