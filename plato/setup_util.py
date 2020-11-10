import os

from plato.db.models import Template
from typing import Dict, Any
from jinja2 import Environment as JinjaEnv, FileSystemLoader, select_autoescape
import pathlib
import shutil
from smart_open import s3
from .compose import FILTERS


class SetupError(Exception):
    """
    Error for any setup Exception to occur when running this module's functions.
    """
    ...


class NoStaticContentFound(SetupError):
    """
    raised when no static content fount on S3
    """

    def __init__(self, template_id: str):
        """
        Exception initialization

        :param template_id: the id of the template
        :type template_id: string
        """
        message = f"No static content found. template_id: {template_id}"
        super(NoStaticContentFound, self).__init__(message)


class NoIndexTemplateFound(SetupError):
    """
    raised when no template found on S3
    """

    def __init__(self, template_id: str):
        """
        Exception initialization

        :param template_id: the id of the template
        :type template_id: string
        """
        message = f"No index template file found. Template_id: {template_id}"
        super(NoIndexTemplateFound, self).__init__(message)


def get_file_s3(bucket_name: str, url: str, s3_template_directory: str) -> Dict[str, Any]:
    """
    Get files from s3 and save them in the form of a dict. If a folder is inserted as the url, all files in that folder
        will be returned

    :param bucket_name: the bucket_name we want to retrieve file from
    :type bucket_name: string

    :param url: the url leading to the file/folder
    :type url: string

    :param s3_template_directory: the s3-bucket path for the templates directory
    :type s3_template_directory: string

    :return: A dictionary with key as file's relative location on s3-bucket and value as file's content
    :rtype: Dict[str, Any]
    """
    key_content_mapping: dict = {}
    for key, content in s3.iter_bucket(bucket_name=bucket_name, prefix=url):
        if key[-1] == '/' or not content:
            # Is a directory
            continue
        # based on https://www.python.org/dev/peps/pep-0616/
        new_key = key[len(s3_template_directory):]
        key_content_mapping[new_key] = content
    return key_content_mapping


def write_files(files: Dict[str, Any], target_directory: str) -> None:
    """
    Write files to a target directory
    :param files: a dict representing files needing to be written in the target directory
        with key as the file url and the value as file content
    :type files: Dict[str, Any]

    :param target_directory: the directory all the files will reside in
    :type target_directory: string
    """
    for key, content in files.items():
        path = pathlib.Path(f"{target_directory}/{key}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, mode="wb") as file:
            file.write(content)


def load_templates(s3_bucket: str, target_directory: str, s3_template_directory: str) -> None:
    """
    Gets templates from the AWS S3 bucket which are associated with ones available in the DB.
    Expected directory structure is {s3_template_directory}/{template_id}
    Args:
        s3_bucket: AWS S3 Bucket where the templates are
        target_directory: Target directory to store the templates in
        s3_template_directory: Base directory for S3 Bucket
    """
    # delete all old templates
    deleted_path = pathlib.Path(target_directory)
    if deleted_path.exists():
        shutil.rmtree(deleted_path)

    templates = Template.query.with_entities(Template.id).all()

    for template in templates:
        template_id = template.id

        static_folder = f"{s3_template_directory}/static"
        template_file = f"{s3_template_directory}/templates/{template_id}/{template_id}"

        # get static files
        static_files = get_file_s3(bucket_name=s3_bucket, url=static_folder, s3_template_directory=s3_template_directory)
        write_files(files=static_files, target_directory=target_directory)

        # get template content
        template_files = get_file_s3(bucket_name=s3_bucket, url=template_file, s3_template_directory=s3_template_directory)
        if not template_files:
            raise NoIndexTemplateFound(template_id)
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


def inside_container():
    """
    Returns true if we are running inside a container.
    Copied from testcontainers library as testcontainers are a dev dependency.

    https://github.com/docker/docker/blob/a9fa38b1edf30b23cae3eade0be48b3d4b1de14b/daemon/initlayer/setup_unix.go#L25
    """
    return os.path.exists('/.dockerenv')