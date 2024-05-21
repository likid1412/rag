"""token operation"""


def num_tokens(text: str) -> int:
    """
    Return the number of tokens in a string.

    **NOTE** simulate it 1 to 1

    On average, a token in Japanese can be roughly equivalent to 1-3 characters,

    or use api to calculate it such as
    [Token calculator](https://console.cloud.tencent.com/hunyuan/tokenizer)
    """

    return len(text)
