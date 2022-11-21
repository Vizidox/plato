import os
import pathlib
import zipfile
from pathlib import Path
from typing import Dict, Any, BinaryIO

from smart_open import s3

from plato.util.path_util import template_path, static_file_path, tmp_zipfile_path, tmp_path, static_path


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
    base_tmp_path = tmp_path(zip_file_name)
    # extract files to temporary directory
    file = zipfile.ZipFile(tmp_zipfile_path(zip_file_name))
    file.extractall(path=base_tmp_path)

    local_template = Path(template_path(base_tmp_path, template_id))
    with local_template.open(mode='rb') as tmp_file:
        write_file_to_s3(tmp_file, s3_bucket, template_path(s3_template_dir, template_id))

    static_files = os.listdir(static_path(base_tmp_path, template_id))
    for static_file in static_files:
        tmp_static_sys_path = Path(static_file_path(base_tmp_path, template_id, static_file))
        with tmp_static_sys_path.open(mode='rb') as tmp_file:
            write_file_to_s3(tmp_file, s3_bucket, static_file_path(s3_template_dir, template_id, static_file))


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


def write_files(files: Dict[str, Any], target_directory: str) -> None:
    """
    Write files to a target directory

    Args:
        files (Dict[str, Any]): a dict representing files needing to be written in the target directory
            with key as the file url and the value as file content
        target_directory (str): the directory all the files will reside in
    """
    for key, content in files.items():
        path = pathlib.Path(f"{target_directory}/{key}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, mode="wb") as file:
            file.write(content)
