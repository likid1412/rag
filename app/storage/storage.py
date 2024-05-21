"""Handle Storage operations, such as upload file"""

import os
import io
from typing import BinaryIO
from datetime import datetime, timedelta
import pytz
from loguru import logger
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
import starlette.datastructures
from app.helper.file import get_unique_filename, FileInfo


class Storage:
    """Handle Storage operations, such as upload file"""

    RAG_Bucket = "rag"

    _client: Minio
    _bucket: str

    def __init__(self, bucket: str):
        """
        Create a Storage object with bucket, all operations will use this bucket
        If you want to operate another bucket, create a new Storage object

        Args:
            bucket (str): Name of the bucket.

        Returns:
            Storage: class:`Minio <Minio>` object
        """

        self._client = self._new_client()
        self._bucket = bucket

    def _new_client(self) -> Minio:
        return Minio(
            os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=False,
        )

    def get_file_dict_list(self, files: list[UploadFile]) -> list[dict]:
        """return a list contain
        {"file": UploadFile, "file_info": FileInfo} dict

        Args:
            files (list[UploadFile]): uploaded files

        Returns:
            list[dict]: a list contain
        {"file": UploadFile, "file_info": FileInfo} dict
        """

        file_data: list[dict] = []
        for file in files:
            file_info = get_unique_filename(file.filename)
            file_data.append({"file": file, "file_info": file_info})
        return file_data

    def _check_file_params(self, file_dict_list: list[dict]) -> None:
        for file_dict in file_dict_list:
            logger.debug(f"file_dict: {file_dict}")
            msg = ""
            if "file" not in file_dict:
                msg = "file not in file_dict"
            elif "file_info" not in file_dict:
                msg = "file_info not in file_dict"
            elif not isinstance(
                file_dict["file"], starlette.datastructures.UploadFile
            ):
                # isinstance(file_dict["file"], UploadFile) return False,
                # use starlette.datastructures.UploadFile instead
                msg = f"{file_dict['file']} file value is not UploadFile type"
            elif not isinstance(file_dict["file_info"], FileInfo):
                msg = (
                    f"{file_dict['file_info']} file_info"
                    f" value is not FileInfo type"
                )
            elif file_dict["file"].file.closed:
                msg = f"{file_dict['file'].filename} is closed"

            if len(msg) > 0:
                logger.error(msg)
                raise ValueError(msg)

    async def upload_file_and_get_presigned_url(
        self,
        file_dict_list: list[dict],
    ) -> list[dict]:
        """
        Uploads files to storage,
        return file infos (file name, unique file id, presigned url)

        Args:
            files (list[UploadFile]): The uploaded file list.

        Returns:
            list[dict]: uploaded file info with file name,
            unique file id and presigned url

        Raises:
            ValueError: files invalid
        """

        self._check_file_params(file_dict_list)

        upload_result: list[dict] = []

        # upload
        for file_dict in file_dict_list:
            file: UploadFile = file_dict["file"]
            file_info: FileInfo = file_dict["file_info"]
            file_content = await file.read()
            self.upload_file_data(
                destination_file=file_info.file_unique_name,
                data=io.BytesIO(file_content),
                length=len(file_content),
                content_type=file.content_type,
            )

            # get signed url and etag as file id
            expires = timedelta(days=7)
            presigned_url = self._client.presigned_get_object(
                bucket_name=self._bucket,
                object_name=file_info.file_unique_name,
                expires=expires,
            )
            upload_result.append(
                {
                    "file_info": file_info,
                    "signed_url": presigned_url,
                    "expires": self._get_formatted_date(expires),
                }
            )

        logger.info(f"upload_result: {upload_result}")
        return upload_result

    def check_or_make_bucket(self):
        """Make the bucket if it doesn't exist."""

        found = self._client.bucket_exists(self._bucket)
        if not found:
            self._client.make_bucket(self._bucket)
            logger.info("Created bucket", self._bucket)
        else:
            logger.info("Bucket", self._bucket, "already exists")

    def upload_file_data(
        self,
        destination_file: str,
        data: BinaryIO,
        length: int,
        content_type: str,
    ) -> None:
        """
        Uploads data from source_file to an destination bucket and filename.

        Args:
            destination_file (str): The destination filename.
            data (BinaryIO): An object having callable read()
            returning bytes object.
            length (int): Data size; -1 for unknown size and
            set valid part_size.
            content_type (str): Content type of the object.

        Raises:
            HTTPException: If upload failed.
        """

        try:
            self.check_or_make_bucket()

            # Upload the file, renaming it in the process
            result = self._client.put_object(
                bucket_name=self._bucket,
                object_name=destination_file,
                data=data,
                length=length,
                content_type=content_type,
            )

        except S3Error as e:
            logger.error(f"MinIO error: {str(e)}")
            raise e

        logger.info(
            "successfully uploaded as object",
            destination_file,
            "to bucket",
            self._bucket,
            f"created {result.object_name} object;"
            f" etag: {result.etag}, version-id: {result.version_id}",
        )

    def _get_formatted_date(self, expires: timedelta, timezone="Asia/Shanghai"):
        """
        Formatted date as "MM/DD/YYYY HH:MM:SS GMT+offset"
        by adding a timedelta to the current date in a specified timezone

        Args:
            expires (timedelta): The timedelta object representing the duration
            to add to the current date.
            timezone (str, optional): The timezone identifier.
            Defaults to "Asia/Shanghai".

        Returns:
            str: The formatted date string in the specified format.
        """

        current_date = datetime.now(pytz.timezone(timezone))

        # Calculate the new date by adding a timedelta (e.g., 7 days)
        new_date = current_date + expires

        # Format the new date as "MM/DD/YYYY HH:MM:SS GMT+8"
        formatted_date = new_date.strftime("%m/%d/%Y %H:%M:%S GMT%z")

        return formatted_date
