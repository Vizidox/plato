from http import HTTPStatus
from pathlib import Path

import pytest

from plato.error_messages import template_not_found
from tests import get_message
from plato.db.models import Template
from plato.db import db
from json import loads as json_loads


CURRENT_TEST_PATH = str(Path(__file__).resolve().parent)
NUMBER_OF_TEMPLATES = 50


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


@pytest.mark.usefixtures("populate_db")
class TestGetTemplates:
    GET_TEMPLATES_ENDPOINT = '/templates/'
    GET_TEMPLATES_METHOD_NAME = "templates"

    GET_TEMPLATES_BY_ID_ENDPOINT = '/templates/{0}'
    GET_TEMPLATES_BY_ID_METHOD_NAME = 'template_by_id'

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
