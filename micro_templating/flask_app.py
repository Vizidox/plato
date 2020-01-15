"""Flask app creation module.

Flask app creation is handled here by the create_app function.
Import the function wherever you decide to create a flask app.

"""
from flasgger import Swagger
from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine

from jinja2 import Environment as JinjaEnv
from micro_templating.api import initalize_api
from micro_templating.auth import Authenticator
from micro_templating.db.database import init_db
from micro_templating.views.views import SwaggerViewCatalogue


def create_app(project_name: str, project_version: str,
               db_url: str, authenticator: Authenticator, jinja_env: JinjaEnv,
               swagger_scope: str = "templating",
               default_swagger_client: str = "", default_swagger_secret: str = "",):
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

    engine = create_engine(db_url)
    db_session = init_db(engine)

    cors = CORS(app)

    app.config['SWAGGER'] = {
        'title': project_name,
        'version': project_version,
        'uiversion': 3,
        'swagger': '2.0'
    }

    swagger_config = Swagger.DEFAULT_CONFIG
    # Used to initialize Oauth in swagger-ui as per the initOAuth method
    # https://github.com/swagger-api/swagger-ui/blob/v3.24.3/docs/usage/oauth2.md
    swagger_config['auth'] = {
        "clientId": f"{default_swagger_client}",
        "clientSecret": f"{default_swagger_secret}"
    }

    swagger_template = {
        "securityDefinitions": {
            "api_auth": {
                "type": "oauth2",
                "flow": "application",
                "tokenUrl": f"{authenticator.auth_host}/protocol/openid-connect/token",
                "scopes": {f"{swagger_scope}": "gives access to the templating engine"}
            }
        }
    }

    swag = Swagger(app, template=swagger_template, config=swagger_config)
    swag.definition_models.append(*SwaggerViewCatalogue.swagger_definitions)

    app.config["JINJENV"] = jinja_env
    app.config["AUTH"] = authenticator

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

    initalize_api(app, authenticator, jinja_env)

    return app
