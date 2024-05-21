# RAG

## Project Summary: Intelligent Document Analysis with Retrieval-Augmented Generation (RAG) and Vector Search

This open-source project leverages Optical Character Recognition (OCR) to convert files in various formats (PDF, TIFF, PNG, JPEG) into text. It integrates Retrieval-Augmented Generation (RAG) for extracting relevant attributes from the text. The core functionality involves taking a query text as input, performing a vector search to identify relevant parts of the file, and using Large Language Model (LLM) providers such as OpenAI, KIMI, and Tencent Hunyuan to generate answers from the search results.

## Feature List

| Feature                  | Description                                                                                      |
|--------------------------|--------------------------------------------------------------------------------------------------|
| File Upload              | Facilitates the upload of files in supported formats for processing.                             |
| Multi-format OCR         | Supports OCR for PDF, TIFF, PNG, and JPEG files, converting them into text.                      |
| Vector Search            | Performs vector search to identify relevant parts of the text based on embeddings.               |
| LLM Integration          | Integrates with LLM providers like OpenAI, KIMI, and Tencent Hunyuan for generating responses.   |
| Embedding-based Retrieval| Uses vector embeddings for accurate and efficient information retrieval.                         |

## Getting Started with RAG

**install with Docker**

1. Clone the repos
2. Set neccessary environment variables

    Make sure to set your required environment variables in the `.env` file. You can read more about how to set them up in the [API Keys Section](#api-keys)

3. Deploy using Docker

    With Docker installed and the rag repository cloned, navigate to the directory containing the Dockerfile in your terminal or command prompt. Run the following command to start the rag application in detached mode, which allows it to run in the background:

```bash
# clone rag repo
git clone https://github.com/likid1412/rag

# navigate to rag
cd rag

# build, will download the necessary Docker images
docker build -t rag .

# run and start rag
docker run --env-file .env -dt --name rag -p 80:80 rag

```

Remember, Docker must be installed on your system to use this method. For installation instructions and more details about Docker, visit the official Docker documentation.

You can read [FastAPI in Containers](https://fastapi.tiangolo.com/deployment/docker/) for a quick start.

4. **Access rag**

- You can access your local rag [Interactive API docs](http://127.0.0.1:80/docs)
- You can access your local rag [Alternative API docs](http://127.0.0.1:80/redoc)

## API Keys

Before starting rag you'll need to configure access to various components depending on your chosen technologies, such as OpenAI, hunyuan, and Kimi via an `.env` file. Create this `.env` in the same directory you want to start rag in. Check the [.env.example](./.env.example) as example.

>Make sure to only set environment variables you intend to use, environment variables with missing or incorrect values may lead to errors.

Below is a comprehensive list of the API keys and variables you may require:

| Environment Variable | Value | Description |
|---|---|---|
| MINIO_ENDPOINT | the endpoint to your minio storage | See [Minio as local storage](docs/minio.md) |
| MINIO_ACCESS_KEY | Minio access key | See [Minio as local storage](docs/minio.md) |
| MINIO_SECRET_KEY | Minio secret key | See [Minio as local storage](docs/minio.md) |
|---|---|---|
| TENCENT_VECTOR_URL | URL for Tencent Vector Database | Access to [Tencent Vector Database](https://console.cloud.tencent.com/vdb) |
| TENCENT_VECTOR_USER | Username for Tencent Vector Database | Access to [Tencent Vector Database](https://console.cloud.tencent.com/vdb) |
| TENCENT_VECTOR_KEY | API Key for Tencent Vector Database | Access to [Tencent Vector Database](https://console.cloud.tencent.com/vdb) |
|---|---|---|
| TENCENTCLOUD_SECRET_ID | Tencent Cloud Secret ID for Tencent hunyuan LLM | Access to [Tencent API](https://console.cloud.tencent.com/cam/capi) for Tencent hunyuan LLM |
| TENCENTCLOUD_SECRET_KEY | Tencent Cloud Secret Key for Tencent hunyuan LLM | Access to [Tencent API](https://console.cloud.tencent.com/cam/capi) for Tencent hunyuan LLM |
| TENCENT_MODEL | Tencent HunYuan Model name | [Tencent hunyuan model](https://cloud.tencent.com/document/api/1729/105701) |
|---|---|---|
| API_KEY | OpenAI SDK API Key | Accee OpenAI or compatible LLM Provider API Key such as [Kimi](https://platform.moonshot.cn/console/api-keys) |
| BASE_URL | OpenAI SDK Base URL | Accee OpenAI or compatible LLM Provider API Key such as [Kimi](https://platform.moonshot.cn/console/api-keys) |
| MODEL | OpenAI SDK Model name | Model of OpenAI or compatible LLM Provider |


## Storage

Use minio as local storage, see [Minio as local storage](docs/minio.md) for more detail

## Embedding

### OpenAI embedding

You can get it from [OpenAI](https://openai.com/)

### Tencent hunyuan embedding

Check [hunyuan-embedding-API](https://cloud.tencent.com/document/api/1729/102832) for more detail.

You can find instructions for obtaining a key [here](https://console.cloud.tencent.com/hunyuan/start)

## Vector Database

You can get it from [Tencent Vector Database](https://console.cloud.tencent.com/vdb)

## LLM providers

### OpenAI

You can get it from [OpenAI](https://openai.com/)

### Kimi (Moonshot)

Check [Moonshot](https://platform.moonshot.cn/docs/api/chat) for more detail.

You can find instructions for obtaining a key [here](https://platform.moonshot.cn/console/api-keys)

### Tencent hunyuan

Check [hunyuan](https://cloud.tencent.com/document/api/1729/105701) for more detail.

You can find instructions for obtaining a key [here](https://console.cloud.tencent.com/hunyuan/start)


## TODO

- Upload large file using stream upload
- Add uuid to log for trace

## One More Thing

### About Chunking Strategies

Seems the oce result has divided the content based on its structure and hierarchy, which is the paragraphs, resulting in more semantically coherent chunks, we can simple use Fixed-size chunking base on the paragraphs.

read more: [Chunking Strategies for LLM Applications | Pinecone](https://www.pinecone.io/learn/chunking-strategies/)