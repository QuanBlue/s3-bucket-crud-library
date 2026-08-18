import os
import csv
import pytest
from conftest import put_object

def test_upload_to_s3_single_file(same_instance_buckets, tmp_path):
    s3, bucket1, _ = same_instance_buckets
    
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("hello s3")
    
    s3.upload_to_s3(bucket1, source_path=str(file_path), s3_prefix="uploads/")
    
    keys, _, _ = s3.list_objects_batch(bucket1)
    assert "uploads/test_file.txt" in keys
    body = s3.s3_client.get_object(Bucket=bucket1, Key="uploads/test_file.txt")["Body"].read()
    assert body == b"hello s3"

def test_upload_to_s3_folder(same_instance_buckets, tmp_path):
    s3, bucket1, _ = same_instance_buckets
    
    folder_path = tmp_path / "test_folder"
    folder_path.mkdir()
    (folder_path / "file1.txt").write_text("f1")
    (folder_path / "file2.txt").write_text("f2")
    
    s3.upload_to_s3(bucket1, source_path=str(folder_path), s3_prefix="my_folder")
    
    keys, _, _ = s3.list_objects_batch(bucket1)
    # the code creates s3_prefix/folder_name/ 
    # my_folder/test_folder/file1.txt
    assert "my_folder/test_folder/" in keys
    assert "my_folder/test_folder/file1.txt" in keys
    assert "my_folder/test_folder/file2.txt" in keys

def test_upload_to_s3_csv(same_instance_buckets, tmp_path):
    s3, bucket1, _ = same_instance_buckets
    
    f1 = tmp_path / "f1.txt"
    f1.write_text("csv1")
    f2 = tmp_path / "f2.txt"
    f2.write_text("csv2")
    
    csv_file = tmp_path / "upload.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "prefix"])
        writer.writerow([str(f1), "csv_uploads/"])
        writer.writerow([str(f2), "csv_uploads/sub/"])
        
    s3.upload_to_s3(bucket1, csv_file=str(csv_file))
    
    keys, _, _ = s3.list_objects_batch(bucket1)
    assert "csv_uploads/f1.txt" in keys
    assert "csv_uploads/sub/f2.txt" in keys

def test_upload_to_s3_invalid_path(same_instance_buckets, capsys):
    s3, bucket1, _ = same_instance_buckets
    
    s3.upload_to_s3(bucket1, source_path="invalid/path/that/does/not/exist.txt")
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.out

def test_show_tree(same_instance_buckets, capsys):
    s3, bucket1, _ = same_instance_buckets
    put_object(s3, bucket1, "a.txt", body=b"a")
    put_object(s3, bucket1, "folder/b.txt", body=b"b")
    
    s3.show_tree(bucket1)
    captured = capsys.readouterr()
    assert bucket1 in captured.out
    assert "a.txt" in captured.out
    assert "folder" in captured.out
    assert "b.txt" in captured.out

def test_download_objects(same_instance_buckets, tmp_path):
    s3, bucket1, _ = same_instance_buckets
    put_object(s3, bucket1, "dl/file.txt", body=b"download_me")
    
    s3.download_objects(bucket1, prefix="dl/", local_dir=str(tmp_path))
    
    downloaded_file = tmp_path / bucket1 / "dl" / "file.txt"
    assert downloaded_file.exists()
    assert downloaded_file.read_text() == "download_me"

def test_delete_objects_prefix(same_instance_buckets):
    s3, bucket1, _ = same_instance_buckets
    put_object(s3, bucket1, "del/f1.txt", body=b"1")
    put_object(s3, bucket1, "keep/f2.txt", body=b"2")
    
    s3.delete_objects(bucket1, prefix="del/")
    
    keys, _, _ = s3.list_objects_batch(bucket1)
    assert "del/f1.txt" not in keys
    assert "keep/f2.txt" in keys

def test_delete_objects_empty_prefix(same_instance_buckets, capsys):
    s3, bucket1, _ = same_instance_buckets
    s3.delete_objects(bucket1, prefix="non-existent/")
    captured = capsys.readouterr()
    assert "[INFO] No objects found with prefix:" in captured.out

def test_delete_objects_csv(same_instance_buckets, tmp_path):
    s3, bucket1, _ = same_instance_buckets
    put_object(s3, bucket1, "del_csv/f1.txt", body=b"1")
    put_object(s3, bucket1, "del_csv/f2.txt", body=b"2")
    put_object(s3, bucket1, "keep/f3.txt", body=b"3")
    
    csv_file = tmp_path / "delete.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["path"])
        writer.writerow(["del_csv/f1.txt"])
        writer.writerow(["del_csv/f2.txt"])
        
    s3.delete_objects(bucket1, csv_file=str(csv_file))
    
    keys, _, _ = s3.list_objects_batch(bucket1)
    assert "del_csv/f1.txt" not in keys
    assert "del_csv/f2.txt" not in keys
    assert "keep/f3.txt" in keys
