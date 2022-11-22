import pathlib
from typing import Dict, Any


def write_files(files: Dict[str, Any], target_directory: str) -> None:
    """
    Write files to a target directory

    Args:
        files (Dict[str, Any]): a dict representing files needing to be written in the target directory
            with key as the file url and the value as file content
        target_directory (str): the directory all the files will reside in
    """
    for key, content in files.items():
        path = pathlib.Path(f"{target_directory}/{key}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, mode="wb") as file:
            file.write(content)
