from micro_templating.flask_app import create_app
from settings import WORKING_DB_URL, AUTH_SERVER, PROJECT_NAME, PROJECT_VERSION, SWAGGER_AUTH_CLIENT_SECRET, \
    SWAGGER_AUTH_CLIENT

app = create_app(project_name=PROJECT_NAME, project_version=PROJECT_VERSION,
                 db_url=WORKING_DB_URL, auth_host_url=AUTH_SERVER,
                 default_swagger_client=SWAGGER_AUTH_CLIENT, default_swagger_secret=SWAGGER_AUTH_CLIENT_SECRET)

if __name__ == '__main__':
    app.run()
