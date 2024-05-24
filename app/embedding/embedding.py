"""Embedding operations"""

import os
from loguru import logger
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.hunyuan.v20230901 import models
from app.client.hunyuan_client import new_hunyuan_client
from app.exceptions.exceptions import InvalidResponseFromUpStream


# pylint: disable=too-few-public-methods
class Embedding:
    """Embedding operations"""

    EMBEDDING_MAX_TOKEN = int(os.getenv("EMBEDDING_MAX_TOKEN", "1024"))
    """
    Embedding input can not over 1024 token

    ref: https://cloud.tencent.com/document/api/1729/102832
    """

    def __init__(self) -> None:
        self._client = new_hunyuan_client()

    def embedding(self, content: str) -> list[float]:
        """embedding content

        Args:
            content (str): Embedding content, need less or equal than 1024 Token

        Returns:
            _type_: _description_
        """

        try:
            # 实例化一个请求对象,每个接口都会对应一个request对象
            req = models.GetEmbeddingRequest()
            req.Input = content

            # 返回的resp是一个GetEmbeddingResponse的实例，与请求对象对应
            rsp = self._client.GetEmbedding(req)
            if not isinstance(rsp.Data, list):
                msg = (
                    f"GetEmbedding rsp data is not list, {rsp.Data}, req: {req}"
                )
                logger.error(msg)
                raise TypeError(msg)
            if len(rsp.Data) == 0:
                msg = f"GetEmbedding rsp data is empty, req: {req}"
                logger.error(msg)
                raise InvalidResponseFromUpStream(
                    "GetEmbedding rsp data is empty"
                )

            logger.info(
                f"GetEmbedding success, content: {content},"
                f" Usage: {rsp.Usage}, RequestId: {rsp.RequestId}"
            )

            data: models.EmbeddingData
            vec: list[float]
            data = rsp.Data[0]
            vec = data.Embedding
            if len(vec) == 0:
                msg = "GetEmbedding Embedding vector is empty"
                logger.error(msg)
                raise InvalidResponseFromUpStream(msg)

            return vec
        except TencentCloudSDKException as e:
            logger.error(f"GetEmbedding failed, e: {e}")
            raise e
