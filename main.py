"""Main module to instantiate Flask app.

Either create a Flask run configuration on this module or set up to run it locally with main.

"""

from plato.flask_app import create_app
from plato.settings import WORKING_DB_URL, PROJECT_NAME, PROJECT_VERSION, TEMPLATE_DIRECTORY, STORAGE_TYPE, \
    S3_TEMPLATE_DIR
from plato.util.setup_util import create_template_environment, setup_swagger_ui, initialize_file_storage

template_environment = create_template_environment(TEMPLATE_DIRECTORY)
swagger_ui_config = setup_swagger_ui(PROJECT_NAME, PROJECT_VERSION)
file_storage = initialize_file_storage(STORAGE_TYPE)
app = create_app(db_url=WORKING_DB_URL,
                 template_static_directory=f"{TEMPLATE_DIRECTORY}/static",
                 jinja_env=template_environment,
                 swagger_ui_config=swagger_ui_config,
                 storage=file_storage)

if __name__ == '__main__':
    # in app-context setups
    with app.app_context():
        if STORAGE_TYPE == 's3':  # todo create enum for this
            file_storage.load_templates(TEMPLATE_DIRECTORY, S3_TEMPLATE_DIR)
    app.run()
