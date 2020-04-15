import pytest

from tests.conftest import MockAuthenticator
from micro_templating.db.models import Template
from micro_templating.db import db


@pytest.fixture(scope="class")
def populate_db(client):
    with client.application.test_request_context():
        for i in range(200):
            t = Template(partner_id="Bob", id_=str(i),
                         schema={"type": "object",
                                 "properties": {f"{i}": {"type": "string"}}
                                 },
                         type_="text/html", metadata={}, example_composition={}, tags=[])
            db.session.add(t)
        db.session.commit()

        yield

        Template.query.delete()
        db.session.commit()


@pytest.mark.usefixtures("populate_db")
class TestTemplates:

    GET_TEMPLATES_ENDPOINT = '/templates/'
    GET_TEMPLATES_METHOD_NAME = "templates"

    def test_auth_protected(self, authenticator: MockAuthenticator):
        assert self.GET_TEMPLATES_METHOD_NAME in authenticator.authenticated_endpoints

