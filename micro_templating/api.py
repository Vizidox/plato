from collections import Sequence
from typing import Optional

from flask import jsonify, request, current_app, g, Flask

from .auth import Authenticator
from .db.models import Template
from micro_templating.views.views import TemplateDetailView
from jinja2 import Environment as JinjaEnv


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
            required: false
        responses:
          200:
            description: Information on the template
            schema:
              $ref: '#/definitions/TemplateDetail'
          404:
            description: Template not found
        """

        template: Template = Template.query.filter_by(auth_id=g.auth_id).first()

        if template is None:
            return jsonify({"message": f"Template '{template_id}' not found"}), 404

        view = TemplateDetailView(template.id, template.schema, template.type, template.metadata_)

        return jsonify(view)

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
        """

        all_templates: Sequence[Template] = Template.query.filter_by(auth_id=g.auth_id).all()
        views = [TemplateDetailView(template.id, template.schema, template.type, template.metadata_) for template in
                 all_templates]

        return jsonify(views)
