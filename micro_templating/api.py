from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger
from sqlalchemy import create_engine

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'Template API',
    'uiversion': 3,
    'openapi': '3.0.2'
}

cors = CORS(app)
swagger = Swagger(app)

engine = create_engine(db_url)
app.config['database'] = db


@app.route("/templates/<string:template_id>/", methods=["GET"])
def template(template_id: str):
    """
    Returns template information
    ---
    parameters: template_id:
        -   in: path
            name: template_id
            type: string
            required: true
    responses:
        200:
            description: The template details.
            schema:
                $ref: '#/definitions/TemplateDetail':
    """

    template = None

    return jsonify(template)