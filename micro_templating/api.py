from flask import jsonify, request, current_app, g
from micro_templating.views.views import TemplateDetailView


def initalize_api(app, auth, jinjaenv):

    @app.route("/templates/<string:template_id>", methods=['GET'])
    @auth.token_required
    def template(template_id: str):
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
        """
        # env = jinjaenv
        # all_templates: Sequence[Template] = Template.query.filter(Template. == )

        view = TemplateDetailView(f"{g.auth_id}template_example", {"schema": {}}, "text/html", {})

        return jsonify(**view._asdict())



