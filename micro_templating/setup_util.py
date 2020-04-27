import os

from micro_templating.db.models import Template
from typing import Dict, Any
from jinja2 import Environment as JinjaEnv, FileSystemLoader, select_autoescape
import pathlib
import shutil
import smart_open

from .auth import Authenticator

class SetupError(Exception):
    """
    Error for any setup Exception to occur when running this module's functions.
    """
    ...


class NoStaticContentFound(SetupError):
    """
    raised when no static content fount on S3
    """
    def __init__(self, partner_id: str, template_id: str):
        """
        Exception initialization

        :param partner_id: the id of the partner
        :type partner_id: string

        :param template_id: the id of the template
        :type template_id: string
        """
        message = f"No static content found. partner_id: {partner_id}, template_id: {template_id}"
        super(NoStaticContentFound, self).__init__(message)

class NoIndexTemplateFound(SetupError):
    """
    raised when no template found on S3
    """
    def __init__(self, partner_id: str, template_id: str):
        """
        Exception initialization

        :param partner_id: the id of the partner
        :type partner_id: string

        :param template_id: the id of the template
        :type template_id: string
        """
        message = f"No index template file found. partner_id: {partner_id}, template_id: {template_id}"
        super(NoIndexTemplateFound, self).__init__(message)


def setup_authenticator(auth_host_url: str, oauth2_audience: str, auth_host_origin: str = "") -> Authenticator:
    """
    Convenience method to setup the authenticator to gather all setup functions in one module.

    Args:
        auth_host_url: url for keycloak host e.g https://keycloak.org/auth/realms/vizidox/
        auth_host_origin: the url keycloak signs with, defaults to auth_host_url
        oauth2_audience: audience for JWT token validation

    Returns:
        Authenticator: authenticator be used for token validation
    """
    return Authenticator(auth_host_url, oauth2_audience, auth_host_origin)

def get_file_s3(bucket_name: str, url: str) -> Dict[str, Any]:
    """
    get files from s3 and save them in the form of a dict. If a folder is inserted as the url, all files in that folder
        will be returned

    :param bucket_name: the bucket_name we want to retrieve file from
    :type bucket_name: string

    :param url: the url leading to the file/folder
    :type url: string

    :return: A dictionary with key as file's location on s3-bucket and value as file's content
    :rtype: Dict[str, Any]
    """
    key_content_mapping: dict = {}
    for key, content in smart_open.s3_iter_bucket(bucket_name=bucket_name, prefix=url):
        if key[-1] == '/' or not content:
            # Is a directory
            continue
        key_content_mapping[key] = content
    return key_content_mapping

def load_templates(s3_bucket: str, target_directory: str) -> None:
    """
    Gets templates from the AWS S3 bucket which are associated with ones available in the DB.
    Expected directory structure is /{auth_id}/{template_id}
    Args:
        s3_bucket: AWS S3 Bucket where the templates are
        target_directory: Target directory to store the templates in
    """
    # delete all old templates
    deleted_path = pathlib.Path(target_directory)
    if deleted_path.exists():
        shutil.rmtree(deleted_path)

    templates: Template = Template.query.all()

    for template in templates:
        partner_id = str(template.partner_id)
        template_id = str(template.id)

        static_folder = f"static/{partner_id}/{template_id}"
        template_file = f"templates/{partner_id}/{template_id}/{template_id}1"

        file_urls = [static_folder, template_file]

        for file_url in file_urls:
            data_files = get_file_s3(bucket_name=s3_bucket, url=file_url)

            if not data_files:
                if file_url == static_folder:
                    raise NoStaticContentFound(partner_id, template_id)
                else:
                    raise NoIndexTemplateFound(partner_id, template_id)

            for key, content in data_files.items():
                path = pathlib.Path(f"{target_directory}/{key}")
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, mode="wb") as file:
                    file.write(content)

def create_template_environment(template_directory_path: str) -> JinjaEnv:
    """
    Setup jinja2 templating engine from a given directory path.

    Args:
        template_directory_path: Path to the directory where templates are stored

    Returns:
        JinjaEnv: Jinja2 Environment with templating
    """
    env = JinjaEnv(
        loader=FileSystemLoader(template_directory_path),
        autoescape=select_autoescape(["html", "xml"])
    )

    return env


def inside_container():
    """
    Returns true if we are running inside a container.
    Copied from testcontainers library as testcontainers are a dev dependency.

    https://github.com/docker/docker/blob/a9fa38b1edf30b23cae3eade0be48b3d4b1de14b/daemon/initlayer/setup_unix.go#L25
    """
    return os.path.exists('/.dockerenv')
