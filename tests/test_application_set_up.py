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

    for i in range(0, n_of_test_dir):
        # file names
        for n in range(0, i+1):
            with s3.open(bucket_name, key_id=f"{i}/{n}", mode="wb") as file:
                file.write(f"I am file {i}{n}!".encode("latin-1"))

    with TemporaryDirectory() as template_dir_name:
        load_templates(bucket_name, template_dir_name)

        dir_path = pathlib.Path(template_dir_name)
        all_template_dirs = list(dir_path.iterdir())

        assert len(all_template_dirs) == n_of_test_dir
        for dir_ in all_template_dirs:
            file_list = list(dir_.iterdir())

            assert len(file_list) == int(dir_.name) + 1

