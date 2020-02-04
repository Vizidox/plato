"""Flask app creation module.

Flask app creation is handled here by the create_app function.
Import the function wherever you decide to create a flask app.

"""
from flask import Flask
from flask_cors import CORS

from jinja2 import Environment as JinjaEnv
from micro_templating.api import initalize_api
from micro_templating.auth import Authenticator
from micro_templating.views import swag
from micro_templating.db import db
from micro_templating.cli import register_cli_commands


def create_app(project_name: str, project_version: str,
               db_url: str, authenticator: Authenticator, jinja_env: JinjaEnv,
               swagger_scope: str = "templating",
               default_swagger_client: str = "", default_swagger_secret: str = "",) -> Flask:
    """

    Args:
        jinja_env: Jinja environment responsible for rendering the templates
        authenticator: Authenticator responsible for validating tokens on API requests
        project_name: Name of the flask app
        project_version: Version of the flask app
        db_url: Database URI
        swagger_scope: Scope name be used in swagger-ui
        default_swagger_client: Default value for client in client_credentials for swagger-ui
        default_swagger_secret: Default value for secret in client_credentials for swagger-ui

    Returns:

    """
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    db.init_app(app)

    cors = CORS(app)

    app.config['SWAGGER'] = {
        'title': project_name,
        'version': project_version,
        'uiversion': 3,
        'swagger': '2.0',
        "securityDefinitions": {
            "api_auth": {
                "type": "oauth2",
                "flow": "application",
                "tokenUrl": f"{authenticator.auth_host_origin}/protocol/openid-connect/token",
                "scopes": {f"{swagger_scope}": "gives access to the templating engine"}
            }
        },
        # 'auth' configuration used to initialize Oauth in swagger-ui as per the initOAuth method
        # https://github.com/swagger-api/swagger-ui/blob/v3.24.3/docs/usage/oauth2.md
        # this is not standard flasgger behavior but it is possible because we overrode the swagger-ui templates
        "auth": {
            "clientId": f"{default_swagger_client}",
            "clientSecret": f"{default_swagger_secret}"
        }
    }

    swag.init_app(app)

    app.config["JINJENV"] = jinja_env
    app.config["AUTH"] = authenticator

    register_cli_commands(app)
    initalize_api(app, authenticator, jinja_env)

    return app
