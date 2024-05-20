# RAG

an application that integrates file handling, simulates Optical Character Recognition (OCR), and employs Retrieval-Augmented Generation (RAG) for attribute extraction.

## Task

- Endpoints
    - upload
    - ocr
    - extract
- chat
    - [Moonshot AI - 开放平台](https://platform.moonshot.cn/console/api-keys) ok
- embedding
    - debug ok

## Build docker image

```sh
# build
docker build -t rag .

# run, 9090 for accessing minio
docker run -dt \
    --name rag-test  \
    -p 80:80 \
    -p 9090:9090 \
    rag
```

ref: [FastAPI in Containers - Docker - FastAPI](https://fastapi.tiangolo.com/deployment/docker/)