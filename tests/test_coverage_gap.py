import pytest
from botocore.exceptions import ClientError
from unittest.mock import patch, MagicMock
from s3_library.utils import helpers, sync_utils, tree_utils
from conftest import put_object
from treelib import Tree

def test_s3_object_empty_folder_download(same_instance_buckets, tmp_path):
    s3, bucket1, _ = same_instance_buckets
    # Create an empty folder object (key ending with /)
    s3.s3_resource.Object(bucket1, "empty_dir/").put(Body="")
    
    # Should skip downloading the empty folder, hitting the continue statement
    s3.download_objects(bucket1, prefix="empty_dir/", local_dir=str(tmp_path))
    assert not (tmp_path / bucket1 / "empty_dir").is_file()

def test_helpers_list_folders_and_files_pagination():
    # Mock s3_client to return a continuation token
    mock_client = MagicMock()
    mock_client.list_objects_v2.side_effect = [
        {"NextContinuationToken": "token123", "Contents": [{"Key": "file1.txt", "Size": 10}]},
        {"Contents": [{"Key": "file2.txt", "Size": 20}]}
    ]
    folders, files = helpers.list_folders_and_files(mock_client, "bucket", "")
    assert len(files) == 2
    assert "file1.txt" in files
    assert "file2.txt" in files

def test_helpers_list_folders_and_files_break(same_instance_buckets):
    s3, bucket1, _ = same_instance_buckets
    # Create 6 folders to trigger break
    for i in range(6):
        put_object(s3, bucket1, f"f{i}/test.txt", body=b"")
        
    folders, files = helpers.list_folders_and_files(s3.s3_client, bucket1, "", max_items_per_level=3)
    assert len(folders) == 3

    # Test file limit break
    bucket2 = "test-file-limit"
    s3.create_bucket(bucket2)
    for i in range(6):
        put_object(s3, bucket2, f"file{i}.txt", body=b"")
    folders, files = helpers.list_folders_and_files(s3.s3_client, bucket2, "", max_items_per_level=3)
    assert len(files) == 3
    s3.delete_objects(bucket2, "")
    s3.delete_bucket(bucket2)

def test_helpers_get_max_name_length_max_depth():
    tree = Tree()
    tree.create_node("root", "/")
    # max_depth 0 will hit the return 0 immediately
    length = helpers.get_max_name_length(tree, depth=3, max_depth=3)
    assert length == 0

def test_sync_utils_client_errors(capsys):
    mock_resource = MagicMock()
    mock_client = MagicMock()
    
    # Test copy_object ClientError
    mock_resource.Object().copy_from.side_effect = ClientError({"Error": {"Code": "Test", "Message": "Msg"}}, "op")
    sync_utils.copy_object(mock_resource, "src", "dst", "key")
    assert "[ERROR]" in capsys.readouterr().out
    
    # Test copy_object_stream ClientError
    mock_client.get_object.side_effect = ClientError({"Error": {"Code": "Test", "Message": "Msg"}}, "op")
    sync_utils.copy_object_stream(mock_client, mock_resource, "src", "dst", "key")
    assert "[ERROR]" in capsys.readouterr().out
    
    # Test sync_objects loop ClientError
    with patch("s3_library.utils.sync_utils.list_all_keys") as mock_list, \
         patch("s3_library.utils.sync_utils.copy_object") as mock_copy:
        mock_list.side_effect = [["key1"], []] # source has key1, dest is empty
        mock_copy.side_effect = ClientError({"Error": {"Code": "Test", "Message": "Msg"}}, "op")
        
        count = sync_utils.sync_objects(mock_client, mock_resource, "src", mock_client, mock_resource, "dst")
        assert count == 0
        assert "[ERROR]" in capsys.readouterr().out

def test_tree_utils_coverage(same_instance_buckets, capsys):
    s3, bucket1, _ = same_instance_buckets
    
    # Create nested structure to test max_depth logic
    put_object(s3, bucket1, "dir1/dir2/file.txt", body=b"")
    
    # build_tree_from_s3 max_depth=1 will hit continue logic
    tree = tree_utils.build_tree_from_s3(s3.s3_client, bucket1, max_depth=1)
    # the queue popped ("/", 0), added dir1 to queue with depth 1
    # next iteration will see depth >= max_depth (1 >= 1) and continue
    assert tree.get_node("dir1") is not None
    assert tree.get_node("dir1/dir2") is None
    
    # Create many items to hit show_more logic in display_s3_tree
    for i in range(6):
        put_object(s3, bucket1, f"file{i}.txt", body=b"")
    
    tree2 = tree_utils.build_tree_from_s3(s3.s3_client, bucket1)
    
    # max_depth limits output in display_s3_tree
    tree_utils.display_s3_tree(tree2, max_depth=0)
    
    # Truncate long names
    long_name = "a" * 50 + ".txt"
    put_object(s3, bucket1, long_name, body=b"")
    tree3 = tree_utils.build_tree_from_s3(s3.s3_client, bucket1)
    tree_utils.display_s3_tree(tree3, max_items_per_level=10)
    out = capsys.readouterr().out
    assert "..." in out
    
    # Show more logic triggered
    tree_utils.display_s3_tree(tree2, max_items_per_level=3)
    out = capsys.readouterr().out
    assert "└──  ..." in out
