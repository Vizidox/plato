# -*- coding: utf-8 -*-
import boto3
from moto import mock_s3
from smart_open import s3
import pathlib

from micro_templating.setup_util import load_templates
from tempfile import TemporaryDirectory


@mock_s3
def test_template_loading():
    """
    Test the retrieval of every directory and file in a s3 bucket
    """
    conn = boto3.resource('s3', region_name='eu-central-1')
    bucket_name = "test_template_bucket"
    conn.create_bucket(Bucket=bucket_name)

    # directory names
    n_of_test_dir = 5
    encoding = "utf-8"

    for i in range(0, n_of_test_dir):
        # file names
        for n in range(0, i+1):
            with s3.open(bucket_name, key_id=f"{i}/{n}", mode="wb") as file:
                file.write(f"I am file {i}{n}!".encode(encoding))

    with TemporaryDirectory() as template_dir_name:
        load_templates(bucket_name, template_dir_name)

        dir_path = pathlib.Path(template_dir_name)
        all_template_dirs = list(dir_path.iterdir())

        assert len(all_template_dirs) == n_of_test_dir
        for dir_ in all_template_dirs:
            file_list = list(dir_.iterdir())

            assert len(file_list) == int(dir_.name) + 1

        updatee_path = f"{template_dir_name}/{n_of_test_dir - 1}/0"
        with open(updatee_path, mode='r', encoding=encoding) as updatee_file:
            assert updatee_file.read() == f"I am file {n_of_test_dir-1}0!"

        # update file
        with s3.open(bucket_name, key_id=f"{n_of_test_dir - 1}/0", mode="wb") as file:
            file.write(f"I am an updated file!".encode(encoding))

        load_templates(bucket_name, template_dir_name)

        with open(updatee_path, mode='r', encoding=encoding) as updatee_file:
            assert updatee_file.read() == f"I am an updated file!"
