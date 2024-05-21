"""Some helper function"""

import urllib.parse
from pydantic import HttpUrl
from loguru import logger
from app.model.file_info import FileInfo
from .uuid import get_uuid

SEP_STR = "___"


def get_unique_filename(file_name: str) -> FileInfo:
    """Generate a unique filename using the original filename and a UUID

    Args:
        filename (str): file name

    Raises:
        ValueError: if file_name is empty

    Returns:
        FileInfo: file info

    """

    if len(file_name) == 0:
        msg = "filename is empty"
        logger.error(msg)
        raise ValueError(msg)

    # we will use uuid as vector db collection name,
    # vector db collection must begin with alpha, add the alpha prefix
    file_id = f"a-{get_uuid()}"
    return FileInfo(
        file_id=file_id,
        file_name=file_name,
        file_unique_name=f"{file_id}{SEP_STR}{file_name}",
    )


def get_file_info_from_signed_url(signed_url: HttpUrl) -> FileInfo:
    """parse file info from signed_url, and return file info

    Args:
        signed_url (str): signed url

    Raises:
        ValueError: if signed_url can't parse to FileInfo

    Returns:
        FileInfo: file info
    """

    if not signed_url.path:
        msg = f"signed_url path not existed, {signed_url.path}"
        logger.error(msg)
        raise ValueError(msg)

    paths = signed_url.path.split("/")
    if len(paths) == 0:
        msg = f"signed_url paths is empty, {signed_url.path}"
        logger.error(msg)
        raise ValueError(msg)

    # file id may be a URL-encoded string
    file_unique_name = urllib.parse.unquote(paths[-1], encoding="utf-8")
    sep_list = file_unique_name.split(SEP_STR)
    if len(sep_list) != 2:
        msg = f"signed_url split path len not valid, {signed_url.path}"
        logger.error(msg)
        raise ValueError(msg)

    if len(sep_list[1]) == 0:
        msg = (
            f"signed_url split path, filename part is empty, {signed_url.path}"
        )
        logger.error(msg)
        raise ValueError(msg)

    return FileInfo(
        file_unique_name=file_unique_name,
        file_id=sep_list[0],
        file_name=sep_list[1],
    )
