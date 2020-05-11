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


@pytest.mark.usefixtures("populate_db")
@mock_s3
class TestApplicationSetup:

    @staticmethod
    def get_template_file_path(partner_id: str, template_id: str):
        return TEMPLATE_FILE_PATH_FORMAT.format(partner_id, template_id, template_id)

    @staticmethod
    def get_static_file_path(partner_id: str, template_id: str, file_name: str):
        return STATIC_FILE_PATH_FORMAT.format(partner_id, template_id, file_name)

    @staticmethod
    def write_to_s3(bucket_name, file_path):
        encoding = "utf-8"
        with s3.open(bucket_name, key_id=file_path, mode="wb") as file:
            file.write(f"I am file !".encode(encoding))

    def setup(self):
        self.partner_id = "partner_id"

    def populate_s3(self, bucket_name: str):
        conn = boto3.resource('s3', region_name='eu-central-1')
        conn.create_bucket(Bucket=bucket_name)

        static_file = self.get_static_file_path(partner_id=self.partner_id, file_name="abc", template_id="0")
        self.write_to_s3(bucket_name=bucket_name, file_path=static_file)

        template_file = self.get_template_file_path(partner_id=self.partner_id, template_id="0")
        self.write_to_s3(bucket_name=bucket_name, file_path=template_file)


    def populate_s3_with_missing_static_file(self, bucket_name: str):
        conn = boto3.resource('s3', region_name='eu-central-1')
        conn.create_bucket(Bucket=bucket_name)

        template_file = self.get_template_file_path(partner_id=self.partner_id, template_id="0")
        self.write_to_s3(bucket_name=bucket_name, file_path=template_file)

    def populate_s3_with_missing_template_file(self, bucket_name):
        conn = boto3.resource('s3', region_name='eu-central-1')
        conn.create_bucket(Bucket=bucket_name)

        static_file = self.get_static_file_path(partner_id=self.partner_id, file_name="abc", template_id="0")
        self.write_to_s3(bucket_name=bucket_name, file_path=static_file)

    def test_success_case(self, client):
        bucket_name = "test_template_bucket_1"
        self.populate_s3(bucket_name)
        with client.application.test_request_context():
            with TemporaryDirectory() as temp:
                template_dir_name = temp + "/abc"
                pathlib.Path(template_dir_name).mkdir(parents=True, exist_ok=True)
                load_templates(bucket_name, template_dir_name)

    def test_missing_static_file(self, client):
        bucket_name = "test_template_bucket_2"
        self.populate_s3_with_missing_static_file(bucket_name)
        with client.application.test_request_context():
            with TemporaryDirectory() as temp:
                with pytest.raises(NoStaticContentFound):
                    template_dir_name = temp + "/abc"
                    pathlib.Path(template_dir_name).mkdir(parents=True, exist_ok=True)
                    load_templates(bucket_name, template_dir_name)

    def test_missing_template_file(self, client):
        bucket_name = "test_template_bucket_3"
        self.populate_s3_with_missing_template_file(bucket_name)
        with client.application.test_request_context():
            with pytest.raises(NoIndexTemplateFound):
                with TemporaryDirectory() as temp:
                    template_dir_name = temp + "/abc"
                    pathlib.Path(template_dir_name).mkdir(parents=True, exist_ok=True)
                    load_templates(bucket_name, template_dir_name)
