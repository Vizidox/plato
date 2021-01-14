import os
import zipfile
from pathlib import Path
from typing import Dict, Any

from smart_open import s3

from plato.util.file_util import compute_s3_template_path, compute_s3_static_path, compute_tmp_static_path, \
    compute_tmp_template_path


class S3Error(Exception):
    """
    Error for any setup Exception to occur when running this module's functions.
    """
    ...


class NoStaticContentFound(S3Error):
    """
    raised when no static content fount on S3
    """

    def __init__(self, template_id: str):
        """
        Exception initialization

        :param template_id: the id of the template
        :type template_id: string
        """
        message = f"No static content found. template_id: {template_id}"
        super(NoStaticContentFound, self).__init__(message)


class NoIndexTemplateFound(S3Error):
    """
    raised when no template found on S3
    """

    def __init__(self, template_id: str):
        """
        Exception initialization

        :param template_id: the id of the template
        :type template_id: string
        """
        message = f"No index template file found. Template_id: {template_id}"
        super(NoIndexTemplateFound, self).__init__(message)


def get_file_s3(bucket_name: str, url: str, s3_template_directory: str) -> Dict[str, Any]:
    """
    Get files from S3 and save them in the form of a dict. If a folder is inserted as the url, all files in that folder
        will be returned

    :param bucket_name: the bucket_name we want to retrieve file from
    :type bucket_name: string

    :param url: the url leading to the file/folder
    :type url: string

    :param s3_template_directory: the s3-bucket path for the templates directory
    :type s3_template_directory: string

    :return: A dictionary with key as file's relative location on s3-bucket and value as file's content
    :rtype: Dict[str, Any]
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
    Uploads template related files (static and template) to their respective S3 bucket directories

    :param template_id: Template Id
    :param s3_template_dir: S3 Bucket template directory
    :param zip_file_name: Filename for the zipfile
    :param s3_bucket: S3 Bucket where the
    """

    # extract files to temporary directory
    file = zipfile.ZipFile(f'/tmp/{zip_file_name}.zip')
    file.extractall(path=f'/tmp/{zip_file_name}')

    local_template = Path(compute_tmp_template_path(zip_file_name, template_id))
    static_files = os.listdir(f"/tmp/{zip_file_name}/static/{template_id}")

    with local_template.open(mode='rb') as tmp_file:
        write_file_to_s3(tmp_file, s3_bucket, compute_s3_template_path(s3_template_dir, template_id))

    for static_file in static_files:
        tmp_static_path = Path(compute_tmp_static_path(zip_file_name, template_id, static_file))
        with tmp_static_path.open(mode='rb') as tmp_file:
            write_file_to_s3(tmp_file, s3_bucket, compute_s3_static_path(s3_template_dir, template_id, static_file))


def write_file_to_s3(input_file, s3_bucket, s3_path) -> None:
    with s3.open(s3_bucket, s3_path, mode='wb') as file:
        file.write(input_file.read())
