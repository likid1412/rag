from fastapi import FastAPI, UploadFile

from model.file import OcrPayload, ExtractPayload

app = FastAPI()


@app.post("/upload")
async def upload(files: list[UploadFile]):
    return {"filenames": [file.filename for file in files]}


@app.post("/ocr")
async def ocr(payload: OcrPayload):
    return {"signed_url": payload.signed_url}


@app.post("/extract")
async def extract(payload: ExtractPayload):
    return {"query": payload.query, "file_id": payload.file_id}
