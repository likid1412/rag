"""endpoints entrance"""

from fastapi import FastAPI, UploadFile
from app.model.file import OcrPayload, ExtractPayload
from app.valid.valid import validate_files
from app.storage.storage import Storage

app = FastAPI()


@app.post("/upload")
async def upload(files: list[UploadFile]) -> dict:
    """
    Upload files (limited to pdf, tiff, png, jpeg formats),
    saves files to storage, returning file infos (see Returns)

    Args:
        files (list[UploadFile]): The uploaded file list.

    Returns:
        dict: uploaded file info with the original file name from uploaded file,
        unique file id and signed URL

    Raises:
        HTTPException:
            - If the file content type or file extension is not allowed.
            - If upload failed
    """

    # validate files format
    validate_files(files)

    s = Storage(Storage.RAG_Bucket)
    file_infos = await s.upload_file_and_get_presigned_url(files)

    # TODO: error handler

    # TODO: try async upload
    return {"file_infos": file_infos}


@app.post("/ocr")
async def ocr(payload: OcrPayload):
    return {"signed_url": payload.signed_url}


@app.post("/extract")
async def extract(payload: ExtractPayload):
    return {"query": payload.query, "file_id": payload.file_id}
