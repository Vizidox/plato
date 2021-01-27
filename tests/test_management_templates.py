import json

from http import HTTPStatus
from pathlib import Path

import boto3
import pytest
from moto import mock_s3

from plato.db.models import Template
from plato.db import db

from tests.test_application_set_up import BUCKET_NAME

CURRENT_TEST_PATH = str(Path(__file__).resolve().parent)
TEMPLATE_DETAILS_1 = {"title": "template_test_1",
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

TEMPLATE_DETAILS_2 = {"title": "template_test_2",
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


@pytest.fixture(scope="function")
def populate_db(client):
    with client.application.test_request_context():
        t = Template(id_='template_test_1',
                     schema={
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
                     type_="text/html", metadata={}, example_composition={}, tags=[])
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
class TestManageTemplates:
    CREATE_TEMPLATE_ENDPOINT = '/template/create'
    UPDATE_TEMPLATE = '/template/{0}/update'

    def test_create_new_template_invalid_zip_file(self, client):
        with open(f'{CURRENT_TEST_PATH}/resources/invalid_file.zip', 'rb') as file:
            template_details_str = json.dumps(TEMPLATE_DETAILS_2)
            data: dict = {'template_details': template_details_str}
            filename = 'invalid_file.zip'
            if file is not None:
                file_payload = (file, filename) if filename is not None else file
                data["zipfile"] = file_payload
            result = client.post(self.CREATE_TEMPLATE_ENDPOINT, data=data)
            assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_create_new_template_already_exists(self, client):
        with open(f'{CURRENT_TEST_PATH}/resources/template_test_1.zip', 'rb') as file:
            template_details_str = json.dumps(TEMPLATE_DETAILS_1)
            data: dict = {'template_details': template_details_str}
            template_id = "template_test_1"
            filename = f'{template_id}.zip'
            if file is not None:
                file_payload = (file, filename) if filename is not None else file
                data["zipfile"] = file_payload
            result = client.post(self.CREATE_TEMPLATE_ENDPOINT, data=data)
            assert result.status_code == HTTPStatus.CONFLICT

    def test_create_new_template_invalid_file_type(self, client):
        filename = 'example.pdf'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS_2)
        data: dict = {'template_details': template_details_str}
        if file is not None:
            file_payload = (file, filename) if filename is not None else file
            data["zipfile"] = file_payload
        result = client.post(self.CREATE_TEMPLATE_ENDPOINT, data=data)
        assert result.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE

    def test_create_new_template_ok(self, client):
        with open(f'{CURRENT_TEST_PATH}/resources/template_test_2.zip', 'rb') as file:
            template_id = "template_test_2"
            template_details_str = json.dumps(TEMPLATE_DETAILS_2)
            data: dict = {'template_details': template_details_str}
            filename = f'{template_id}.zip'
            if file is not None:
                file_payload = (file, filename) if filename is not None else file
                data["zipfile"] = file_payload

            result = client.post(self.CREATE_TEMPLATE_ENDPOINT, data=data)
            assert result.status_code == HTTPStatus.CREATED
            template_model: Template = Template.query.filter_by(id=template_id).one()
            assert template_model is not None

            expected_template = Template.from_json_dict(TEMPLATE_DETAILS_2)
            assert template_model.schema == expected_template.schema

    def test_update_template_invalid_zip_file(self, client):
        with open(f'{CURRENT_TEST_PATH}/resources/invalid_file.zip', 'rb') as file:
            template_details_str = json.dumps(TEMPLATE_DETAILS_2)
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
        template_details_str = json.dumps(TEMPLATE_DETAILS_2)
        data: dict = {'template_details': template_details_str}

        if file is not None:
            file_payload = (file, filename) if filename is not None else file
            data["zipfile"] = file_payload

        result = client.put(self.UPDATE_TEMPLATE.format(template_id), data=data)
        assert result.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE

    def test_update_template_invalid_id(self, client):
        template_id = "template_test_1_invalid"
        filename = 'template_test_2.zip'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS_2)
        data: dict = {'template_details': template_details_str}

        if file is not None:
            file_payload = (file, filename) if filename is not None else file
            data["zipfile"] = file_payload

        result = client.put(self.UPDATE_TEMPLATE.format(template_id), data=data)
        assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_update_template_not_found(self, client):
        template_id = "template_test_2"
        filename = 'template_test_2.zip'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS_2)
        data: dict = {'template_details': template_details_str}

        if file is not None:
            file_payload = (file, filename) if filename is not None else file
            data["zipfile"] = file_payload

        result = client.put(self.UPDATE_TEMPLATE.format(template_id), data=data)
        assert result.status_code == HTTPStatus.NOT_FOUND

    def test_update_template_ok(self, client):
        template_id = "template_test_1"
        filename = 'template_test_1.zip'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS_1)
        data: dict = {'template_details': template_details_str}

        if file is not None:
            file_payload = (file, filename) if filename is not None else file
            data["zipfile"] = file_payload

        result = client.put(self.UPDATE_TEMPLATE.format(template_id), data=data)
        assert result.status_code == HTTPStatus.OK
        template_model: Template = Template.query.filter_by(id=template_id).one()
        assert template_model.example_composition is not None
        expected_example_composition = {
                          "qr_code": "https://vizidox.com",
                          "cert_date": "2020-01-12",
                          "cert_name": "Alan Turing",
                          "serial_number": "C18009"
                      }
        assert template_model.example_composition == expected_example_composition

        expected_template = Template.from_json_dict(TEMPLATE_DETAILS_1)
        assert template_model.schema == expected_template.schema


