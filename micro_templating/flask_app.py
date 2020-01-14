from typing import Optional

import requests
from flasgger import Swagger
from flasgger.base import SwaggerDefinition
from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine

from micro_templating.api import initalize_api
from micro_templating.auth import Authenticator
from micro_templating.db.database import init_db
from micro_templating.setup_util import load_templates, create_template_environment
from micro_templating.views.views import SwaggerViewCatalogue
from settings import S3_BUCKET, TEMPLATE_DIRECTORY


def create_app(project_name: str, project_version: str,
               auth_host_url: str, db_url: str,
               default_swagger_client: str = "", default_swagger_secret: str = ""):
    app = Flask(__name__)

    engine = create_engine(db_url, convert_unicode=True)
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
                "tokenUrl": f"{auth_host_url}/protocol/openid-connect/token",
                "scopes": {"templating": "gives access to the templating engine"}
            }
        }
    }

    swag = Swagger(app, template=swagger_template, config=swagger_config)
    swag.definition_models.append(*SwaggerViewCatalogue.swagger_definitions)

    load_templates(S3_BUCKET, TEMPLATE_DIRECTORY)
    jinja_env = create_template_environment(TEMPLATE_DIRECTORY)

    authenticator = Authenticator(auth_host_url, "templating")

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
