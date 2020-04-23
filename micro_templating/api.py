from flask import jsonify, request, g, Flask, send_file
from jsonschema import ValidationError
from sqlalchemy import String, cast as db_cast
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm.exc import NoResultFound

from micro_templating.compose import PDF_MIME, ALL_AVAILABLE_MIME_TYPES
from micro_templating.compose.renderer import compose, RendererNotFound
from micro_templating.views.views import TemplateDetailView
from mimetypes import guess_extension
from .auth import Authenticator
from .db.models import Template
from .error_messages import invalid_compose_json, template_not_found, unsupported_mime_type, aspect_ratio_compromised, \
    resizing_unsupported
from accept_types import get_best_match


class UnsupportedMIMEType(Exception):
    """
    Exception to be raised when the mime type requested is not supported
    """
    ...


def initialize_api(app: Flask, auth: Authenticator):
    """
    Initializes Flask app with the microservice endpoints.

    Args:
        app: The Flask app
        auth: The authenticator to provide security on the endpoints.

    Returns:

    """
    @app.route("/templates/<string:template_id>", methods=['GET'])
    @auth.token_required
    def template_by_id(template_id: str):
        """
        Returns template information
        ---
        security:
          - api_auth: [templating]
        parameters:
          - name: template_id
            in: path
            type: string
            required: true
        responses:
          200:
            description: Information on the template
            schema:
              $ref: '#/definitions/TemplateDetail'
          404:
            description: Template not found
        tags:
           - template
        """
        try:

            template: Template = Template.query.filter_by(partner_id=g.partner_id, id=template_id).one()
            view = TemplateDetailView.view_from_template(template)
            return jsonify(view._asdict())

        except NoResultFound:
            return jsonify({"message": template_not_found.format(template_id)}), 404

    @app.route("/templates/", methods=['GET'])
    @auth.token_required
    def templates():
        """
        Returns template information
        ---
        security:
          - api_auth: [templating]
        parameters:
          - in: query
            name: tags
            type: array
            items:
                type: string
        responses:
          200:
            description: Information on all templates available
            type: array
            items:
                $ref: '#/definitions/TemplateDetail'
        tags:
           - template
        """

        tags = request.args.getlist("tags", type=str)

        template_query = Template.query.filter_by(partner_id=g.partner_id)
        if tags:
            template_query = template_query.filter(Template.tags.contains(db_cast(tags, ARRAY(String))))

        json_views = [TemplateDetailView.view_from_template(template)._asdict() for
                      template in
                      template_query]

        return jsonify(json_views)

    @app.route("/template/<string:template_id>/compose", methods=["POST"])
    @auth.token_required
    def compose_file(template_id: str):
        """
        Composes file based on the template
        ---
        consumes:
            - application/json
        produces:
            - application/pdf
            - image/png
        parameters:
            - name: template_id
              in: path
              type: string
              required: true
            - in: body
              name: schema
              description: body to compose file with, must be according to the template schema
              schema:
                type: object
            - in: header
              name: accept
              required: false
              type: string
              enum: [application/pdf, image/png]
              description: MIME type(s) to determine what kind of file is outputted
            - in: query
              name: height
              required: false
              type: integer
              description: Intended height for image output
            - in: query
              name: width
              required: false
              type: integer
              description: Intended width for image output
        security:
          - api_auth: [templating]
        responses:
          201:
            description: composed file
            schema:
              type: file
          400:
            description: Invalid compose data for template schema
          404:
             description: Template not found
          406:
             description: Unsupported MIME type for file
        tags:
           - compose
           - template
        """
        return _compose(template_id, lambda t: request.get_json())

    @app.route("/template/<string:template_id>/example", methods=["GET"])
    @auth.token_required
    def example_compose(template_id: str):
        """
        Gets example file based on the template
        ---
        consumes:
            - application/json
        produces:
            - application/pdf
            - image/png
        parameters:
            - name: template_id
              in: path
              type: string
              required: true
            - in: header
              name: accept
              required: false
              type: string
              enum: [application/pdf, image/png]
            - in: query
              name: height
              required: false
              type: integer
              description: Intended height for image output
            - in: query
              name: width
              required: false
              type: integer
              description: Intended width for image output
        security:
          - api_auth: [templating]
        responses:
          200:
            description: composed file
            schema:
              type: file
          404:
             description: Template not found
          406:
             description: Unsupported MIME type for file
        tags:
           - compose
           - template
        """
        return _compose(template_id, lambda t: t.example_composition)

    def _compose(template_id: str, compose_retrieval_function):
        width = request.args.get("width", type=int)
        height = request.args.get("height", type=int)

        accept_header = request.headers.get("Accept", PDF_MIME)
        mime_type = get_best_match(accept_header, ALL_AVAILABLE_MIME_TYPES)

        try:
            if mime_type is None:
                raise UnsupportedMIMEType(accept_header)

            if width is not None and height is not None:
                return jsonify({"message": aspect_ratio_compromised}), 400

            if (width is not None or height is not None) and mime_type == PDF_MIME:
                return jsonify({"message": resizing_unsupported.format(mime_type)}), 400

            template_model: Template = Template.query.filter_by(partner_id=g.partner_id, id=template_id).one()
            compose_data = compose_retrieval_function(template_model)
            composed_file = compose(template_model, compose_data, mime_type)
            return send_file(composed_file, mimetype=mime_type, as_attachment=True,
                             attachment_filename=f"compose{guess_extension(mime_type)}"), 201
        except (RendererNotFound, UnsupportedMIMEType):
            return jsonify(
                {"message": unsupported_mime_type.format(accept_header, ", ".join(ALL_AVAILABLE_MIME_TYPES))}), 406
        except NoResultFound:
            return jsonify({"message": template_not_found.format(template_id)}), 404
        except ValidationError as ve:
            return jsonify({"message": invalid_compose_json.format(ve.message)}), 400
