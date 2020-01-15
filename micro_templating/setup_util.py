from jinja2 import Environment as JinjaEnv, FileSystemLoader, select_autoescape
import pathlib

from smart_open import s3_iter_bucket

from auth import Authenticator


class SetupError(Exception):
    """
    Error for any setup Exception to occur when running this module's functions.
    """
    ...


def setup_authenticator(auth_host_url: str, oauth2_audience: str) -> Authenticator:
    return Authenticator(auth_host_url, oauth2_audience)


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
    load_templates(s3_bucket, target_directory)
    return create_template_environment(target_directory)
