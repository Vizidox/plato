import os
import zipfile
from pathlib import Path
from typing import Dict, Any, BinaryIO

from smart_open import s3


class S3Error(Exception):
    """
    Error for any setup Exception to occur when running this module's functions.
    """
    ...


class NoStaticContentFound(S3Error):
    """
    Raised when no static content found on S3
    """

    def __init__(self, template_id: str):
        """
        Exception initialization

        Args:
            template_id (str): the id of the template

        """
        message = f"No static content found. template_id: {template_id}"
        super(NoStaticContentFound, self).__init__(message)


class NoIndexTemplateFound(S3Error):
    """
    Raised when no template found on S3
    """

    def __init__(self, template_id: str):
        """
        Exception initialization

        Args:
            template_id (str): the id of the template
        """
        message = f"No index template file found. Template_id: {template_id}"
        super(NoIndexTemplateFound, self).__init__(message)


def get_file_s3(bucket_name: str, url: str, s3_template_directory: str) -> Dict[str, Any]:
    """
    Get files from S3 and save them in the form of a dict. If a folder is inserted as the url, all files in that folder
        will be returned

    Args:
        bucket_name (str): the bucket_name we want to retrieve file from
        url (str): the url leading to the file/folder
        s3_template_directory (str): the s3-bucket path for the templates directory

    Returns:
     A dictionary with key as file's relative location on s3-bucket and value as file's content
    """
    key_content_mapping: dict = {}
    for key, content in s3.iter_bucket(bucket_name=bucket_name, prefix=url):
        if key[-1] == '/' or not content:
            # Is a directory
            continue
        # based on https://www.python.org/dev/peps/pep-0616/
        new_key = key[len(s3_template_directory):]
        key_content_mapping[new_key] = content
    return key_content_mapping


def upload_template_files_to_s3(template_id: str, s3_template_dir: str, zip_file_name: str, s3_bucket: str) -> None:
    """
    Uploads template related files (static and template) to their respective S3 Bucket directories

    Args:
        template_id (str): the template id
        s3_template_dir (str): S3 Bucket template directory
        zip_file_name (str): the filename for the zipfile
        s3_bucket (str): S3 Bucket
    """

    # extract files to temporary directory
    file = zipfile.ZipFile(f'/tmp/{zip_file_name}.zip')
    file.extractall(path=f'/tmp/{zip_file_name}')

    local_template = Path(f"/tmp/{zip_file_name}/templates/{template_id}/{template_id}")
    s3_template_path = f"{s3_template_dir}/templates/{template_id}/{template_id}"
    static_files = os.listdir(f"/tmp/{zip_file_name}/static/{template_id}")

    with local_template.open(mode='rb') as fin:
        write_file_to_s3(fin, s3_bucket, s3_template_path)

    for static_file in static_files:
        with open(f"/tmp/{zip_file_name}/static/{template_id}/{static_file}", mode='rb') as fin:
            write_file_to_s3(fin, s3_bucket, f"{s3_template_dir}/static/{template_id}/{static_file}")


def write_file_to_s3(input_file: BinaryIO, s3_bucket: str, s3_path: str) -> None:
    """
    Write file to S3 Bucket Path

    Args:
        input_file (BinaryIO): the input file
        s3_bucket (str): S3 Bucket
        s3_path (str): the S3 Bucket path
    """
    with s3.open(s3_bucket, s3_path, mode='wb') as file:
        file.write(input_file.read())
