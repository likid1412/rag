"""valid"""

import os
from loguru import logger
from fastapi import HTTPException, UploadFile, status


ALLOWED_CONTENT_TYPES = [
    "application/pdf",
    "image/tiff",
    "image/png",
    "image/jpeg",
]

ALLOWED_EXTENSIONS = {
    "application/pdf": [".pdf"],
    "image/tiff": [".tiff", ".tif"],
    "image/png": [".png"],
    "image/jpeg": [".jpeg", ".jpg"],
}


def validate_files(files: list[UploadFile]) -> None:
    """
    Validate the content type and extension of the uploaded file.

    Args:
        files (list[UploadFile]): The uploaded file list.

    Raises:
        HTTPException: If the file content type or extension is not allowed.
    """

    # TODO: should check file content format?

    file_names: set[str] = set()

    for file in files:
        logger.info(
            f"filename: {file.filename}, content_type: {file.content_type}"
        )

        # check duplicated filename
        if file.filename in file_names:
            msg = f"{file.filename} filename duplicated"
            logger.error(msg)
            raise ValueError(msg)

        file_names.add(file.filename)

        validate_file_type(file, ALLOWED_CONTENT_TYPES)
        validate_file_extension(file, ALLOWED_EXTENSIONS)


def validate_file_type(file: UploadFile, allowed_content_types: list) -> None:
    """
    Validate the content type of the uploaded file.

    Args:
        file (UploadFile): The uploaded file.
        allowed_content_types (list): List of allowed content types.

    Raises:
        HTTPException: If the file content type is not allowed.
    """
    if file.content_type not in allowed_content_types:
        # return a specific http code 415,
        # if raise ValueError, can not be catch and return in endpoint as 415
        msg = f"{file.filename} file type {file.content_type} not allowed."
        logger.error(msg)
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            msg,
        )


def validate_file_extension(file: UploadFile, allowed_extensions: dict) -> None:
    """
    Validate the file extension of the uploaded file.

    Args:
        file (UploadFile): The uploaded file.
        allowed_extensions (dict): Dictionary mapping content types to
        allowed extensions.

    Raises:
        HTTPException: If the file extension is not allowed.
    """

    split_list = os.path.splitext(file.filename)
    if len(split_list) < 2:
        msg = f"{file.filename} filename not contain extension"
        logger.error(msg)
        raise ValueError(msg)

    ext = split_list[1].lower()
    if ext not in allowed_extensions.get(file.content_type, []):
        # want to return a specific http code 415,
        # if raise ValueError, can not be catch and return in endpoint as 415
        msg = (
            f"{file.filename} file extension {ext} not allowed for"
            f" content type {file.content_type}."
        )
        logger.error(msg)
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            msg,
        )
