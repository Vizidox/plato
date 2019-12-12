import pathlib
from flasgger import Swagger
from flask import Flask
from flask_cors import CORS
from smart_open import s3_iter_bucket
from sqlalchemy import create_engine

from micro_templating.db.database import init_db
from settings import WORKING_DB_URL, S3_BUCKET

app = Flask(__name__)

engine = create_engine(WORKING_DB_URL, convert_unicode=True)
db_session = init_db(engine)

cors = CORS(app)
swag = Swagger(app)


def load_templates(s3_bucket: str, target_directory: str):
    """
    Gets templates from the AWS S3 bucket
    Args:
        s3_bucket: AWS S3 Bucket where the templates are
        target_directory: Target directory to store the templates in
    """
    for key, content in s3_iter_bucket(s3_bucket):
        if key[-1] == '/' or not content:
            # Is a directory
            continue

        path = pathlib.Path(f"{target_directory}/{key}")
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, mode="wb") as file:
            file.write(content)


load_templates(S3_BUCKET, "templates")


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
