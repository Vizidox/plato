import os

from jinja2 import Environment as JinjaEnv, FileSystemLoader, select_autoescape
import pathlib

from smart_open import s3_iter_bucket

from .auth import FlaskAuthenticator, Authenticator


class SetupError(Exception):
    """
    Error for any setup Exception to occur when running this module's functions.
    """
    ...


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
    return FlaskAuthenticator(auth_host_url, oauth2_audience, auth_host_origin)


def load_templates(s3_bucket: str, target_directory: str):
    """
    Gets templates from the AWS S3 bucket. Assumes every file inside the bucket is a template.
    Expected directory structure is /{auth_id}/{template_id}
    Args:
        s3_bucket: AWS S3 Bucket where the templates are
        target_directory: Target directory to store the templates in
    """
    try:
        for key, content in s3_iter_bucket(s3_bucket):
            if key[-1] == '/' or not content:
                # Is a directory
                continue

            path = pathlib.Path(f"{target_directory}/{key}")
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, mode="wb") as file:
                file.write(content)
    except Exception as e:
        raise SetupError(e, "Unable to obtain templates from S3")


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


def setup_jinja_environment(s3_bucket: str, target_directory: str) -> JinjaEnv:
    """
    Obtains the templates from the S3 bucket and makes them available as part of the JinjaEnv

    Args:
        s3_bucket: string representing which bucket is to be accessed
        target_directory: path to the directory where the templates should be stored

    Returns:
        JinjaEnv: environment loaded for target_directory with all templates from bucket
    """
    load_templates(s3_bucket, target_directory)
    return create_template_environment(f"{target_directory}/templates")


def setup_swagger_ui(project_name: str, project_version: str,
                     auth_host_origin: str, swagger_scope: str,
                     default_swagger_client: str = "", default_swagger_secret: str = "") -> dict:
    swagger_ui_config = {
        'title': project_name,
        'version': project_version,
        'uiversion': 3,
        'swagger': '2.0',
        'favicon': "/static/favicon-32x32.png",
        'swagger_ui_css': "/static/swagger-ui.css",
        'swagger_ui_standalone_preset_js': '/static/swagger-ui-standalone-preset.js',
        'description': '',
        "securityDefinitions": {
            "api_auth": {
                "type": "oauth2",
                "flow": "application",
                "tokenUrl": f"{auth_host_origin}/protocol/openid-connect/token",
                "scopes": {f"{swagger_scope}": "gives access to the templating engine"}
            }
        },
        # 'auth' configuration used to initialize Oauth in swagger-ui as per the initOAuth method
        # https://github.com/swagger-api/swagger-ui/blob/v3.24.3/docs/usage/oauth2.md
        # this is not standard flasgger behavior but it is possible because we overrode the swagger-ui templates
        "auth": {
            "clientId": f"{default_swagger_client}",
            "clientSecret": f"{default_swagger_secret}"
        }
    }

    return swagger_ui_config

def inside_container():
    """
    Returns true if we are running inside a container.
    Copied from testcontainers library as testcontainers are a dev dependency.

    https://github.com/docker/docker/blob/a9fa38b1edf30b23cae3eade0be48b3d4b1de14b/daemon/initlayer/setup_unix.go#L25
    """
    return os.path.exists('/.dockerenv')
