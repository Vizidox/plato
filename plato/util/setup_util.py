import os

from plato.db.models import Template
from jinja2 import Environment as JinjaEnv, FileSystemLoader, select_autoescape
import pathlib
import shutil
from plato.compose import FILTERS
from .path_util import template_path, base_static_path
from .file_storage_util import write_files
from ..file_storage import PlatoFileStorage, S3FileStorage, DiskFileStorage, NoIndexTemplateFound
from .. import settings


class InvalidFileStorageTypeException(Exception):
    """
    Exception raised when attempting to initialize the File Storage with an invalid type
    """
    def __init__(self, type_: str):
        """
        Constructor method
        """
        super(InvalidFileStorageTypeException, self).__init__(type_)


def load_templates(s3_bucket: str, target_directory: str, s3_template_directory: str) -> None:
    """
    Gets templates from the AWS S3 bucket which are associated with ones available in the DB.
    Expected directory structure is {s3_template_directory}/{template_id}

    Args:
        s3_bucket: AWS S3 Bucket where the templates are
        target_directory: Target directory to store the templates in
        s3_template_directory: Base directory for S3 Bucket
    """
    old_templates_path = pathlib.Path(target_directory)
    if old_templates_path.exists():
        shutil.rmtree(old_templates_path)

    templates = Template.query.with_entities(Template.id).all()
    file_storage = S3FileStorage(settings.TEMPLATE_DIRECTORY, bucket_name=s3_bucket)
    # get static files
    static_files = file_storage.get_file(path=base_static_path(s3_template_directory),
                                         template_directory=s3_template_directory)
    write_files(files=static_files, target_directory=target_directory)

    for template in templates:
        # get template content
        template_files = file_storage.get_file(path=template_path(s3_template_directory, template.id),
                                               template_directory=s3_template_directory)
        if not template_files:
            raise NoIndexTemplateFound(template.id)
        write_files(files=template_files, target_directory=target_directory)


def create_template_environment(template_directory_path: str) -> JinjaEnv:
    """
    Setup jinja2 templating engine from a given directory path.
    Also adds all available filters to the JinjaEnv, which are available to be directly used within the template HTML files.
    Example usage of filter: {{ p.date | filter_function(args) }}

    Args:
        template_directory_path: Path to the directory where templates are stored

    Returns:
        JinjaEnv: Jinja2 Environment with templating
    """
    env = JinjaEnv(
        loader=FileSystemLoader(f"{template_directory_path}/templates"),
        autoescape=select_autoescape(["html", "xml"])
    )
    env.filters.update({filter_.__name__: filter_ for filter_ in FILTERS})
    return env


def setup_swagger_ui(project_name: str, project_version: str) -> dict:
    """
    Configurations to be used on the Swagger-ui page.

    Args:
        project_name: The project name to be displayed
        project_version: The project version to be displayed
    Returns:
        dict: The swagger ui configuration to be used with Flasgger
    """
    swagger_ui_config = {
        'title': project_name,
        'version': project_version,
        'uiversion': 3,
        'swagger': '2.0',
        'favicon': "/static/favicon-32x32.png",
        'swagger_ui_css': "/static/swagger-ui.css",
        'swagger_ui_standalone_preset_js': '/static/swagger-ui-standalone-preset.js',
        'description': ''
    }

    return swagger_ui_config


def initialize_file_storage(storage_type: str) -> PlatoFileStorage:
    """
    Initializes a correct instance of the Plato File Storage, depending on the env values

    :param storage_type: The storage type
    :type storage_type: str

    :raises InvalidFileStorageTypeException: If the given file storage type doesn't exist

    :return: An instance of FileStorage
    :rtype: class:`FileStorage`
    """
    file_storage: PlatoFileStorage
    if storage_type == "disk":
        file_storage = DiskFileStorage(settings.DATA_DIR)
    elif storage_type == 's3':
        file_storage = S3FileStorage(settings.DATA_DIR, settings.S3_BUCKET)
    else:
        raise InvalidFileStorageTypeException(storage_type)
    return file_storage


def inside_container():
    """
    Returns true if we are running inside a container.
    Copied from testcontainers library as testcontainers are a dev dependency.

    https://github.com/docker/docker/blob/a9fa38b1edf30b23cae3eade0be48b3d4b1de14b/daemon/initlayer/setup_unix.go#L25
    """
    return os.path.exists('/.dockerenv')
