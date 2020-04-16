import io

import pytest
from fitz import Document
from micro_templating.db import db
from micro_templating.db.models import Template
from tests import partner_id_set

PARTNER_1 = "test_partner"
PLAIN_TEXT_TEMPLATE_ID = "plain_text"


@pytest.fixture(scope="class")
def template_test_examples(client, template_loader):
    with client.application.test_request_context():
        plain_text_template_model = Template(partner_id=PARTNER_1, id_=PLAIN_TEXT_TEMPLATE_ID,
                                             schema={"type": "object",
                                                     "properties": {"plain": {"type": "string"}}
                                                     },
                                             type_="text/html", metadata={}, example_composition={}, tags=[])
        db.session.add(plain_text_template_model)
        template_loader.mapping[f"{PARTNER_1}/{PLAIN_TEXT_TEMPLATE_ID}/{PLAIN_TEXT_TEMPLATE_ID}"] = "{{ p.plain }}"
        db.session.commit()

    yield

    with client.application.test_request_context():

        Template.query.delete()
        db.session.commit()


@pytest.mark.usefixtures("template_test_examples")
class TestCompose:

    COMPOSE_ENDPOINT = "/template/{0}/compose"
    COMPOSE_METHOD_NAME = "compose_file"

    def test_compose_plain_ok(self, client):
        with partner_id_set(client.application, PARTNER_1):
            expected_test = "This is some plain text"
            json_request = {"plain": expected_test}
            response = client.post(self.COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID), json=json_request)
            assert response.data is not None
            pdf_document = Document(filetype="bytes", stream=response.data)
            real_text = "".join((page.getText() for page in pdf_document))
            assert real_text.strip() == expected_test
