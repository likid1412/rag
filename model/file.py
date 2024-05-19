from pydantic import BaseModel


class OcrPayload(BaseModel):
    signed_url: str
    """signed url
    """


class ExtractPayload(BaseModel):
    query: str
    """query
    """

    file_id: str
    """file id
    """
