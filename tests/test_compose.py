import io
from http import HTTPStatus
from itertools import chain
from PIL import Image
from math import isclose
import pytest
from fitz import Document

from micro_templating.compose import ALL_AVAILABLE_MIME_TYPES
from micro_templating.db import db
from micro_templating.db.models import Template
from micro_templating.error_messages import aspect_ratio_compromised, resizing_unsupported, unsupported_mime_type
from tests import partner_id_set, get_message

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
                                             type_="text/html", metadata={},
                                             example_composition={"plain": "plain_example"}, tags=[])
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

    EXAMPLE_COMPOSE_ENDPOINT = "/template/{0}/example"
    EXAMPLE_COMPOSE_METHOD_NAME = "example_compose"

    def test_compose_plain_ok(self, client):
        with partner_id_set(client.application, PARTNER_1):
            expected_text = "This is some plain text"
            json_request = {"plain": expected_text}
            response = client.post(self.COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID), json=json_request)
            assert response.status_code == HTTPStatus.OK
            assert response.data is not None
            pdf_document = Document(filetype="bytes", stream=response.data)
            real_text = "".join((page.getText() for page in pdf_document))
            assert real_text.strip() == expected_text

    def test_compose_image_exists(self, client):
        with partner_id_set(client.application, PARTNER_1):
            def get_images_from_template(template_id: str):
                response = client.post(self.COMPOSE_ENDPOINT.format(template_id), json={})
                assert response.data is not None
                assert response.status_code == HTTPStatus.OK
                pdf_document = Document(filetype="bytes", stream=response.data)
                blocks = chain.from_iterable((page.getText("dict")["blocks"] for page in pdf_document))
                return [block["image"] for block in blocks]

            images = get_images_from_template(PNG_IMAGE_TEMPLATE_ID)
            assert len(images) == 1

            images = get_images_from_template(NO_IMAGE_TEMPLATE_ID)
            assert len(images) == 0

    def test_example_ok(self, client):
        with client.application.app_context():
            test_template = Template.query.filter_by(partner_id=PARTNER_1, id=PLAIN_TEXT_TEMPLATE_ID).one()
            expected_text = test_template.example_composition["plain"]

        with partner_id_set(client.application, PARTNER_1):
            response = client.get(self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID))
            assert response.status_code == HTTPStatus.OK
            assert response.data is not None
            pdf_document = Document(filetype="bytes", stream=response.data)
            real_text = "".join((page.getText() for page in pdf_document))
            assert real_text.strip() == expected_text

    def test_resize_ok(self, client):
        error = 1
        expected_resize = 200
        with partner_id_set(client.application, PARTNER_1):
            response = client.get(
                f"{self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID)}",
                headers={"accept": "image/png"}
            )
            assert response.status_code == HTTPStatus.OK
            assert response.data is not None
            with Image.open(io.BytesIO(response.data)) as img:
                width, height = img.size

            expected_resolution = height / width
            assert height != expected_resize
            assert width != expected_resize

            response = client.get(
                f"{self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID)}?width={expected_resize}",
                headers={"accept": "image/png"}
            )

            def maintains_aspect_ratio(response):
                assert response.status_code == HTTPStatus.OK
                assert response.data is not None
                with Image.open(io.BytesIO(response.data)) as img_:
                    width_, height_ = img_.size
                real_resolution = height_ / width_
                assert isclose(expected_resolution, real_resolution, abs_tol=error / 10)
                return width_, height_

            real_width, _ = maintains_aspect_ratio(response)
            assert isclose(expected_resize, real_width, abs_tol=error)

            response = client.get(
                f"{self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID)}?height={expected_resize}",
                headers={"accept": "image/png"}
            )

            _, real_height = maintains_aspect_ratio(response)
            assert isclose(expected_resize, real_height, abs_tol=error)

    def test_resize_nok(self, client):
        intended_resize = 200

        response = client.get(
            f"{self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID)}"
            f"?width={intended_resize}&height={intended_resize}",
            headers={"accept": "image/png"}
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert get_message(response) == aspect_ratio_compromised

        pdf_mimetype = "application/pdf"

        response = client.get(
            f"{self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID)}"
            f"?width={intended_resize}",
            headers={"accept": pdf_mimetype}
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert get_message(response) == resizing_unsupported.format(pdf_mimetype)

    def test_unsupported_mimetype(self, client):
        jpeg_mimetype = "image/jpeg"

        response = client.get(
            f"{self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID)}",
            headers={"accept": jpeg_mimetype}
        )

        assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
        assert get_message(response) == unsupported_mime_type.format(jpeg_mimetype, ", ".join(ALL_AVAILABLE_MIME_TYPES))
