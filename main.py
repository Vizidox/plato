"""Main module to instantiate Flask app.

Either create a Flask run configuration on this module or set up to run it locally with main.

"""

from micro_templating.flask_app import create_app
from micro_templating.settings import WORKING_DB_URL, AUTH_SERVER, PROJECT_NAME, PROJECT_VERSION,\
    SWAGGER_AUTH_CLIENT_SECRET, SWAGGER_AUTH_CLIENT, CLIENT_ID, SWAGGER_AUTH_SCOPE, S3_BUCKET, TEMPLATE_DIRECTORY,\
    AUTH_SERVER_ORIGIN
from micro_templating.setup_util import setup_authenticator, setup_jinja_environment, setup_swagger_ui

authenticator = setup_authenticator(AUTH_SERVER, CLIENT_ID, AUTH_SERVER_ORIGIN)
template_environment = setup_jinja_environment(S3_BUCKET, TEMPLATE_DIRECTORY)
swagger_ui_config = setup_swagger_ui(PROJECT_NAME, PROJECT_VERSION,
                                     AUTH_SERVER_ORIGIN,
                                     SWAGGER_AUTH_SCOPE,
                                     default_swagger_client=SWAGGER_AUTH_CLIENT,
                                     default_swagger_secret=SWAGGER_AUTH_CLIENT_SECRET)
app = create_app(db_url=WORKING_DB_URL,
                 authenticator=authenticator,
                 jinja_env=template_environment,
                 swagger_ui_config=swagger_ui_config
                 )

if __name__ == '__main__':
    app.run()
