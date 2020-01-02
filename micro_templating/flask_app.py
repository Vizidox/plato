from flasgger import Swagger
from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine
from micro_templating.db.database import init_db
from micro_templating.setup_util import load_templates, create_template_environment
from settings import WORKING_DB_URL, S3_BUCKET, TEMPLATE_DIRECTORY, AUTH_SERVER, PROJECT_NAME, PROJECT_VERSION

app = Flask(__name__)

swagger_config = Swagger.DEFAULT_CONFIG
app.config['SWAGGER'] = {
    'title': PROJECT_NAME,
    'version': PROJECT_VERSION,
    'uiversion': 3,
    'swagger': '2.0'
}

engine = create_engine(WORKING_DB_URL, convert_unicode=True)
db_session = init_db(engine)

cors = CORS(app)

swagger_template = {
    "openapi": "3.0",
    'uiversion': "3",
    "info": {
        "title": PROJECT_NAME,
        "version": PROJECT_VERSION
    },
    "securityDefinitions": {
        "api_auth": {
            "type": "oauth2",
            "flow": "application",
            "tokenUrl": f"{AUTH_SERVER}/protocol/openid-connect/token",
            "scopes": {"templating": "gives access to the templating engine"}
        }
    }
}

swag = Swagger(app, template=swagger_template, config=swagger_config)

jinja_config_key = "JINJA_TEMPLATE_ENGINE"

load_templates(S3_BUCKET, TEMPLATE_DIRECTORY)
app.config[jinja_config_key] = create_template_environment(TEMPLATE_DIRECTORY)


def get_template_engine(current_app):
    """
    Obtains the template engine for the current flask app

    Args:
        current_app: Current flask app

    Returns:
        Environment: Jinja2 Environment with templating
    """
    return current_app.config[jinja_config_key]


@app.teardown_appcontext
def shutdown_session(exception=None):
    """

    Shuts down the session after the request is done with it

    Args:
        exception: Error raised by Flask

    Returns:
        exception: Error raised by Flask
    """
    db_session.remove()
    return exception
