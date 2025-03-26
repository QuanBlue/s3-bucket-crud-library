<h1 align="center">
  <img src="./assets/s3-bucket-logo.svg" alt="icon" width="200"></img>
  <br>
  <b>S3 Bucket CRUD Library</b>
</h1>

<p align="center">Library that can interact with Viettel Cloud, AWS S3 Bucket or any bucket that compatible AWS S3 bucket API</p>

<!-- Badges -->
<p align="center">
  <a href="https://github.com/QuanBlue/s3-bucket-crud-library/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/QuanBlue/s3-bucket-crud-library" alt="contributors" />
  </a>
  <a href="">
    <img src="https://img.shields.io/github/last-commit/QuanBlue/s3-bucket-crud-library" alt="last update" />
  </a>
  <a href="https://github.com/QuanBlue/s3-bucket-crud-library/network/members">
    <img src="https://img.shields.io/github/forks/QuanBlue/s3-bucket-crud-library" alt="forks" />
  </a>
  <a href="https://github.com/QuanBlue/s3-bucket-crud-library/stargazers">
    <img src="https://img.shields.io/github/stars/QuanBlue/s3-bucket-crud-library" alt="stars" />
  </a>
  <a href="https://github.com/QuanBlue/s3-bucket-crud-library/issues/">
    <img src="https://img.shields.io/github/issues/QuanBlue/s3-bucket-crud-library" alt="open issues" />
  </a>
  <a href="https://github.com/QuanBlue/s3-bucket-crud-library/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/QuanBlue/s3-bucket-crud-library.svg" alt="license" />
  </a>
</p>

<p align="center">
  <b>
      <a href="https://github.com/QuanBlue/s3-bucket-crud-library">Documentation</a> •
      <a href="https://github.com/QuanBlue/s3-bucket-crud-library/issues/">Report Bug</a> •
      <a href="https://github.com/QuanBlue/s3-bucket-crud-library/issues/">Request Feature</a>
  </b>
</p>

<br/>

<details open>
<summary><b>📖 Table of Contents</b></summary>

