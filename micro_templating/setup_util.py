from jinja2 import Environment, FileSystemLoader, select_autoescape
import pathlib

from smart_open import s3_iter_bucket


def load_templates(s3_bucket: str, target_directory: str):
    """
    Gets templates from the AWS S3 bucket. Assumes every file inside the bucket is a template.
    Expected directory structure is /{auth_id}/{template_id}
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


def create_template_environment(template_directory_path: str) -> Environment:
    """
    Setup jinja2 templating engine from

    Args:
        template_directory_path: Path to the directory where templates are stored

    Returns:
        Environment: Jinja2 Environment with templating
    """
    env = Environment(
        loader=FileSystemLoader(template_directory_path),
        autoescape=select_autoescape(["html", "xml"])
    )

    return env
