from micro_templating.flask_app import create_app
from settings import WORKING_DB_URL, AUTH_SERVER, PROJECT_NAME, PROJECT_VERSION

app = create_app(project_name=PROJECT_NAME, project_version=PROJECT_VERSION,
                 db_url=WORKING_DB_URL, auth_host_url=AUTH_SERVER)

if __name__ == '__main__':
    app.run()
