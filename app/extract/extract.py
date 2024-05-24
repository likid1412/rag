"""generate answer from query"""

import os
from loguru import logger
from app.embedding.embedding import Embedding
from app.vectordb.vectordb import VDB
from app.helper.token import num_tokens
from app.chat import openai, hunyuan
from app.model.payload import API_HUNYUAN


class Extract:
    """generate answer from query"""

    ASK_INTRODUCTION = (
        "Use the below paragraphs on the document to answer the subsequent"
        " question. If the answer cannot be found in the paragraphs,"
        ' write "I could not find an answer."'
    )
    ANSWER_NOT_FOUND = "I could not find an answer."

    MAX_TOKEN = int(os.getenv("MAX_TOKEN", "10240"))
    """
    The max token of model use (input + output)

    Why max is 10240 (10k) token?

    1. Default retrieve relevant text from vector database is 10 items
    2. The max embedding input token is 1024 (1k)
    3. Max token for model input should be 10240 (10k)
    """

    OUTPUT_TOKEN = int(os.getenv("OUTPUT_TOKEN", "500"))
    """
    The token of model output, default to 500

    Output should be short in RAG situation (Question answering)
    """

    TOKEN_BUDGET = MAX_TOKEN - OUTPUT_TOKEN
    """
    The token of model input = max token - output token
    """

    def __init__(self) -> None:
        pass

    def generate_answer(self, query: str, file_id: str, api: str) -> str:
        """generate answer from query using GPT and relevant texts search from
        vector database which relevanted to the file_id

        Args:
            query (str): query

        Returns:
            str: answer
        """

        # check vector databse document of file_id existed
        vdb = VDB.default_vdb()
        if not vdb.is_collection_existed(file_id):
            msg = f"{file_id} fild_id of ducument not existed"
            logger.error(msg)
            raise ValueError(msg)

        # document of file_id existed, set to collection
        vdb.collection = file_id

        # embedding query text into vector using embedding model
        em = Embedding()
        vec = em.embedding(query)

        # search query text vector in vector database using file_id
        relevanted_list = vdb.search(vec)
        if len(relevanted_list) == 0:
            return Extract.ANSWER_NOT_FOUND

        logger.info(
            f"relevanted_list: {VDB.get_list_without_content(relevanted_list)}"
        )

        # call chat completion to generate the answer from the search result
        answer = self.ask(query=query, relevanted_list=relevanted_list, api=api)

        return answer

    def query_message(
        self,
        query: str,
        relevanted_list: list[dict],
        token_budget: int,
    ) -> str:
        """Return a message for GPT, with relevant source texts

        Args:
            query (str): query
            relevanted_list (list[dict]): list of relevant texts
            token_budget (int): token budget

        Returns:
            str: a message for GPT, with relevant source texts
        """

        strings: list[str] = []
        for relevanted in relevanted_list:
            strings.append(relevanted["content"])

        introduction = Extract.ASK_INTRODUCTION
        question = f"\n\nQuestion: {query}"
        message = introduction
        for string in strings:
            next_article = f'\n\nparagraph section:\n"""\n{string}\n"""'
            if num_tokens(message + next_article + question) > token_budget:
                break

            message += next_article
        return message + question

    def ask(
        self,
        query: str,
        relevanted_list: list[dict],
        api: str,
        token_budget: int = TOKEN_BUDGET,
    ) -> str:
        """Answers a query using GPT and list of relevant texts.

        Args:
            query (str): query
            relevanted_list (list[dict]): list of relevant texts
            api (str, optional): call api with API_OPENAI or API_HUNYUAN.
            token_budget (int, optional): token budget. Defaults TOKEN_BUDGET.

        Returns:
            str: _description_
        """
        message = self.query_message(
            query, relevanted_list, token_budget=token_budget
        )

        messages = [
            {"role": "user", "content": message},
        ]

        if api == API_HUNYUAN:
            return hunyuan.chat_completions(messages)

        return openai.chat_completions(messages)
