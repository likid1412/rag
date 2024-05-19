FROM python:3.10
WORKDIR /rag
COPY . /rag
RUN pip install -r requirements.txt -i https://mirrors.tencent.com/pypi/simple/