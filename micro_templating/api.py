from flask import jsonify, request, g, Flask, send_file
from jsonschema import ValidationError
from sqlalchemy import String, cast as db_cast
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm.exc import NoResultFound

from micro_templating.views.views import TemplateDetailView
from .auth import Authenticator
from .compose.renderer import compose
from .db.models import Template
from .error_messages import invalid_compose_json, template_not_found


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
        try:
            mimetype = "application/pdf"
            template_model: Template = Template.query.filter_by(partner_id=g.partner_id, id=template_id).one()
            compose_data = request.get_json()
            pdf_file = compose(template_model, compose_data, mimetype)
            return send_file(pdf_file, mimetype=mimetype, as_attachment=True,
                             attachment_filename=f"compose.pdf"), 201
        except NoResultFound:
            return jsonify({"message": template_not_found.format(template_id)}), 404
        except ValidationError as ve:
            return jsonify({"message": invalid_compose_json.format(ve.message)}), 400

    @app.route("/template/<string:template_id>/example", methods=["GET"])
    @auth.token_required
    def example_compose(template_id: str):
        """
        Gets example file based on the template
        ---
        consumes:
            - application/json
        parameters:
            - name: template_id
              in: path
              type: string
              required: true
        security:
          - api_auth: [templating]
        responses:
          200:
            description: composed file
            schema:
              type: file
          404:
             description: Template not found
        tags:
           - compose
           - template
        """
        try:
            mimetype = "application/pdf"
            template_model: Template = Template.query.filter_by(partner_id=g.partner_id, id=template_id).one()
            pdf_file = compose(template_model, template_model.example_composition, mimetype)

            return send_file(pdf_file, mimetype=mimetype, as_attachment=True,
                             attachment_filename=f"{template_model.id}-example.pdf"), 200
        except NoResultFound:
            return jsonify({"message": template_not_found.format(template_id)}), 404
