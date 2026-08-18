import csv
import os
import mimetypes


def list_objects_batch(s3_client, bucket_name: str, prefix: str = "", batch_size: int = 1000, continuation_token: str = None) -> tuple:
    """
    Retrieve a batch of objects from an S3 bucket.

    :param s3_client: Boto3 S3 client instance.
    :param bucket_name: Name of the S3 bucket.
    :param prefix: Prefix to filter objects.
    :param batch_size: Maximum number of objects to retrieve per API call.
    :param continuation_token: Token for pagination.
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
            object_sizes.append(obj["Size"])

    return object_keys, response.get("NextContinuationToken"), object_sizes


def delete_objects_batch(s3_resource, bucket_name: str, objects_to_delete: list) -> None:
    """
    Delete a batch of objects from an S3 bucket.

    :param s3_resource: Boto3 S3 resource instance.
    :param bucket_name: Name of the S3 bucket.
    :param objects_to_delete: List of objects to delete.
    """
    bucket = s3_resource.Bucket(bucket_name)
    total_deleted = 0
    batch_size = 1000

    for i in range(0, len(objects_to_delete), batch_size):
        batch = objects_to_delete[i:i + batch_size]
        response = bucket.delete_objects(Delete={"Objects": batch})
        deleted = response.get("Deleted", [])

        for obj in deleted:
            print(f"[INFO] Deleted: {obj.get('Key', obj)}")

        total_deleted += len(deleted)

    print(f"[INFO] Successfully deleted {total_deleted} objects from {bucket_name}.")


def human_readable_size(size: int, decimal_places: int = 2) -> str:
    """
    Convert file size from bytes to a human-readable format (KB, MB, GB, etc.).

    :param size: File size in bytes.
    :param decimal_places: Number of decimal places to retain.
    """
    if size == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    idx = 0

    while size >= 1024 and idx < len(units) - 1:
        size /= 1024.0
        idx += 1

    return f"{size:.{decimal_places}f} {units[idx]}"


def list_folders_and_files(s3_client, bucket_name: str, prefix: str, max_items_per_level: int = 5) -> tuple:
    """
    Retrieve folders and files directly under a specified prefix.

    :param s3_client: Boto3 S3 client instance.
    :param bucket_name: Name of the S3 bucket.
    :param prefix: Prefix to filter objects.
    :param max_items_per_level: Maximum items to retrieve per level.
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

        # get folder list
        for common_prefix in response.get("CommonPrefixes", []):
            folder_name = common_prefix["Prefix"][len(prefix):]
            folders[folder_name] = 0 

            if max_items_per_level and len(folders) >= max_items_per_level:
                break

        # get file list (just only not reach max_items_per_level)
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


def get_max_name_length(tree, node_id: str = "/", depth: int = 0, max_depth: int = 3) -> int:
    """
    Determine the maximum length of file/folder names for column size alignment.

    :param tree: The tree structure containing file/folder nodes.
    :param node_id: The identifier of the starting node, defaults to "/".
    :param depth: The current depth of recursion, defaults to 0.
    :param max_depth: The maximum depth to traverse, defaults to 3.
    """
    if depth >= max_depth:
        return 0

    node = tree.get_node(node_id)
    max_length = len(node.data["name"])

    for child in tree.children(node_id):
        max_length = max(max_length, get_max_name_length(
            tree, child.identifier, depth+1, max_depth))

    return max_length


def read_csv(file_path: str) -> list:
    """
    Read a CSV file and return a list of dictionaries.

    :param file_path: Path to the CSV file.
    """
    if not os.path.isfile(file_path):
        print(f"[ERROR] File CSV không tồn tại: {file_path}")
        return []

    data = []

    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)

        # get number of columns file CSV
        max_columns = max(len(row)for row in reader if row)
        file.seek(0)

        # name header
        new_header = ["path", "prefix"] + \
            [f"col_{i+3}" for i in range(max_columns - 2)]

        next(reader, None) # Skip the header row
        
        for row in reader:
            # skip empty line
            if len(row) < 1:
                continue

            row_dict = {new_header[i]: row[i].strip() if i < len(
                row) else "" for i in range(len(new_header))}

            data.append(row_dict)

    return data


def upload_file_to_s3(s3_resource, bucket_name: str, file_path: str, s3_key: str):
    """
    Upload a single file to an S3 bucket with the appropriate content type.

    :param s3_resource: Boto3 S3 resource instance.
    :param bucket_name: Name of the S3 bucket.
    :param file_path: Local file path.
    :param s3_key: S3 destination key.
    """
    content_type = mimetypes.guess_type(
        file_path)[0] or "application/octet-stream"

    with open(file_path, "rb") as f:
        s3_resource.Bucket(bucket_name).upload_fileobj(
            f, s3_key, ExtraArgs={"ContentType": content_type})

    print(f"[INFO] Uploaded: {file_path} -> s3://{bucket_name}/{s3_key}")




