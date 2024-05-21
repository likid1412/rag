"""OCR operations"""

import os
import json
import random
import asyncio
import tempfile
import textwrap
import traceback
import requests
from loguru import logger
from app.embedding.embedding import Embedding
from app.vectordb.vectordb import VDB
from app.helper.safe_dict import ThreadSafeDict
from app.helper.uuid import get_uuid
from app.helper.token import num_tokens
from app.helper.file import FileInfo
from app.helper.retry import retry


class Ocr:
    """OCR operations"""

    # FIXME: It's better to save status into database,
    # in memory dict will clear after server stop
    ocr_progress: ThreadSafeDict = ThreadSafeDict()
    """ocr progress dict, key is file_id, value is progress"""

    def __init__(self, singed_url: str, file_info: FileInfo) -> None:
        """init ocr instance

        Args:
            singed_url (str): singed url for downloaded file
            file_info (FileInfo): file info
        """

        self.singed_url = singed_url
        self.file_info = file_info

    # pylint: disable=broad-exception-caught
    async def perform_ocr_in_background(self) -> None:
        """ocr may take long time, perform ocr operation in background"""

        if not self.file_info.is_valid():
            logger.error(f"file_info invalid, file_info: {self.file_info}")
            return

        await asyncio.to_thread(self._sync_perform_ocr)

    def _sync_perform_ocr(self) -> None:
        try:
            self._perform_ocr()
        except Exception as e:
            Ocr.ocr_progress.delete(self.file_info.file_name)
            logger.error(
                f"perform_ocr failed, file_info: {self.file_info}, e: {e}"
                f", {traceback.format_exc()}"
            )

    def _perform_ocr(self) -> None:
        """Simulates running an OCR service on a file for a given a signed url

        Args:
            singed_url (str): signed url
        """

        logger.info(f"file_info: {self.file_info}")
        file_id = self.file_info.file_id
        Ocr.ocr_progress.set(file_id, 0.01)

        # download file first
        tmp_file_path = self._download_file(self.singed_url)
        Ocr.ocr_progress.set(file_id, 0.1)

        try:
            # simulate ocr
            logger.info("start ocr")
            paragraphs = self._simulate_ocr_paragraphs(
                tmp_file_path, self.file_info.file_name
            )
            logger.info("ocr success")

            embedding_content_list = self._get_embedding_content_list(
                paragraphs
            )
            if len(embedding_content_list) == 0:
                msg = "embedding_content_list is empty"
                logger.error(msg)
                raise ValueError(msg)

            Ocr.ocr_progress.set(file_id, 0.11)

            # embedding ocr result
            logger.info("start embedding")
            self._embedding_and_save_vector(embedding_content_list, file_id)
            logger.info(
                "_embedding success"
                f", embedding_content_list len: {len(embedding_content_list)}"
            )
        except Exception as e:
            logger.error(
                f"failed after download file, remove downloaded file, e: {e}"
            )
            os.remove(tmp_file_path)
            raise e

        # Delete the temporary file
        os.remove(tmp_file_path)
        Ocr.ocr_progress.set(file_id, 1)
        logger.info("all completed")

    def _simulate_ocr_paragraphs(
        self, file_path: str, filename: str
    ) -> list[str]:
        """Simulate ocr

        Args:
            file_path (str): The path of file which need ocr

        Returns:
            list: ocr paragraphs content list
        """

        logger.info(f"simulate ocr with file_path: {file_path}")
        ocr_result = self._simulate_get_ocr_result(filename)
        err_msg = ""
        if "analyzeResult" not in ocr_result:
            err_msg = "ocr_result analyzeResult not existed"
        elif "paragraphs" not in ocr_result["analyzeResult"]:
            err_msg = "ocr_result paragraphs not existed"
        elif len(ocr_result["analyzeResult"]["paragraphs"]) == 0:
            err_msg = "ocr_result paragraphs is empty"

        if len(err_msg) > 0:
            logger.error(err_msg)
            raise ValueError(err_msg)

        paragraphs = ocr_result["analyzeResult"]["paragraphs"]
        logger.info(f"paragraphs: {paragraphs[0]}, len: {len(paragraphs)}")
        return paragraphs

    def _simulate_get_ocr_result(self, filename: str) -> dict:
        """
        Simulates get OCR json result

        Returns:
            dict: The parsed data from the randomly chosen JSON file.
        """

        json_dir = "app/ocr-json"
        if filename.startswith("建築基準法施行令"):
            chosen_file = "建築基準法施行令.json"
        elif filename.startswith("東京都建築安全条例"):
            chosen_file = "東京都建築安全条例.json"
        else:
            json_files = ["建築基準法施行令.json", "東京都建築安全条例.json"]
            chosen_file = random.choice(json_files)

        file_path = os.path.join(json_dir, chosen_file)
        logger.debug(f"filename: {filename}, chosen_file: {chosen_file}")

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _download_file(self, singed_url: str) -> str:
        timeout = 10 * 60  # 10 minutes in seconds
        logger.info(
            f"start download, singed_url: {singed_url}, timeout: {timeout}"
        )

        # Download the file from the signed URL with streaming
        response = requests.get(singed_url, stream=True, timeout=timeout)
        response.raise_for_status()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            # Write the response content to the temporary file
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name

        logger.info(f"write to tmp_file_path: {tmp_file_path} success")
        return tmp_file_path

    def _get_embedding_content_list(self, paragraphs: list) -> list[str]:
        # Seems the oce result has divided the content
        # based on its structure and hierarchy, which is the paragraphs,
        # resulting in more semantically coherent chunks,
        # we can simple use Fixed-size chunking base on the paragraphs.
        # read more: [Chunking Strategies for LLM Applications | Pinecone]
        # (https://www.pinecone.io/learn/chunking-strategies/)

        embedding_content = ""
        embedding_content_list: list[str] = []
        max_token = Embedding.EMBEDDING_MAX_TOKEN

        total_content_len = 0
        total_embedding_content_len = 0

        for p in paragraphs:
            if "content" not in p:
                continue

            content = p["content"]

            total_content_len += len(content)
            if num_tokens(embedding_content + content) <= max_token:
                # combine
                embedding_content += content
                continue

            # oversize, add to list, and reset to content
            if len(embedding_content) != 0:
                # add to list and reset
                embedding_content_list.append(embedding_content)
                embedding_content = ""

            if num_tokens(content) > max_token:
                # content in paragraphs oversize, split it with len,
                # here we use max_token as len for convenient
                split_list = textwrap.wrap(content, max_token)
                for s in split_list:
                    embedding_content_list.append(s)
            else:
                embedding_content = content

        # add last one
        if len(embedding_content) > 0:
            embedding_content_list.append(embedding_content)

        for item in embedding_content_list:
            total_embedding_content_len += len(item)

        if total_content_len != total_embedding_content_len:
            msg = (
                f"Something wrong, miss embedding content,"
                f" total_content_len: {total_content_len},"
                f" total_embedding_content_len: {total_embedding_content_len}"
            )
            logger.error(msg)
            raise ValueError(msg)

        logger.info(
            f"embedding_content_list len: {len(embedding_content_list)}, "
            f"total_embedding_content_len: {total_embedding_content_len}"
        )
        if len(embedding_content_list) > 3:
            logger.info(
                f"embedding_content_list top 3: {embedding_content_list[0:3]}"
            )
        else:
            logger.info(f"embedding_content_list: {embedding_content_list}")

        return embedding_content_list

    def _embedding_and_save_vector(
        self, embedding_content_list: list[str], collection: str
    ) -> None:
        list_len = len(embedding_content_list)
        if list_len == 0:
            logger.warning("embedding_content_list is empty")

        em = Embedding()
        # 0.1 for other task
        remaining = (1 - Ocr.ocr_progress.get(self.file_info.file_id)) - 0.1

        vdb = VDB.default_vdb(collection)

        for index, content in enumerate(embedding_content_list):
            vec = retry(em.embedding, content)

            doc_id = get_uuid()
            doc = vdb.new_document(str(doc_id), vec, content)
            retry(vdb.upsert_data, [doc])
            logger.info(f"embedding and upsert_data success, doc_id: {doc_id}")

            Ocr.ocr_progress.set(
                self.file_info.file_id, (index / list_len) * remaining
            )

            if index % 10 == 0:
                logger.info(
                    f"embedding_content_list len: {list_len}, index: {index}"
                )
