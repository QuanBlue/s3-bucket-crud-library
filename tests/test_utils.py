from s3_library.utils import helpers, tree_utils
import pytest
from conftest import put_object

def test_human_readable_size():
    assert helpers.human_readable_size(0) == "0 B"
    assert helpers.human_readable_size(1023) == "1023.00 B"
    assert helpers.human_readable_size(1024) == "1.00 KB"
    assert helpers.human_readable_size(1048576) == "1.00 MB"
    assert helpers.human_readable_size(1073741824) == "1.00 GB"

def test_list_folders_and_files(same_instance_buckets):
    s3, bucket1, _ = same_instance_buckets
    put_object(s3, bucket1, "a.txt", body=b"1")
    put_object(s3, bucket1, "folder/b.txt", body=b"2")
    
    folders, files = helpers.list_folders_and_files(s3.s3_client, bucket1, prefix="", max_items_per_level=5)
    assert "folder/" in folders
    assert "a.txt" in files
    
def test_read_csv_empty(tmp_path):
    # test reading a non-existent csv file
    data = helpers.read_csv(str(tmp_path / "nonexistent.csv"))
    assert data == []

def test_read_csv_content(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("path,prefix\nfile1.txt,prefix1/\n\nfile2.txt,prefix2/")
    data = helpers.read_csv(str(csv_file))
    assert len(data) == 2
    assert data[0]["path"] == "file1.txt"
    assert data[1]["path"] == "file2.txt"

def test_tree_utils_build_and_display(same_instance_buckets, capsys):
    s3, bucket1, _ = same_instance_buckets
    put_object(s3, bucket1, "dir1/f1.txt", body=b"hello")
    put_object(s3, bucket1, "dir2/f2.txt", body=b"world")
    
    tree = tree_utils.build_tree_from_s3(s3.s3_client, bucket1, max_depth=3, show_folder_size=True)
    assert tree.get_node("/") is not None
    
    tree_utils.display_s3_tree(tree, node_id="/", max_depth=3, show_folder_size=True)
    captured = capsys.readouterr()
    assert "dir1/" in captured.out
    assert "dir2/" in captured.out
