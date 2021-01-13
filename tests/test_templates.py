import json
from http import HTTPStatus
from pathlib import Path

import boto3
import pytest
from moto import mock_s3

from plato.error_messages import template_not_found
from tests import get_message
from plato.db.models import Template
from plato.db import db
from json import loads as json_loads

from tests.test_application_set_up import BUCKET_NAME

CURRENT_TEST_PATH = str(Path(__file__).resolve().parent)
NUMBER_OF_TEMPLATES = 50
TEMPLATE_DETAILS = {"title": "template_test_1",
                    "schema": {
                        "type": "object",
                        "required": [
                            "cert_name",
                            "serial_number"
                        ],
                        "properties": {
                            "qr_code": {
                                "type": "string"
                            },
                            "cert_name": {
                                "type": "string"
                            },
                            "serial_number": {
                                "type": "string"
                            }
                        }
                    },
                    "type": "text/html",
                    "metadata": {
                        "qr_entries": [
                            "qr_code"
                        ]
                    },
                    "example_composition": {
                        "qr_code": "https://vizidox.com",
                        "cert_date": "2020-01-12",
                        "cert_name": "Alan Turing",
                        "serial_number": "C18009"
                    },
                    "tags": [
                    ]}


@pytest.fixture(scope="class")
def populate_db(client):
    with client.application.test_request_context():
        for i in range(NUMBER_OF_TEMPLATES):
            t = Template(id_=str(i),
                         schema={"type": "object",
                                 "properties": {f"{i}": {"type": "string"}}
                                 },
                         type_="text/html", metadata={}, example_composition={}, tags=[f"tag{str(i)}", "example"])
            db.session.add(t)
        db.session.commit()

    yield

    with client.application.test_request_context():
        Template.query.delete()
        db.session.commit()


@pytest.fixture(scope="function")
@mock_s3
def setup_s3():
    conn = boto3.resource('s3', region_name='eu-central-1')
    conn.create_bucket(Bucket=BUCKET_NAME)


