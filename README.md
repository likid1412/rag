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

# run
docker run -dt \
    --name rag-test  \
    python:3.10
```