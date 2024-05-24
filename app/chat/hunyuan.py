"""chat with Tencent hunyuan api"""

import os
import json
from loguru import logger
from tencentcloud.hunyuan.v20230901 import models
from app.client.hunyuan_client import new_hunyuan_client


def chat_completions(messages: list[dict[str, str]]):
    """chat with Tencent hunyuan api

    Args:
        messages (list[dict]):
        A list of messages comprising the conversation so far.

    Returns:
        str: chat response content
    """

    client = new_hunyuan_client()

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