@pytest.mark.usefixtures("populate_db")
@pytest.mark.usefixtures("setup_s3")
@mock_s3
class TestTemplates:
    GET_TEMPLATES_ENDPOINT = '/templates/'
    GET_TEMPLATES_METHOD_NAME = "templates"

    GET_TEMPLATES_BY_ID_ENDPOINT = '/templates/{0}'
    GET_TEMPLATES_BY_ID_METHOD_NAME = 'template_by_id'

    CREATE_TEMPLATE_ENDPOINT = '/template/create'
    UPDATE_TEMPLATE = '/template/{0}/update'

    def test_obtain_all_template_info(self, client):
        response = client.get(self.GET_TEMPLATES_ENDPOINT)
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == NUMBER_OF_TEMPLATES
        template_view_expected_keys = ["template_id", "template_schema", "type", "metadata", "tags"]
        for i, template_json in enumerate(response.json):
            assert all((key in template_json for key in template_view_expected_keys))
            assert i == json_loads(template_json["template_id"])

    def test_obtain_template_info_by_id_ok(self, client):

        tentative_template_id = 39
        assert tentative_template_id < NUMBER_OF_TEMPLATES

        response = client.get(f"{self.GET_TEMPLATES_ENDPOINT}{tentative_template_id}")
        assert response.status_code == HTTPStatus.OK
        template_info = response.json
        assert template_info and template_info is not None
        assert json_loads(template_info["template_id"]) == tentative_template_id

    def test_obtain_template_info_by_id_not_found(self, client):

        tentative_template_id = 200
        assert tentative_template_id > NUMBER_OF_TEMPLATES
        response = client.get(self.GET_TEMPLATES_BY_ID_ENDPOINT.format(tentative_template_id))
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert get_message(response) == template_not_found.format(tentative_template_id)

    def test_obtain_template_by_tags(self, client):
        for i in range(NUMBER_OF_TEMPLATES):
            current_tag = f"tag{i}"
            tags = {"tags": [current_tag]}
            response = client.get(self.GET_TEMPLATES_ENDPOINT, query_string=tags)
            assert response.status_code == HTTPStatus.OK
            assert len(response.json) == 1
            template_json = response.json[0]
            assert current_tag == template_json["tags"][0]

    def test_obtain_template_by_tags_empty(self, client):
        template_id = 67
        assert template_id > NUMBER_OF_TEMPLATES
        current_tag = f"tag{template_id}"
        tags = {"tags": [current_tag]}
        response = client.get(self.GET_TEMPLATES_ENDPOINT, query_string=tags)
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 0

    def test_obtain_template_by_more_than_one_tag(self, client):
        template_id = 32
        assert template_id < NUMBER_OF_TEMPLATES
        current_tag = f"tag{template_id}"
        tags = {"tags": [current_tag, "example"]}

        response = client.get(self.GET_TEMPLATES_ENDPOINT, query_string=tags)
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 1

    def test_create_new_file_invalid_zip_file(self, client):
        with open(f'{CURRENT_TEST_PATH}/resources/invalid_file.zip', 'rb') as file:
            template_details_str = json.dumps(TEMPLATE_DETAILS)
            data: dict = {'template_details': template_details_str}
            filename = 'invalid_file.zip'
            if file is not None:
                file_payload = (file, filename) if filename is not None else file
                data["zipfile"] = file_payload
            result = client.post(self.CREATE_TEMPLATE_ENDPOINT, data=data)
            assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_create_new_file_invalid_file_type(self, client):
        filename = 'example.pdf'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS)
        data: dict = {'template_details': template_details_str}
        if file is not None:
            file_payload = (file, filename) if filename is not None else file
            data["zipfile"] = file_payload
        result = client.post(self.CREATE_TEMPLATE_ENDPOINT, data=data)
        assert result.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE

    def test_create_new_file_ok(self, client):
        with open(f'{CURRENT_TEST_PATH}/resources/template_test_1.zip', 'rb') as file:
            template_details_str = json.dumps(TEMPLATE_DETAILS)
            data: dict = {'template_details': template_details_str}
            filename = 'template_test_1.zip'
            if file is not None:
                file_payload = (file, filename) if filename is not None else file
                data["zipfile"] = file_payload

            result = client.post(self.CREATE_TEMPLATE_ENDPOINT, data=data)
            assert result.status_code == HTTPStatus.CREATED

            template_id = "template_test_1"
            response = client.get(f"{self.GET_TEMPLATES_ENDPOINT}{template_id}")
            assert response.status_code == HTTPStatus.OK
            template_info = response.json
            assert template_info and template_info is not None
            assert template_info["template_id"] == template_id

    def test_update_template_invalid_zip_file(self, client):
        with open(f'{CURRENT_TEST_PATH}/resources/invalid_file.zip', 'rb') as file:
            template_details_str = json.dumps(TEMPLATE_DETAILS)
            data: dict = {'template_details': template_details_str}
            filename = 'invalid_file.zip'
            template_id = "template_test_1"

            if file is not None:
                file_payload = (file, filename) if filename is not None else file
                data["zipfile"] = file_payload
            result = client.put(self.UPDATE_TEMPLATE.format(template_id), data=data)
            assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_update_template_invalid_file_type(self, client):
        template_id = "template_test_1"
        filename = 'example.pdf'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS)
        data: dict = {'template_details': template_details_str}

        if file is not None:
            file_payload = (file, filename) if filename is not None else file
            data["zipfile"] = file_payload

        result = client.put(self.UPDATE_TEMPLATE.format(template_id), data=data)
        assert result.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE

    def test_update_template_invalid_template_id(self, client):
        template_id = "template_test_1_invalid"
        filename = 'template_test_1.zip'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS)
        data: dict = {'template_details': template_details_str}

        if file is not None:
            file_payload = (file, filename) if filename is not None else file
            data["zipfile"] = file_payload

        result = client.put(self.UPDATE_TEMPLATE.format(template_id), data=data)
        assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_update_template_ok(self, client):
        template_id = "template_test_1"
        filename = 'template_test_1.zip'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS)
        data: dict = {'template_details': template_details_str}

        if file is not None:
            file_payload = (file, filename) if filename is not None else file
            data["zipfile"] = file_payload

        result = client.put(self.UPDATE_TEMPLATE.format(template_id), data=data)
        assert result.status_code == HTTPStatus.OK

    def test_update_template_template_not_found(self, client):
        # deletes template in db if exists
        template_id = "template_test_1"
        Template.query.filter_by(id=template_id).delete()
        db.session.commit()

        filename = 'template_test_1.zip'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS)
        data: dict = {'template_details': template_details_str}

        if file is not None:
            file_payload = (file, filename) if filename is not None else file
            data["zipfile"] = file_payload

        result = client.put(self.UPDATE_TEMPLATE.format(template_id), data=data)
        assert result.status_code == HTTPStatus.NOT_FOUND
