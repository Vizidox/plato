"""Flask app creation module.

Flask app creation is handled here by the create_app function.
Import the function wherever you decide to create a flask app.

"""
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from jinja2 import Environment as JinjaEnv
from plato.api import initialize_api
from plato.views import swag
from plato.db import db
from plato.cli import register_cli_commands


def create_app(db_url: str, template_static_directory: str,
               jinja_env: JinjaEnv, swagger_ui_config: dict) -> Flask:
    """

    Args:
        jinja_env: Jinja environment responsible for rendering the templates
        template_static_directory: The directory where the static content for the templates
        db_url: Database URI
        swagger_ui_config: The Swagger-UI config to be used with Flasgger.
         As defined in https://github.com/flasgger/flasgger#swagger-ui-and-templates

    Returns:

    """
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    Migrate(app, db)
    CORS(app)

    app.config['SWAGGER'] = swagger_ui_config
    swag.init_app(app)

    app.config["JINJENV"] = jinja_env
    app.config["TEMPLATE_STATIC"] = template_static_directory

    register_cli_commands(app)
    initialize_api(app)

    return app
