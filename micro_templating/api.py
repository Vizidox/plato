from flask import jsonify, request
from .flask_app import app
from .views.template import TemplateDetailView

@app.route("/template/{string:template_id}", methods=['GET'])
def template():
    """
    Returns template information
    ---
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

    view = TemplateDetailView("template_example", {"schema": {}}, "text/html", {})

    return jsonify(**view._asdict())


if __name__ == "__main__":
    app.run(debug=True)
