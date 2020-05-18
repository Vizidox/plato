# -*- coding: utf-8 -*-
import boto3
import pytest
import pathlib
from moto import mock_s3
from smart_open import s3
from micro_templating.setup_util import load_templates, NoStaticContentFound, NoIndexTemplateFound
from tempfile import TemporaryDirectory
from micro_templating.db.models import Template, db

TEMPLATE_FILE_PATH_FORMAT = "templates/{0}/{1}/{2}"
STATIC_FILE_PATH_FORMAT = "static/{0}/{1}/{2}"


def get_template_file_path(partner_id: str, template_id: str):
    return TEMPLATE_FILE_PATH_FORMAT.format(partner_id, template_id, template_id)


def get_static_file_path(partner_id: str, template_id: str, file_name: str):
    return STATIC_FILE_PATH_FORMAT.format(partner_id, template_id, file_name)


def create_child_temp_folder(main_directory: str) -> None:
    template_dir_name = main_directory + "/abc"
    pathlib.Path(template_dir_name).mkdir(parents=True, exist_ok=True)
    return template_dir_name

def write_to_s3(bucket_name, file_path):
    encoding = "utf-8"
    with s3.open(bucket_name, key_id=file_path, mode="wb") as file:
        file.write(f"I am file !".encode(encoding))


@pytest.fixture(scope="class")
def populate_db(client):
    with client.application.test_request_context():
        template = Template(partner_id="partner_id", id_="0", schema={},
                            type_="text/html", tags=['test_tags'], metadata={}, example_composition="place_holder")
        db.session.add(template)
        db.session.commit()

    yield

    with client.application.test_request_context():
        Template.query.delete()
        db.session.commit()


@pytest.fixture(scope='function')
@mock_s3
def populate_s3() -> str:
    bucket_name = 'test_template_bucket_1'
    conn = boto3.resource('s3', region_name='eu-central-1')
    conn.create_bucket(Bucket=bucket_name)

    static_file = get_static_file_path(partner_id="partner_id", file_name="abc", template_id="0")
    write_to_s3(bucket_name=bucket_name, file_path=static_file)

    template_file = get_template_file_path(partner_id="partner_id", template_id="0")
    write_to_s3(bucket_name=bucket_name, file_path=template_file)

    return bucket_name


@pytest.fixture(scope='function')
@mock_s3
def populate_s3_with_missing_static_file() -> str:
    bucket_name = 'test_template_bucket_2'
    conn = boto3.resource('s3', region_name='eu-central-1')
    conn.create_bucket(Bucket=bucket_name)

    template_file = get_template_file_path(partner_id="partner_id", template_id="0")
    write_to_s3(bucket_name=bucket_name, file_path=template_file)

    return bucket_name


@pytest.fixture(scope='function')
@mock_s3
def populate_s3_with_missing_template_file() -> str:
    bucket_name = 'test_template_bucket_3'
    conn = boto3.resource('s3', region_name='eu-central-1')
    conn.create_bucket(Bucket=bucket_name)

    static_file = get_static_file_path(partner_id="partner_id", file_name="abc", template_id="0")
    write_to_s3(bucket_name=bucket_name, file_path=static_file)

    return bucket_name


@pytest.mark.usefixtures("populate_db")
@mock_s3
class TestApplicationSetup:
    def setup(self):
        self.partner_id = "partner_id"

    def test_success_case(self, client, populate_s3):
        bucket_name = populate_s3
        with client.application.test_request_context():
            with TemporaryDirectory() as temp:
                # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
                template_dir_name = create_child_temp_folder(temp)
                load_templates(bucket_name, template_dir_name)

    def test_missing_static_file(self, client, populate_s3_with_missing_static_file):
        bucket_name = populate_s3_with_missing_static_file
        with client.application.test_request_context():
            with TemporaryDirectory() as temp:
                with pytest.raises(NoStaticContentFound):
                    # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
                    template_dir_name = create_child_temp_folder(temp)
                    load_templates(bucket_name, template_dir_name)

    def test_missing_template_file(self, client, populate_s3_with_missing_template_file):
        bucket_name = populate_s3_with_missing_template_file
        with client.application.test_request_context():
            with pytest.raises(NoIndexTemplateFound):
                with TemporaryDirectory() as temp:
                    # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
                    template_dir_name = create_child_temp_folder(temp)
                    load_templates(bucket_name, template_dir_name)
