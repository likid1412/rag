"""test chat"""

from tencentcloud.hunyuan.v20230901 import models
from .hunyuan import chat_completions


def _hunyuan_chat_rsp() -> str:
    return """{
        "Created": 1716503647,
        "Usage": {
            "PromptTokens": 1868,
            "CompletionTokens": 8,
            "TotalTokens": 1876
        },
        "Note": "以上内容为AI生成，不代表开发者立场，请勿删除或修改本标记",
        "Id": "23edcc4e-c8dc-4ab2-b133-57469922d813",
        "Choices": [
            {
                "FinishReason": "stop",
                "Delta": null,
                "Message": {
                    "Role": "assistant",
                    "Content": "I could not find an answer."
                }
            }
        ],
        "ErrorMsg": null,
        "RequestId": "23edcc4e-c8dc-4ab2-b133-57469922d813"
    }"""


# pylint: disable=duplicate-code
def test_hunyuan_chat_completions(mocker):
    """test hunyuan chat completions"""

    response: models.ChatCompletionsResponse = models.ChatCompletionsResponse()
    response.from_json_string(_hunyuan_chat_rsp())

    mocker.patch(
        "tencentcloud.common.credential.Credential.__init__",
        return_value=None,
    )
    mocker.patch(
        "tencentcloud.hunyuan.v20230901.hunyuan_client"
        ".HunyuanClient.ChatCompletions",
        return_value=response,
    )

    params = [
        {
            "Role": "user",
            "Content": "Use the below paragraphs on the document to"
            " answer the subsequent question.",
        },
    ]

    assert chat_completions(params) == "I could not find an answer."
