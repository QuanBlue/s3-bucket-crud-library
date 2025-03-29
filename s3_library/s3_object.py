import os
from .utils import helpers, tree_utils


class S3Object:
    """
    Class that integrates both S3Bucket and S3Object functionalities.
    """

    def upload_to_s3(self, bucket_name: str, source_path: str = "", s3_prefix: str = "", csv_file: str = None) -> None:
        """
        Upload a file or an entire directory to an S3 bucket.

        :param bucket_name: Name of the S3 bucket.
        :param source_path: Path to the file or folder to upload.
        :param s3_prefix: Destination path in S3 (default is root).
        :param csv_file: Path to a CSV file containing file paths and prefixes for batch upload.
        """
        if csv_file:
            file_list = helpers.read_csv(csv_file)
            
            # upload all file in csv file 
            for file_info in file_list:
                path = file_info["path"] 
                prefix = file_info["prefix"]
                self.upload_to_s3(bucket_name, path, prefix)

        else:
            # standardize S3_Prefix to make sure there is always "/"
            if s3_prefix and not s3_prefix.endswith("/"):
                s3_prefix += "/"

            # upload single file
            if os.path.isfile(source_path):
                file_name = os.path.basename(source_path)
                s3_key = os.path.join(s3_prefix, file_name).replace("\\", "/")
                helpers.upload_file_to_s3(
                    self.s3_resource, bucket_name, source_path, s3_key)
            
            # Upload folder (muti-file in folder)
            elif os.path.isdir(source_path):
                # create folder
                folder_name = os.path.basename(os.path.normpath(source_path))
                s3_folder_path = os.path.join(s3_prefix, folder_name).replace("\\", "/") + "/"
                self.s3_resource.Object(bucket_name, s3_folder_path).put(Body="")
                print(f"[INFO] Created folder: s3://{bucket_name}/{s3_folder_path}")

                # Upload all files in folder
                for root, _, files in os.walk(source_path):
                    for file in files:
                        local_file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(local_file_path, source_path)
                        s3_key = os.path.join(s3_folder_path, relative_path).replace("\\", "/")
                        helpers.upload_file_to_s3(self.s3_resource, bucket_name, local_file_path, s3_key)

            else:
                print(f"[ERROR] {source_path} does not exist or is invalid.")

    def list_objects_batch(self, bucket_name: str, prefix: str = "", batch_size: int = 1000, continuation_token: str = None) -> tuple:
        """
        Retrieve a batch of objects from an S3 bucket.

        :param bucket_name: Name of the S3 bucket.
        :param prefix: Prefix to filter objects.
        :param batch_size: Maximum number of objects per API call.
        :param continuation_token: Token for pagination.
        """
        return helpers.list_objects_batch(self.s3_client, bucket_name, prefix, batch_size, continuation_token)


    def show_tree(self, bucket_name: str, node_id: str = "/", depth: int = 0, max_depth: int = 5, max_items_per_level: int = 5, prefix: str = "", show_folder_size: bool = False) -> None:
        """
        Display the S3 bucket structure as a tree.

        :param bucket_name: Name of the S3 bucket.
        :param node_id: Root node identifier.
        :param depth: Current depth.
        :param max_depth: Maximum depth to display.
        :param max_items_per_level: Maximum items to display per level.
        :param prefix: Prefix for filtering objects.
        :param show_folder_size: Whether to display folder sizes.
        """
        tree = tree_utils.build_tree_from_s3(self.s3_client,bucket_name, prefix=prefix, show_folder_size=show_folder_size)
        tree_utils.display_s3_tree(tree=tree, node_id=node_id, depth=depth, max_depth=max_depth, 
                                   max_items_per_level=max_items_per_level, prefix=prefix, show_folder_size=show_folder_size)


    def download_objects(self, bucket_name: str, prefix: str = "", local_dir: str = "./") -> None:
        """
        Download all objects matching a prefix from an S3 bucket, maintaining directory structure.

        :param bucket_name: Name of the S3 bucket.
        :param prefix: Folder or object prefix to download (e.g., 'myfolder/', 'a/b/c.png').
        :param local_dir: Local directory to store downloaded files (default is './').
        """  
        bucket_local_dir = os.path.join(local_dir, bucket_name)
        os.makedirs(bucket_local_dir, exist_ok=True)

        for obj in self.s3_resource.Bucket(bucket_name).objects.filter(Prefix=prefix):
            if obj.key.endswith("/"):  # skip the empty folder
                continue


            # create folder if not exists
            local_path = os.path.join(bucket_local_dir, obj.key)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # download file
            self.s3_resource.Bucket(
                bucket_name).download_file(obj.key, local_path)
            print(f"[INFO] Downloaded: {obj.key} -> {local_path}")


    def delete_objects(self, bucket_name: str, prefix: str = "", csv_file: str = None) -> None:
        """
        Deletes objects from an S3 bucket.

        :param bucket_name: Name of the S3 bucket.
        :param prefix: Prefix or object key to delete.
        :param csv_file: Path to a CSV file containing objects to delete.
        """
        bucket = self.s3_resource.Bucket(bucket_name)
        objects_to_delete = []

        if csv_file:
            # delete objects list in csv file
            file_list = helpers.read_csv(csv_file)
            for file_info in file_list:
                objects_to_delete.append({"Key": file_info["path"]})
                for obj in bucket.objects.filter(Prefix=file_info["path"]):
                    objects_to_delete.append({"Key": obj.key})
        else:
            # delete objects
            objects_to_delete = [{"Key": obj.key} for obj in bucket.objects.filter(Prefix=prefix)]
            if not objects_to_delete:
                print(f"[INFO] No objects found with prefix: {prefix}")
                return

        # delete batch (1000 object/time)
        helpers.delete_objects_batch(self.s3_resource, bucket_name, objects_to_delete)
