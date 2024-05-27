"""Handle Storage operations, such as upload file"""

import os
import time
import tempfile
import shutil
from datetime import datetime, timedelta
import pytz
from loguru import logger
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
from app.helper.file import get_unique_filename, FileInfo
from app.helper.safe_dict import ThreadSafeDict


class Storage:
    """Handle Storage operations, such as upload file"""

    RAG_Bucket = "rag"
    upload_results: ThreadSafeDict = ThreadSafeDict()
    """upload results dict, key is file_id, value is upload_result dict"""

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
        {"temp_file_path": path saved UploadFile, "file_info": FileInfo} dict

        Args:
            files (list[UploadFile]): uploaded files

        Returns:
            list[dict]: a list contain
        {"temp_file_path": path saved UploadFile, "file_info": FileInfo} dict
        """

        file_data: list[dict] = []
        for file in files:
            temp_file_path = ""
            try:
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file_path = temp_file.name
                    shutil.copyfileobj(file.file, temp_file)
            except Exception as e:
                logger.error(f"write to temp_file failed, e: {e}")
                if len(temp_file_path) > 0 and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                raise

            file_info = get_unique_filename(file.filename)
            file_data.append(
                {
                    "file_info": file_info,
                    "temp_file_path": temp_file_path,
                }
            )
        return file_data

    def _check_file_params(self, file_dict_list: list[dict]) -> None:
        msg = ""
        for file_dict in file_dict_list:
            logger.debug(f"file_dict: {file_dict}")
            temp_file_path = file_dict.get("temp_file_path", None)
            file_info = file_dict.get("file_info", None)

            if not isinstance(temp_file_path, str):
                msg = f"{temp_file_path} temp_file_path value is not str type"
                break

            if not isinstance(file_info, FileInfo):
                msg = f"{file_info} file_info value is not FileInfo type"
                break

            if not os.path.exists(temp_file_path):
                msg = f"{temp_file_path} file not existed"
                break

        if len(msg) > 0:
            logger.error(msg)
            raise ValueError(msg)

    async def upload_file_in_background(
        self,
        file_dict_list: list[dict],
    ) -> list[dict]:
        upload_result: dict[str, dict] = None
        try:
            upload_result = await self.upload_file_and_get_presigned_url(
                file_dict_list
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"write to temp_file failed, e: {e}")

        for file_dict in file_dict_list:
            # remove temp file no matter failed or success
            temp_file_path = file_dict["temp_file_path"]
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            file_info: FileInfo = file_dict["file_info"]
            if upload_result is None:
                # failed
                Storage.upload_results.set(
                    file_info.file_id, {"status": "failed"}
                )
            else:
                if file_info.file_id not in upload_result:
                    logger.error(f"{file_info.file_id} not in upload_result")
                    continue

                # success
                Storage.upload_results.set(
                    file_info.file_id,
                    {
                        "status": "success",
                        "result": upload_result[file_info.file_id],
                    },
                )
                logger.info(
                    f"upload success, {upload_result[file_info.file_id]}"
                )

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

        st = time.time()
        upload_result: dict[str, dict] = {}

        self._check_file_params(file_dict_list)

        # upload
        for file_dict in file_dict_list:
            temp_file_path = file_dict["temp_file_path"]
            file_info: FileInfo = file_dict["file_info"]
            self.upload_file_data(
                destination_file=file_info.file_unique_name,
                file_path=temp_file_path,
            )

            # get signed url and etag as file id
            expires = timedelta(days=7)
            presigned_url = self._client.presigned_get_object(
                bucket_name=self._bucket,
                object_name=file_info.file_unique_name,
                expires=expires,
            )
            upload_result[file_info.file_id] = {
                "file_info": file_info,
                "signed_url": presigned_url,
                "expires": self._get_formatted_date(expires),
            }

        logger.info(f"cost: {time.time() - st}, upload_result: {upload_result}")
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
        file_path: str,
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
            result = self._client.fput_object(
                bucket_name=self._bucket,
                object_name=destination_file,
                file_path=file_path,
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
