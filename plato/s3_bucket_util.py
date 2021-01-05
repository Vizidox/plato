import logging
import os
import zipfile
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError

from smart_open import s3


def get_file_s3(bucket_name: str, url: str, s3_template_directory: str) -> Dict[str, Any]:
    """
    Get files from s3 and save them in the form of a dict. If a folder is inserted as the url, all files in that folder
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


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        _ = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def upload_template_files_to_s3(template_id: str, s3_template_dir):
    """
    Uploads template related files (static and template) to each S3 bucket directory
    """

    # todo this code is working but needs some cleanups
    S3_BUCKET_ALT = 'vdx-local-test'

    # extract files to temporary directory
    file = zipfile.ZipFile('/tmp/zipfile.zip')
    file.extractall(path='/tmp/extracted_files')

    # list all the files
    static_files = os.listdir(f"/tmp/extracted_files/static/{template_id}")

    # uploads the files into S3
    _ = upload_file(f"/tmp/extracted_files/templates/{template_id}/{template_id}",
                    S3_BUCKET_ALT,
                    f"{s3_template_dir}/templates/{template_id}/{template_id}")

    for static_file in static_files:
        _ = upload_file(f"/tmp/extracted_files/static/{template_id}/{static_file}",
                        S3_BUCKET_ALT,
                        f"{s3_template_dir}/static/{template_id}/{static_file}")