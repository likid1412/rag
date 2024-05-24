"""test extract"""

# pylint: disable=unused-import

from app.model.payload import API_OPENAI

# need to import, otherwise mocker.patch can not find module.
# Don't know why. If someone know why, please tell me.
from app.chat.openai import chat_completions  # noqa
from .extract import Extract


def _relevanted_list() -> list:
    return [
        {
            "id": "2d729e54-6b9a-472e-a9da-fdd812f24d24",
            "score": 0.48721,
            "content": "test_content_1",
        },
        {
            "id": "656d65a3-aa6c-47fe-a70e-5a70a04d9c9e",
            "score": 0.39663,
            "content": "test_content_2",
        },
    ]


def test_ask(mocker):
    """test extract"""

    answer = "I could not find an answer."

    # from app.chat import openai, hunyuan
    mocker.patch(
        "app.chat.openai.chat_completions",
        return_value=answer,
    )

    ex = Extract()
    # payload = ExtractPayload(query="", file_id="", api="")
    # answer = ex.generate_answer(payload.query, payload.file_id, payload.api)

    query = ""
    relevanted_list = _relevanted_list()

    assert (
        ex.ask(query=query, relevanted_list=relevanted_list, api=API_OPENAI)
        == answer
    )
