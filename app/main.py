"""endpoints entrance"""

import os
import sys
from loguru import logger
from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    status,
    BackgroundTasks,
    Path,
)

from .model.payload import OcrPayload, ExtractPayload
from .valid.valid import validate_files
from .storage.storage import Storage
from .ocr.ocr import Ocr
from .extract.extract import Extract
from .helper.file import get_file_info_from_signed_url
from .exceptions.exceptions import (
    ExceptionHandlingMiddleware,
)


LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss:SSS} | {level} | {file}:{line} | {message}"
)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# remove default logger, will log DEBUG msg to stderr
logger.remove()
logger.add(
    sys.stdout,
    format=LOG_FORMAT,
    level=LOG_LEVEL,
)
logger.add(
    "app.log",
    format=LOG_FORMAT,
    level=LOG_LEVEL,
)


app = FastAPI()

# handle endpoints exception in ExceptionHandlingMiddleware
app.add_middleware(ExceptionHandlingMiddleware)


@app.post("/upload")
async def upload(files: list[UploadFile]) -> dict:
    """
    Upload files (limited to pdf, tiff, png, jpeg formats),
    saves files to storage, returning file infos (see Returns)

    Args:
        files (list[UploadFile]): The uploaded file list.

    Returns:
        dict: uploaded file info with the original file name from uploaded file,
        unique file id, signed URL and
        unique file name which you can search in minio

    Raises:
        - code 400, If file name duplicated in files.
        - code 415, If the file content type or file extension is not allowed.
        - code 500, If internal error happened.


    """

    # NOTE:
    # - the UploadFile object is created when the file is uploaded,
    # UploadFile is not support stream now,
    # client/web will get block until file is uploaed
    # - try processing file (upload to storage) in background using
    # background_tasks, file will get closed (file.close() return True)

    # TODO: should use stream upload for large file,
    # seems fastapi can not do it directly
    # ref:https://github.com/tiangolo/fastapi/issues/2578#issuecomment-752334996

    # validate files format
    validate_files(files)

    s = Storage(Storage.RAG_Bucket)
    file_dict_list = s.get_file_dict_list(files)
    logger.info(f"file_dict_list: {file_dict_list}")

    # FIXME:
    # file will get closed (file.close() return True) running in background,
    # working on solution.
    # 1. copy and pass the buffer, but that will put
    # file data into memory, which is bad for large file
    # TODO: 2. write files to disk, and read them in background (will try)

    # if background:
    #     background_tasks.add_task(
    #         s.upload_file_and_get_presigned_url, file_dict_list
    #     )

    #     file_info_list = []
    #     for file_dict in file_dict_list:
    #         file_info_list.append(file_dict["file_info"])

    #     return {"file_info_list": file_info_list}
    # else:
    upload_result = await s.upload_file_and_get_presigned_url(file_dict_list)
    return {"upload_result": upload_result}


@app.post("/ocr")
async def ocr(payload: OcrPayload, background_tasks: BackgroundTasks) -> dict:
    """
    In background perform OCR  on the document specified by the signed URL.

    Args:
        payload (OcrPayload): A payload containing the signed URL of
        the document to process.

    Returns:
        dict: the result of the OCR process.

    Raises:
        - code 422, If payload is invalid
        - code 400, If signed_url is not a valid download url,
            should container file_id and file_name
        - code 500, If internal error happened.
    """

    logger.info(f"ocr payload: {payload}")
    file_info = get_file_info_from_signed_url(payload.signed_url)
    logger.info(f"file_info: {file_info}")

    o = Ocr(str(payload.signed_url), file_info)
    background_tasks.add_task(o.perform_ocr_in_background)
    Ocr.ocr_progress.set(file_info.file_id, 0)
    return {
        "status": "processing",
        "file_id": file_info.file_id,
    }


@app.get("/ocr_progress/{file_id}")
async def get_ocr_progress(file_id: str = Path(..., min_length=10)) -> dict:
    """get ocr progress of file_id

    Args:
        file_id (str): file id

    Returns:
        dict: ocr progress of file_id,
        status completed will return once finished

    Raises:
        - code 422, If file_id is not valid, min length >= 10
        - code 404, If the progress of file_id not found,
        check whether the file has been process in ocr endpoint or not
    """

    progress = Ocr.ocr_progress.get(file_id)
    if progress is None:
        msg = f"{file_id} file_id not found"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        )

    if progress >= 1.0:
        return {"status": "completed"}

    return {"status": "processing", "progress": progress}


@app.post("/extract")
async def extract(payload: ExtractPayload) -> dict:
    """generate answer from query using GPT and relevant texts search from
        vector database which related to the file_id

    Args:
        payload (ExtractPayload): A payload containing the query and file_id
        which related to the query

    Returns:
        dict: generate answer from query using GPT

    Raises:
        - code 422, If payload is invalid
        - code 500, If internal error happened.
    """

    ex = Extract()
    answer = ex.generate_answer(payload.query, payload.file_id, payload.api)

    return {"answer": answer}
