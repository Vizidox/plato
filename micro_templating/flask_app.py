from flasgger import Swagger
from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine

from micro_templating.db.database import init_db
from micro_templating.setup_util import load_templates, create_template_environment
from settings import WORKING_DB_URL, S3_BUCKET, TEMPLATE_DIRECTORY

app = Flask(__name__)

engine = create_engine(WORKING_DB_URL, convert_unicode=True)
db_session = init_db(engine)

cors = CORS(app)
swag = Swagger(app)

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
