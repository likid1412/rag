FROM python:3.10
WORKDIR /rag
COPY ./requirements.txt /rag/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt -i https://mirrors.tencent.com/pypi/simple/
COPY ./app /rag/app
CMD ["fastapi", "run", "app/main.py", "--port", "80"]