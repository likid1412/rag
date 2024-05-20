import os
from http import HTTPStatus
from fastapi import HTTPException, UploadFile


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


def validate_files(
    files: list[UploadFile],
    allowed_content_types: list = ALLOWED_CONTENT_TYPES,
    allowed_extensions: dict = ALLOWED_EXTENSIONS,
) -> None:
    """
    Validate the content type and extension of the uploaded file.

    Args:
        files (list[UploadFile]): The uploaded file list.
        allowed_content_types (list): List of allowed content types.
        default using ALLOWED_CONTENT_TYPES
        allowed_extensions (dict): Dictionary mapping content types to
        allowed extensions. default using ALLOWED_EXTENSIONS

    Raises:
        HTTPException: If the file content type or extension is not allowed.
    """

    # TODO: should check file format?

    for file in files:
        print(f"filename: {file.filename}, content_type: {file.content_type}")
        validate_file_type(file, allowed_content_types)
        validate_file_extension(file, allowed_extensions)


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
        raise HTTPException(
            HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            f"{file.filename} file type {file.content_type} not allowed.",
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
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions.get(file.content_type, []):
        raise HTTPException(
            HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            f"{file.filename} file extension {ext} not allowed for"
            f" content type {file.content_type}.",
        )