- [:star: Key features](#star-key-features)
- [:toolbox: Getting start](#toolbox-getting-start)
  - [:pushpin: Prerequisites](#pushpin-prerequisites)
  - [:key: Environment Variables](#key-environment-variables)
  - [:hammer\_and\_wrench: Installation](#hammer_and_wrench-installation)
  - [:open\_book: Usage](#open_book-usage)
    - [1. Import and Initialize](#1-import-and-initialize)
    - [2. Bucket Operations](#2-bucket-operations)
    - [3. Object Operations](#3-object-operations)
- [:world\_map: Roadmap](#world_map-roadmap)
- [:busts\_in\_silhouette: Contributors](#busts_in_silhouette-contributors)
- [:sparkles: Credits](#sparkles-credits)
- [:scroll: License](#scroll-license)
</details>

# :star: Key features

A Python library that simplifies interactions with S3-compatible object storage services for **Viettel Cloud**, **AWS S3 Bucket** or any bucket that **compatible AWS S3 bucket API**. It provides easy-to-use functions for managing buckets and objects, including creating, listing, uploading, and deleting files.

-  Create and delete S3 buckets
-  List all available buckets
-  Upload files or folders to S3
-  List objects in a bucket
-  Delete objects by prefix
-  Uses boto3 to interact with S3-compatible services

# :toolbox: Getting start

## :pushpin: Prerequisites

-  Python3
-  Python Package
   -  boto3 `>=1.36.0`
   -  dotenv `>=0.9.9`

## :key: Environment Variables

To run this project, you need to add the following environment variables to your `.env` :

-  **Configs:** Create `.env` file in `./`

   -  `ENDPOINT_URL`: Url that connect to S3 bucket provider
   -  `S3_ACCESS_KEY_ID`: S3 bucket access key
   -  `S3_SECRET_KEY_ID`: S3 bucket secret key id

   Example:

   ```dotenv
   # .env
   # with Viettel Cloud, using https://os.viettelcloud.vn/ endpoint
   # with AWS S3 bucket, using https://s3.<region>.amazonaws.com enpoint
   ENDPOINT_URL = https://os.viettelcloud.vn/
   S3_ACCESS_KEY_ID = xxxxxxxxxxxxxxxxxxxx
   S3_SECRET_KEY_ID = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

You can also check out the file `.env.example` to see all required environment variables.

> **Note**: If you want to use this example environment, you need to rename it to `.env`

## :hammer_and_wrench: Installation

Create python environment

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Install packages

```sh
pip install -r requirements.txt
```

## :open_book: Usage

### 1. Import and Initialize

```python
import os
from dotenv import load_dotenv
from utils import S3Utils

# Load environment variables
load_dotenv()
ENDPOINT_URL = os.getenv("ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_KEY_ID = os.getenv("S3_SECRET_KEY_ID")

os.environ["AWS_REQUEST_CHECKSUM_CALCULATION"] = "when_required"
os.environ["AWS_RESPONSE_CHECKSUM_VALIDATION"] = "when_required"

s3 = S3Utils(ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_KEY_ID)

# [... Your code here ...]
```

### 2. Bucket Operations

```python
# List all available buckets of this s3 bucket
buckets = s3.list_bucket()
print(buckets)

# Create a new bucket (ex: my-new-bucket)
s3.create_bucket(bucket_name="my-new-bucket")

# Delete a bucket (ex: my-new-bucket)
s3.delete_bucket(bucket_name="my-new-bucket")
```

### 3. Object Operations

List objects in bucket

```python
# List objects in bucket.
# By default it get first 1000 object (batch=1000)
objects = s3.list_objects_batch(bucket_name="my-bucket")

# List first 9999 objects in bucket.
objects = s3.list_objects_batch(bucket_name="my-bucket", batch="9999")

# List 1000 first object in folder (ex: foo/boo/)
objects = s3.list_objects_batch(bucket_name="my-bucket", prefix="foo/boo/")

# If you wanna create pagination
# use param: "continuation_token" (ex: list 1000 object has index 1001 to 2000)
objects = s3.list_objects_batch(bucket_name="my-bucket", continuation_token="1001")
```

Print object in tree format

```python
# by default it will show depth = 3 and 5 item in a folder
s3.print_objects_tree(bucket_name="my-bucket")

# output
#
# 📂 test-s3/
# ├─ 📂 utils/
# │   ├─ 📂 __pycache__/
# │   │   ├── 📄 13105_rev8.json
# │   │   ├── 📄 9734_rev5.json
# │   │   ├── 📄 __init__.cpython-312.pyc
# │   │   ├── 📄 s3_bucket.cpython-312.pyc
# │   │   ├── 📄 s3_object.cpython-312.pyc
# │   │   └── 📄 ...
# │   ├── 📄 __init__.py
# │   ├── 📄 s3_bucket.py
# │   ├── 📄 s3_object.py
# │   └── 📄 s3_utils.py
# ├── 📄 config.txt
# ...

# show tree with deeper (depth=6)
s3.print_objects_tree(bucket_name="my-bucket", max_depth=4)

# output
# 📂 test-s3/
# ├─ 📂 utils/
# │   ├─ 📂 __pycache__/
# │   │   ├─ 📂 images/
# │   │   │   ├── 📄 554acfd1-3680-46e4-8cc9-ffff9a546efc.jpeg
# │   │   │   ├── 📄 delete_image.py
# │   │   │   └── 📄 test.py
# │   │   ├── 📄 13105_rev8.json
# │   │   ├── 📄 9734_rev5.json
# ...
```

Download object/folder

```python
# Download a object (ex: s3_bucket.py)
# By default it will download at locate that you run script
s3.download_objects(bucket_name="my-bucket", prefix="s3_bucket.py")

# Download a folder (download all object have prefix <prefix>)
# It will create and download directory (ex: "utils") at locate that you run script
s3.download_objects(bucket_name="my-bucket", prefix="utils/")

# Download a object to different download dir (ex: /Download)
s3.download_objects(bucket_name="my-bucket", prefix="s3_bucket.py", local_dir="/Download")
```

Upload object/folder/specific objects in csv file

```python
# Upload a object (ex: s3_bucket.py)
# By default it will upload at root (/)
s3.upload_to_s3(bucket_name="my-bucket", source_path="s3_bucket.py")

# Upload a folder (ex: upload folder utils/)
s3.upload_to_s3(bucket_name="my-bucket", source_path="utils/")

# Upload a object to different folder (ex: upload s3_bucket.py to /utils folder)
s3.upload_to_s3(bucket_name="my-bucket", source_path="s3_bucket.py", s3_prefix="utils/")

# Upload objects in csv file
# It will upload all objects/folder that listed in csv file
#
# Ex: upload_objects.csv (at 1st line, it will upload s3_bucket.py to utils folder. At 2nd line, it will upload folder utils to root)
# s3_bucket.py, utils
# utils, 
s3.upload_to_s3(bucket_name="my-bucket", csv_file="upload_objects.csv")
```

Delete object/folder/specific objects in csv file

```python
# Delete a object (ex: s3_bucket.py)
s3.delete_objects(bucket_name="my-bucket", prefix="s3_bucket.py")

# Delete a folder (delete all object have prefix <prefix>) (ex: utils)
s3.delete_objects(bucket_name="my-bucket", prefix="utils/")

# Delete objects in csv file
# It will delete all objects/folder that listed in csv file
#
# Ex: delete_objects.csv
# s3_bucket.py
# utils
s3.delete_objects(bucket_name="my-bucket", csv_file="delete_objects.csv")
```

# :world_map: Roadmap

- [x] Basic CRUD
  - [x] Bucket
    - [x] List Bucket
    - [x] Create Bucket
    - [x] Delete Bucket
  - [x] Objects
    - [x] List Objects 
      - [x] List by batch (default 1000)
      - [x] Pagination 
    - [x] Upload Objects
      - [x] Upload single object
      - [x] Upload folder
      - [x] Upload objects by csv file 
    - [x] Delete Objects
      - [x] Delete single object
      - [x] Delete folder
      - [x] Delete objects by csv file 
  - [ ] Print Objects, folder
    - [x] Tree view
    - [ ] Object, folder size
- [ ] Sync between 2 Buckets


# :busts_in_silhouette: Contributors

<a href="https://github.com/QuanBlue/s3-bucket-crud-library/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=QuanBlue/s3-bucket-crud-library" />
</a>

Contributions are always welcome!

# :sparkles: Credits

This software uses the following packages:

-  [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) - AWS SDK for Python

Emoji and Badges from:

-  [github@thebespokepixel](https://github.com/thebespokepixel/badges) - Badges
-  [github@WebpageFX](https://github.com/WebpageFX/emoji-cheat-sheet.com) - Emoji

# :scroll: License

Distributed under the MIT License. See <a href="./LICENSE">`LICENSE`</a> for more information.

---

> Bento [@quanblue](https://bento.me/quanblue) &nbsp;&middot;&nbsp;
> GitHub [@QuanBlue](https://github.com/QuanBlue) &nbsp;&middot;&nbsp; Gmail quannguyenthanh558@gmail.com
