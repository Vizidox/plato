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

load_templates(S3_BUCKET, TEMPLATE_DIRECTORY)
app.config["jinja_engine"] = create_template_environment(TEMPLATE_DIRECTORY)


@app.teardown_appcontext
def shutdown_session(exception=None):
    """

    Shuts down the session after the request is done with it

    Args:
        exception: Error raised by Flask

    Returns:
        exception: Error raise by Flask
    """
    db_session.remove()
    return exception
