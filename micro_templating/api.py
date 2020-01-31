import io
import tempfile
from collections import Sequence

from flask import jsonify, request, g, Flask, send_file
from jsonschema import validate as json_validate, ValidationError
from weasyprint import HTML, CSS

from error_messages import invalid_compose_json, template_not_found
from .auth import Authenticator
from .db.models import Template
from micro_templating.views.views import TemplateDetailView
from jinja2 import Environment as JinjaEnv
from settings import TEMPLATE_DIRECTORY


def initalize_api(app: Flask, auth: Authenticator, jinjaenv: JinjaEnv):

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

        view = TemplateDetailView(template.id, template.schema, template.type, template.metadata_)

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
        json_views = [TemplateDetailView(template.id, template.schema, template.type, template.metadata_)._asdict() for
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
            json_validate(compose_data, template_model.schema)
        except ValidationError as ve:
            return jsonify({"message": invalid_compose_json.format(ve.message)}), 400

        template = jinjaenv.get_template(
            name=f"{g.partner_id}/{template_id}/{template_id}"
        )  # template id works for the file as well

        composed_html = template.render(
            p=compose_data,
            partner_static=f"{TEMPLATE_DIRECTORY}/static/{g.partner_id}/",
            template_static=f"{TEMPLATE_DIRECTORY}/static/{g.partner_id}/{template_id}/"
        )

        with tempfile.NamedTemporaryFile() as target_file_html:
            html = HTML(string=composed_html)
            html.write_pdf(target_file_html.name)
            with open(target_file_html.name, mode='rb') as temp_file_stream:
                return send_file(io.BytesIO(temp_file_stream.read()), mimetype='application/pdf', as_attachment=True,
                                 attachment_filename="compose.pdf"), 201
