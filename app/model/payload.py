"""model class"""

from loguru import logger
from pydantic import BaseModel, Field, HttpUrl, field_validator

API_OPENAI = "OpenAI"
"""api for OpenAI"""

API_HUNYUAN = "hunyuan"
"""api for Tencent hunyuan model"""


class OcrPayload(BaseModel):
    """ocr endpoint payload"""

    signed_url: HttpUrl
    """signed url
    """


class ExtractPayload(BaseModel):
    """extract endpoint paylod"""

    query: str = Field(..., min_length=3)
    """query
    """

    file_id: str = Field(..., min_length=10)
    """file id
    """

    api: str = Field(
        API_OPENAI,
        description="LLM provider api, could be OpenAI or hunyuan, "
        "default to OpenAI.",
    )
    """LLM provider api, could be OpenAI or hunyuan, default to OpenAI.
    """

    @field_validator("api")
    @classmethod
    def validate_api(cls, value):
        """check api value is valid or not"""

        allowed_values = {API_OPENAI, API_HUNYUAN}
        if value not in allowed_values:
            msg = (
                f"api must be either {API_OPENAI} or {API_HUNYUAN}"
                f", or empty to default {API_OPENAI}"
            )
            logger.error(msg)
            raise ValueError(msg)
        return value
