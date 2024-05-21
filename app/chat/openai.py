"""chat with OpenAI api"""

import os
from openai import OpenAI
from loguru import logger


def chat_completions(messages: list[dict]) -> str:
    """chat with OpenAI api

    Args:
        messages (list[dict]):
        A list of messages comprising the conversation so far.

    Returns:
        str: chat response content
    """

    model = os.getenv("MODEL")
    client = OpenAI(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BASE_URL"),
    )

    response = client.chat.completions.create(
        model=model, messages=messages, stream=False
    )
    logger.info(f"messages:{messages}, response: {response}")
    response_message = response.choices[0].message.content
    return response_message
