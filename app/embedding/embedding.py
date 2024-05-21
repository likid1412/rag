"""Embedding operations"""

import os
from loguru import logger
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models


class Embedding:
    """Embedding operations"""

    EMBEDDING_MAX_TOKEN = int(os.getenv("EMBEDDING_MAX_TOKEN", "1024"))

    def __init__(self) -> None:
        self._client = self._get_client()

    def _get_client(self):
        cred = credential.Credential(
            os.getenv("TENCENTCLOUD_SECRET_ID"),
            os.getenv("TENCENTCLOUD_SECRET_KEY"),
        )
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        http_profile = HttpProfile()
        http_profile.endpoint = "hunyuan.tencentcloudapi.com"

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = hunyuan_client.HunyuanClient(cred, "", client_profile)
        return client

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
                raise ValueError(msg)

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
                raise ValueError(msg)

            return vec
        except TencentCloudSDKException as e:
            logger.error(f"GetEmbedding failed, e: {e}")
            raise e
