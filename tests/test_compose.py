from http import HTTPStatus
from itertools import chain

import pytest
from fitz import Document
from pkg_resources import resource_filename, resource_listdir

from micro_templating.db import db
from micro_templating.db.models import Template
from tests import partner_id_set

PARTNER_1 = "test_partner"
PLAIN_TEXT_TEMPLATE_ID = "plain_text"
PNG_IMAGE_TEMPLATE_ID = "png_image"
NO_IMAGE_TEMPLATE_ID = PNG_IMAGE_TEMPLATE_ID.replace('p', 'u')
PNG_IMAGE_NAME = "balloons.png"

@pytest.fixture(scope="class")
def template_test_examples(client, template_loader):
    with client.application.test_request_context():
        plain_text_template_model = Template(partner_id=PARTNER_1, id_=PLAIN_TEXT_TEMPLATE_ID,
                                             schema={"type": "object",
                                                     "properties": {"plain": {"type": "string"}}
                                                     },
                                             type_="text/html", metadata={}, example_composition={}, tags=[])
        db.session.add(plain_text_template_model)

        plain_text_jinja_id = f"{PARTNER_1}/{PLAIN_TEXT_TEMPLATE_ID}/{PLAIN_TEXT_TEMPLATE_ID}"
        template_loader.mapping[plain_text_jinja_id] = "{{ p.plain }}"

        png_image_template_model = Template(partner_id=PARTNER_1, id_=PNG_IMAGE_TEMPLATE_ID,
                                            schema={"type": "object",
                                                    "properties": {}
                                                    },
                                            type_="text/html", metadata={}, example_composition={}, tags=[])
        db.session.add(png_image_template_model)

        png_template_jinja_id = f"{PARTNER_1}/{PNG_IMAGE_TEMPLATE_ID}/{PNG_IMAGE_TEMPLATE_ID}"
        template_loader.mapping[png_template_jinja_id] = \
            '<!DOCTYPE html>' \
            '<html>' \
            '<body>' \
            '<img id="img_" src="file://{{ template_static }}' \
            f'{PNG_IMAGE_NAME}">' \
            '</img>' \
            '</body>' \
            '</html>'

        no_image_template_model = Template(partner_id=PARTNER_1, id_=NO_IMAGE_TEMPLATE_ID,
                                           schema={"type": "object",
                                                   "properties": {}
                                                   },
                                           type_="text/html", metadata={}, example_composition={}, tags=[])
        db.session.add(no_image_template_model)
        no_image_template_jinja_id = f"{PARTNER_1}/{NO_IMAGE_TEMPLATE_ID}/{NO_IMAGE_TEMPLATE_ID}"
        template_loader.mapping[no_image_template_jinja_id] = \
            '<!DOCTYPE html>' \
            '<html>' \
            '<body>' \
            '<img id="img_" src="file://{{ template_static }}' \
            'no_img.png">' \
            '</img>' \
            '</body>' \
            '</html>'

        db.session.commit()

    yield

    with client.application.test_request_context():
        del template_loader.mapping[plain_text_jinja_id]
        del template_loader.mapping[png_template_jinja_id]
        del template_loader.mapping[no_image_template_jinja_id]
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
            assert response.status_code == HTTPStatus.CREATED
            assert response.data is not None
            pdf_document = Document(filetype="bytes", stream=response.data)
            real_text = "".join((page.getText() for page in pdf_document))
            assert real_text.strip() == expected_test

    def test_compose_image_exists(self, client):
        with partner_id_set(client.application, PARTNER_1):
            response = client.post(self.COMPOSE_ENDPOINT.format(PNG_IMAGE_TEMPLATE_ID), json={})
            assert response.data is not None
            assert response.status_code == HTTPStatus.CREATED
            pdf_document = Document(filetype="bytes", stream=response.data)
            blocks = chain.from_iterable((page.getText("dict")["blocks"] for page in pdf_document))
            images = [block["image"] for block in blocks]
            assert len(images) == 1

            response = client.post(self.COMPOSE_ENDPOINT.format(NO_IMAGE_TEMPLATE_ID), json={})
            assert response.data is not None
            assert response.status_code == HTTPStatus.CREATED
            no_image_document = Document(filetype="bytes", stream=response.data)
            blocks = chain.from_iterable((page.getText("dict")["blocks"] for page in no_image_document))
            images = [block["image"] for block in blocks]
            assert len(images) == 0


