"""vector db operations"""

import os
from loguru import logger
import tcvectordb
from tcvectordb import exceptions
from tcvectordb.model.document import Document, SearchParams
from tcvectordb.model.enum import (
    FieldType,
    IndexType,
    MetricType,
    ReadConsistency,
)
from tcvectordb.model.index import (
    Index,
    VectorIndex,
    FilterIndex,
    HNSWParams,
)
from tcvectordb.model.database import Database
from tcvectordb.model.collection import Collection

# disable/enable http request log print
tcvectordb.debug.DebugEnable = False


class VDB:
    """vector db operations"""

    DATABASE_RAG = "rag"

    DEFAULT_EMBEDDING_DIMENSION = 1024

    MSG_DATABASE_NOT_EXIST = "Database not exist:"
    MSG_COLLECTION_NOT_EXIST = "Collection not exist"

    @classmethod
    def default_vdb(cls, collection: str = ""):
        """create a default vector database instance

        - if collection is not empty, create collection if not existed
        - if collection is empty, you need to set collection before call
            instance functions

        Returns:
            VDB: a default vector database instance
        """

        try:
            vdb = VDB(
                url=os.getenv("TENCENT_VECTOR_URL"),
                key=os.getenv("TENCENT_VECTOR_KEY"),
                username=os.getenv("TENCENT_VECTOR_USER"),
                database=VDB.DATABASE_RAG,
                collection=collection,
            )
        except exceptions.VectorDBException as e:
            logger.error(f"create vdb client failed, e:{e}")
            raise e

        if len(collection) > 0:
            vdb._get_or_create_collection(
                dimension=VDB.DEFAULT_EMBEDDING_DIMENSION
            )
        return vdb

    def __init__(
        self,
        url: str,
        username: str,
        key: str,
        database: str,
        collection: str,
        timeout: int = 30,
    ):
        """init client

        Args:
            url (str): endpoint
            username (str): user name
            key (str): db key
            timeout (int, optional): timeout, seconds. Defaults to 30.
        """

        if not url or not username or not key:
            msg = "url, username or key is empty"
            logger.error(msg)
            raise exceptions.ParamError(message=msg)

        self._client = tcvectordb.VectorDBClient(
            url=url,
            username=username,
            key=key,
            read_consistency=ReadConsistency.STRONG_CONSISTENCY,
            timeout=timeout,
        )

        self._database = database
        self.collection = collection

    def drop_db(self):
        try:
            db = self._client.database(self._database)
            db.drop_database(self._database)
            logger.info(f"{self._database} drop database success")
        except exceptions.ParamError as e:
            if e.message.startswith(VDB.MSG_DATABASE_NOT_EXIST):
                logger.info(f"{self._database} Database not exist")
            else:
                raise

    # def delete_and_drop(self):
    #     db = self._client.database(self._database)

    #     # 删除collection，删除collection的同时，其中的数据也将被全部删除
    #     db.drop_collection(self._collection)

    #     # 删除db，db下的所有collection都将被删除
    #     db.drop_database(self._database)

    def is_db_existed(self) -> Database | None:
        try:
            db = self._client.database(self._database)
            return db
        except exceptions.ParamError as e:
            if e.message.startswith(VDB.MSG_DATABASE_NOT_EXIST):
                logger.info(f"{self._database} Database not exist, e: {e}")
            else:
                raise

        return None

    def is_collection_existed(self, collection: str = "") -> Collection | None:
        if len(collection) == 0:
            collection = self.collection

        try:
            db = self._client.database(self._database)
            coll = db.collection(collection)
            return coll
        except exceptions.ServerInternalError as e:
            if e.message.startswith(VDB.MSG_COLLECTION_NOT_EXIST):
                logger.info(f"{collection} Collection not exist, e: {e}")
            else:
                raise

        return None

    def _get_or_create_db(self) -> Database:
        db = self.is_db_existed()
        if db is not None:
            logger.info(f"{self._database} Database existed, {db}")
            return db

        logger.info(f"{self._database} Database not existed, create")
        db = self._client.create_database(self._database)
        logger.info(f"{self._database} Database create success")
        return db

    def _get_or_create_collection(self, dimension: int):
        db = self._get_or_create_db()
        coll = self.is_collection_existed()
        if coll is not None:
            logger.info(f"{self.collection} Collection existed, {coll}")
            return coll

        index = Index()
        index.add(
            VectorIndex(
                "vector",
                dimension,
                IndexType.HNSW,
                MetricType.COSINE,
                HNSWParams(m=16, efconstruction=200),
            )
        )
        index.add(FilterIndex("id", FieldType.String, IndexType.PRIMARY_KEY))

        # 第二步：创建 Collection
        # 免费测试版实例，其分片 shard 只能为 1，副本 replicas 仅能为 0。
        coll = db.create_collection(
            name=self.collection,
            shard=1,
            replicas=0,
            description="",
            index=index,
        )

        logger.info(f"{self.collection} Create collection success, {coll}")
        return coll

    def new_document(
        self, doc_id: str, vector: list[float], content: str
    ) -> Document:
        return Document(id=doc_id, vector=vector, content=content)

    def upsert_data(self, document_list: list[Document]) -> None:
        # 获取 Collection 对象
        db = self._client.database(self._database)
        coll = db.collection(self.collection)

        # upsert 写入数据，可能会有一定延迟
        # 1. 支持动态 Schema，除了 id、vector 字段必须写入，可以写入其他任意字段；
        # 2. upsert 会执行覆盖写，若文档id已存在，则新数据会直接覆盖原有数据(删除原有数据，再插入新数据)

        result = coll.upsert(documents=document_list)
        logger.info(f"upsert success, result: {result}")

    def search(
        self,
        vector: list[float],
        top_k: int = 10,
        retrieve_vector: bool = False,
    ) -> list[dict]:
        # 获取 Collection 对象
        db = self._client.database(self._database)
        coll = db.collection(self.collection)

        # search
        # 1. search 提供按照 vector 搜索的能力
        # 其他选项类似 search 接口

        # 批量相似性查询，根据指定的多个向量查找多个 Top K 个相似性结果
        doc_list = coll.search(
            vectors=[vector],  # 指定检索向量，最多指定20个
            params=SearchParams(
                ef=200
            ),  # 若使用HNSW索引，则需要指定参数ef，ef越大，召回率越高，但也会影响检索速度
            retrieve_vector=retrieve_vector,
            limit=top_k,
        )

        if len(doc_list) == 0:
            logger.warning("doc_list is empty")
            return doc_list

        # search vectors only one item, get first result
        return doc_list[0]

    @classmethod
    def get_list_without_content(cls, doc_list: list[dict]) -> list[dict]:
        """get doc list without content item, convenient for log

        Args:
            doc_list (list[dict]): doc list from search

        Returns:
            list[dict]: doc list without content item
        """

        simple_msg: list[dict] = []
        for item in doc_list:
            simple_info = {}
            logger.info(f"item: {item}")
            for k, v in item.items():
                if k == "content":
                    continue
                simple_info[k] = v

            simple_msg.append(simple_info)

        return simple_msg
