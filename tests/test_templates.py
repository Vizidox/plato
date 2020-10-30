from http import HTTPStatus

import pytest

from micro_templating.error_messages import template_not_found
from tests import get_message
from micro_templating.db.models import Template
from micro_templating.db import db
from json import loads as json_loads

NUMBER_OF_TEMPLATES = 157


@pytest.fixture(scope="class")
def populate_db(client):
    with client.application.test_request_context():
        for i in range(NUMBER_OF_TEMPLATES):
            t = Template(id_=str(i),
                         schema={"type": "object",
                                 "properties": {f"{i}": {"type": "string"}}
                                 },
                         type_="text/html", metadata={}, example_composition={}, tags=[])
            db.session.add(t)
        db.session.commit()

    yield

    with client.application.test_request_context():
        Template.query.delete()
        db.session.commit()


@pytest.mark.usefixtures("populate_db")
class TestTemplates:

    GET_TEMPLATES_ENDPOINT = '/templates/'
    GET_TEMPLATES_METHOD_NAME = "templates"

    GET_TEMPLATES_BY_ID_ENDPOINT = '/templates/{0}'
    GET_TEMPLATES_BY_ID_METHOD_NAME = "template_by_id"

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

        tentative_template_id = 39
        assert tentative_template_id < NUMBER_OF_TEMPLATES

        new_tentative_template_id = 200
        response = client.get(self.GET_TEMPLATES_BY_ID_ENDPOINT.format(new_tentative_template_id))
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert get_message(response) == template_not_found.format(new_tentative_template_id)
