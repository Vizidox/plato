from collections import Sequence

from flask import jsonify, request, g, Flask, send_file
from jsonschema import ValidationError

from .error_messages import invalid_compose_json, template_not_found
from .compose.types import VDXSchemaValidator
from .compose.renderer import PdfRenderer
from .auth import Authenticator
from .db.models import Template
from micro_templating.views.views import TemplateDetailView
from .settings import TEMPLATE_DIRECTORY


def initalize_api(app: Flask, auth: Authenticator):

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

        template: Template = Template.query.filter_by(partner_id=g.partner_id, id=template_id).first()

        if template is None:
            return jsonify({"message": template_not_found.format(template_id)}), 404

        view = TemplateDetailView.view_from_template(template)

        return jsonify(view._asdict())

    @app.route("/templates/", methods=['GET'])
    @auth.token_required
    def templates():
        """
        Returns template information
        ---
        security:
          - api_auth: [templating]
        responses:
          200:
            description: Information on all templates available
            type: array
            items:
                $ref: '#/definitions/TemplateDetail'
        tags:
           - template
        """

        all_templates: Sequence[Template] = Template.query.filter_by(partner_id=g.partner_id).all()
        json_views = [TemplateDetailView.view_from_template(template)._asdict() for
                      template in
                      all_templates]

        return jsonify(json_views)

    @app.route("/template/<string:template_id>/compose", methods=["POST"])
    @auth.token_required
    def compose_file(template_id: str):
        """
        Composes file based on the template
        ---
        consumes:
            - application/json
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
        tags:
           - compose
           - template
        """
        template_model: Template = Template.query.filter_by(partner_id=g.partner_id, id=template_id).first()

        if template_model is None:
            return jsonify({"message": template_not_found.format(template_id)}), 404

        compose_data = request.get_json()
        try:
            validator = VDXSchemaValidator(template_model.schema)
            validator.validate(compose_data)
        except ValidationError as ve:
            return jsonify({"message": invalid_compose_json.format(ve.message)}), 400

        partner_static_folder = f"{TEMPLATE_DIRECTORY}/static/{g.partner_id}/"
        template_static_folder = f"{TEMPLATE_DIRECTORY}/static/{g.partner_id}/{template_id}/"

        renderer = PdfRenderer(
            template_model=template_model,
            compose_data=compose_data,
            partner_static_directory=partner_static_folder,
            template_static_directory=template_static_folder
        )

        return send_file(renderer.render(), mimetype=renderer.mime_type(), as_attachment=True,
                         attachment_filename=f"compose{renderer.file_extension()}"), 201
