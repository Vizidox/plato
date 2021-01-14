

def compute_s3_template_path(s3_template_dir: str, template_id: str) -> str:
    """
        Returns a S3 Bucket Path for a certain template
    """
    return f"{s3_template_dir}/templates/{template_id}/{template_id}"


def compute_s3_static_path(s3_template_dir: str, template_id: str, static_file: str) -> str:
    """
        Returns a S3 Bucket Path for the static content of a certain template
    """
    return f"{s3_template_dir}/static/{template_id}/{static_file}"


def compute_s3_base_static_path(s3_template_dir: str) -> str:
    """
        Returns a S3 Bucket Path for the static content
    """
    return f"{s3_template_dir}/static"


def compute_tmp_template_path(zip_file_name: str, template_id: str) -> str:
    """
        Returns the tmp path for the content of a certain template
    """
    return f"/tmp/{zip_file_name}/templates/{template_id}/{template_id}"


def compute_tmp_static_path(zip_file_name: str, template_id: str, static_file: str) -> str:
    """
        Returns the tmp path for the static content of a certain template
    """
    return f"/tmp/{zip_file_name}/static/{template_id}/{static_file}"


