from http import HTTPStatus

import pytest

from tests import partner_id_set
from tests.conftest import MockAuthenticator
from micro_templating.db.models import Template
from micro_templating.db import db
from json import loads as json_loads


@pytest.fixture(scope="class")
def populate_db(client):
    with client.application.test_request_context():
        partner1 = "Bob"
        for i in range(157):
            t = Template(partner_id=partner1, id_=str(i),
                         schema={"type": "object",
                                 "properties": {f"{i}": {"type": "string"}}
                                 },
                         type_="text/html", metadata={}, example_composition={}, tags=[])
            db.session.add(t)
        partner2 = "NotBob"
        t = Template(partner_id=partner2, id_=partner2,
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

    def test_auth_protected(self, authenticator: MockAuthenticator):
        assert self.GET_TEMPLATES_METHOD_NAME in authenticator.authenticated_endpoints

    def test_obtain_all_template_info(self, client):
        with partner_id_set(client.application, "Bob"):
            response = client.get(self.GET_TEMPLATES_ENDPOINT)
            assert response.status_code == HTTPStatus.OK
            assert len(response.json) == 157

            template_view_expected_keys = ["template_id", "template_schema", "type", "metadata", "tags"]

            for i, template_json in enumerate(response.json):
                assert all((key in template_json for key in template_view_expected_keys))
                assert i == json_loads(template_json["template_id"])
