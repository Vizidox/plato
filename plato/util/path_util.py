

def s3_template_path(s3_template_dir: str, template_id: str) -> str:
    """
        Returns a S3 Bucket Path for a certain template
    """
    return f"{s3_template_dir}/templates/{template_id}/{template_id}"


def s3_static_file_path(s3_template_dir: str, template_id: str, static_file: str) -> str:
    """
        Returns a S3 Bucket Path for a static file of a certain template
    """
    return f"{s3_base_static_path(s3_template_dir)}/{template_id}/{static_file}"


def s3_static_path(s3_template_dir: str, template_id: str) -> str:
    """
        Returns a S3 Bucket Path for a static file of a certain template
    """
    return f"{s3_base_static_path(s3_template_dir)}/{template_id}"


def s3_base_static_path(s3_template_dir: str) -> str:
    """
        Returns the S3 Bucket Base Path for the static content
    """
    return f"{s3_template_dir}/static"


def tmp_template_path(zip_file_name: str, template_id: str) -> str:
    """
        Returns the tmp path for the content of a certain template
    """
    return f"{tmp_path(zip_file_name)}/templates/{template_id}/{template_id}"


def tmp_static_file_path(zip_file_name: str, template_id: str, static_file: str) -> str:
    """
        Returns the tmp path for a static file of a certain template
    """
    return f"{tmp_path(zip_file_name)}/static/{template_id}/{static_file}"


def tmp_template_static_path(zip_file_name: str, template_id: str) -> str:
    """
        Returns the tmp path for the static content of a certain template
    """
    return f"{tmp_path(zip_file_name)}/static/{template_id}"


def tmp_path(file_name: str) -> str:
    """
        Returns the tmp path where the file (without its extension) can be stored
    """
    return f"/tmp/{file_name}"


def tmp_zipfile_path(zip_file_name: str) -> str:
    """
        Returns the tmp path where the zip file is going to be stored
    """
    return f"{tmp_path(zip_file_name)}.zip"
