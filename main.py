"""Main module to instantiate Flask app.

Either create a Flask run configuration on this module or set up to run it locally with main.

"""

from micro_templating.flask_app import create_app
from micro_templating.settings import WORKING_DB_URL, AUTH_SERVER, PROJECT_NAME, PROJECT_VERSION,\
    SWAGGER_AUTH_CLIENT_SECRET, SWAGGER_AUTH_CLIENT, CLIENT_ID, SWAGGER_AUTH_SCOPE, S3_BUCKET, TEMPLATE_DIRECTORY
from micro_templating.setup_util import setup_authenticator, setup_jinja_environment

authenticator = setup_authenticator(AUTH_SERVER, CLIENT_ID)
template_environment = setup_jinja_environment(S3_BUCKET, TEMPLATE_DIRECTORY)
app = create_app(project_name=PROJECT_NAME, project_version=PROJECT_VERSION,
                 db_url=WORKING_DB_URL,
                 authenticator=authenticator,
                 jinja_env=template_environment,
                 swagger_scope=SWAGGER_AUTH_SCOPE,
                 default_swagger_client=SWAGGER_AUTH_CLIENT, default_swagger_secret=SWAGGER_AUTH_CLIENT_SECRET)

if __name__ == '__main__':
    app.run()
