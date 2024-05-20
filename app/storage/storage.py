"""Handle Storage operations, such as upload file"""

import os
import io
import uuid
from typing import BinaryIO
from datetime import timedelta
from http import HTTPStatus
from minio import Minio
from minio.error import S3Error
from fastapi import HTTPException, UploadFile


class Storage:
    """Handle Storage operations, such as upload file"""

    RAG_Bucket = "rag"

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

    async def upload_file_and_get_presigned_url(
        self, files: list[UploadFile]
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
            HTTPException: If upload to storage failed
        """

        result: list[dict] = []

        for file in files:
            # upload
            # Generate a unique filename using the original filename and a UUID
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            file_content = await file.read()
            self.upload_file_data(
                destination_file=unique_filename,
                data=io.BytesIO(file_content),
                length=len(file_content),
                content_type=file.content_type,
            )

            # get signed url and etag as file id
            presigned_url = self.get_presigned_url(unique_filename)
            result.append(
                {
                    "filename": file.filename,
                    "file_id": unique_filename,
                    "presigned_url": presigned_url,
                }
            )

        print(f"result: {result}")
        return result

    def check_or_make_bucket(self):
        """Make the bucket if it doesn't exist."""

        found = self._client.bucket_exists(self._bucket)
        if not found:
            self._client.make_bucket(self._bucket)
            print("Created bucket", self._bucket)
        else:
            print("Bucket", self._bucket, "already exists")

    def upload_file_data(
        self,
        destination_file: str,
        data: BinaryIO,
        length: int,
        content_type: str,
    ):
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
                self._bucket, destination_file, data, length, content_type
            )

        except S3Error as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"MinIO error: {str(e)}",
            ) from e

        print(
            "successfully uploaded as object",
            destination_file,
            "to bucket",
            self._bucket,
            f"created {result.object_name} object;"
            f" etag: {result.etag}, version-id: {result.version_id}",
        )

    def get_presigned_url(
        self,
        file_name: str,
        expires: timedelta = timedelta(days=7),
    ) -> str:
        """
        Get presigned URL of an object to download its data with expiry time

        Args:
            file_name (str): Name of the file.
            expires (timedelta): Expiry in seconds; defaults to 7 days.

        Returns:
            str: URL string.
        """

        # Get presigned URL string to download 'my-object' in
        # 'my-bucket' with two hours expiry.
        return self._client.presigned_get_object(
            self._bucket,
            file_name,
            expires=expires,
        )
