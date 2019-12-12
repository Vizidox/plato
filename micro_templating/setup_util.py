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