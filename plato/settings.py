import tomlkit
from os import environ, getenv
from dotenv import load_dotenv, find_dotenv

from plato.util.setup_util import inside_container

if not inside_container():
    load_dotenv(find_dotenv(), override=False)


def _get_project_meta() -> dict:
    with open(find_dotenv(filename='pyproject.toml'), mode='r') as pyproject:
        file_contents = pyproject.read()

    return tomlkit.parse(file_contents)['tool']['poetry']


__project_meta = _get_project_meta()

PROJECT_NAME = __project_meta["name"]
PROJECT_VERSION = __project_meta["version"]

ACCESS_KEY = environ["ACCESS_KEY"]

# Template storage
S3_BUCKET = environ["S3_BUCKET"]
S3_TEMPLATE_DIR = getenv("S3_TEMPLATE_DIR", "templating")
TEMPLATE_DIRECTORY = environ["TEMPLATE_DIRECTORY"]

# Database
DB_HOST = environ["DB_HOST"]
DB_PORT = environ["DB_PORT"]
DB_USERNAME = environ["DB_USERNAME"]
DB_PASSWORD = environ["DB_PASSWORD"]
DB_DATABASE = environ["DB_DATABASE"]


def db_url(database_name: str) -> str:
    return f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{database_name}'


WORKING_DB_URL = db_url(DB_DATABASE)
