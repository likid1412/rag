"""chat with Tencent hunyuan api"""

import os
import json
from loguru import logger
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models


def chat_completions(messages: list[dict[str, str]]):
    """chat with Tencent hunyuan api

    Args:
        messages (list[dict]):
        A list of messages comprising the conversation so far.

    Returns:
        str: chat response content
    """

    client = _get_client()

    new_msg_list: list[dict] = []
    for msg in messages:
        new_msg: dict[str, str] = {}
        for k, v in msg.items():
            upcast = k[0].upper() + k[1:]
            new_msg[upcast] = v

        new_msg_list.append(new_msg)
    logger.info(f"new_msg_list:{new_msg_list}")

    # 实例化一个请求对象,每个接口都会对应一个request对象
    req = models.ChatCompletionsRequest()
    params = {
        "Model": os.getenv("TENCENT_MODEL"),
        "Messages": new_msg_list,
        "Stream": False,
    }
    req.from_json_string(json.dumps(params))

    response: models.ChatCompletionsResponse
    choice: models.Choice
    response = client.ChatCompletions(req)
    choice = response.Choices[0]
    logger.info(f"response: {response}")
    return choice.Message.Content


def _get_client():
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
