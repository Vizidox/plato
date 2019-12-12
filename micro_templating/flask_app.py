from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from sqlalchemy import create_engine
from micro_templating.db.database import init_db
from settings import WORKING_DB_URL

app = Flask(__name__)

engine = create_engine(WORKING_DB_URL, convert_unicode=True)
db_session = init_db(engine)

cors = CORS(app)
swag = Swagger(app)


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
