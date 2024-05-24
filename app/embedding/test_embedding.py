"""test embedding"""

import json
from tencentcloud.hunyuan.v20230901 import models
from .embedding import Embedding


# pylint: disable=duplicate-code
def test_embedding(mocker):
    """test embedding"""

    with open(
        "embedding/embedding_rsp_example.json", "r", encoding="utf-8"
    ) as f:
        json_str = f.read()
        rsp = models.GetEmbeddingResponse()
        rsp.from_json_string(json_str)

        rsp_dict = json.loads(json_str)

    mocker.patch(
        "tencentcloud.common.credential.Credential.__init__",
        return_value=None,
    )
    mocker.patch(
        "tencentcloud.hunyuan.v20230901.hunyuan_client"
        ".HunyuanClient.GetEmbedding",
        return_value=rsp,
    )

    em = Embedding()
    assert em.embedding("hello") == rsp_dict["Data"][0]["Embedding"]
