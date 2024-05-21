"""test"""

import os
from fastapi import status
from fastapi.testclient import TestClient
from .main import app

FILE_ID = "a-fa54ff56-7d03-4659-a993-42780a2d911f"
SIGNED_URL = (
    f"http://localhost:9000/rag/{FILE_ID}"
    "___%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%BB%BA%E7%AF%89%E5%AE%89%E5%85%A"
    "8%E6%9D%A1%E4%BE%8B.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz"
)


def test_upload_bad_case_format_error():
    """test upload"""

    with TestClient(app) as client:
        files = []  # List to store httpx.MultipartFile objects
        file_name_list: list[str] = []
        content_type = "text/plain"

        # Create three temporary files with different content
        for i in range(2):
            file_name = f"test_file_{i}.txt"
            file_name_list.append(file_name)
            with open(file_name, "wb") as f:
                f.write(f"This is test content {i}".encode())
                files.append(
                    ("files", (file_name, open(file_name, "rb"), content_type))
                )

        # Send the POST request with multiple files in the dictionary
        response = client.post("/upload", files=files)
        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        assert response.json() == {
            "detail": f"{file_name_list[0]} file type"
            f" {content_type} not allowed.",
        }

        # Clean up temporary files
        for file_name in file_name_list:
            os.remove(file_name)


def test_upload_bad_case_file_name_duplicated():
    """test upload"""

    with TestClient(app) as client:
        files = []  # List to store httpx.MultipartFile objects
        file_name_list: list[str] = []
        content_type = "application/pdf"

        # Create three temporary files with different content
        for i in range(1):
            file_name = f"test_file_{i}.pdf"
            file_name_list.append(file_name)
            with open(file_name, "wb") as f:
                f.write(f"This is test content {i}".encode())

        files.append(
            ("files", (file_name, open(file_name, "rb"), content_type))
        )
        files.append(
            ("files", (file_name, open(file_name, "rb"), content_type))
        )
        # Send the POST request with multiple files in the dictionary
        response = client.post("/upload", files=files)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": f"{file_name_list[0]} filename duplicated"
        }

        # Clean up temporary files
        for file_name in file_name_list:
            os.remove(file_name)


def test_upload_ok(mocker):
    """test upload"""

    mocker.patch("app.storage.storage.Storage.upload_file_data")
    mocker.patch(
        "minio.Minio.presigned_get_object",
        return_value="http://test",
    )

    # file format error
    with TestClient(app) as client:
        files = []  # List to store httpx.MultipartFile objects
        file_name_list: list[str] = []
        content_type = "application/pdf"

        # Create three temporary files with different content
        for i in range(2):
            file_name = f"test_file_{i}.pdf"
            file_name_list.append(file_name)
            with open(file_name, "wb") as f:
                f.write(f"This is test content {i}".encode())
                files.append(
                    ("files", (file_name, open(file_name, "rb"), content_type))
                )

        # Send the POST request with multiple files in the dictionary
        response = client.post("/upload", files=files)
        assert response.status_code == status.HTTP_200_OK

        json_dict: dict = response.json()
        assert "upload_result" in json_dict
        upload_result = json_dict["upload_result"]
        for index, file_name in enumerate(file_name_list):
            file_info = upload_result[index]["file_info"]
            assert file_name == file_info["file_name"]
            assert len(file_info["file_id"]) > 10
            assert file_info["file_unique_name"].startswith(
                file_info["file_id"]
            )

        # assert response.json() == {"upload_result": []}

        # Clean up temporary files
        for file_name in file_name_list:
            os.remove(file_name)


def test_ocr_bad_case_invalid_url(mocker):
    """test ocr"""

    mocker.patch("app.ocr.ocr.Ocr._perform_ocr")

    # no url
    with TestClient(app) as client:
        post_data = {"signed_url": "http:/"}
        response = client.post("/ocr", json=post_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # path invalid
    with TestClient(app) as client:
        post_data = {"signed_url": "http://"}
        response = client.post("/ocr", json=post_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # path invalid
    with TestClient(app) as client:
        post_data = {"signed_url": "http://localhost:9000"}
        response = client.post("/ocr", json=post_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": "signed_url split path len not valid, /"
        }

    # path invalid
    with TestClient(app) as client:
        post_data = {"signed_url": "http://localhost:9000/rag/"}
        response = client.post("/ocr", json=post_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": "signed_url split path len not valid, /rag/"
        }

    # path invalid
    with TestClient(app) as client:
        post_data = {"signed_url": f"http://localhost:9000/rag/{FILE_ID}"}
        response = client.post("/ocr", json=post_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": f"signed_url split path len not valid, /rag/{FILE_ID}"
        }

    # path invalid
    with TestClient(app) as client:
        post_data = {"signed_url": f"http://localhost:9000/rag/{FILE_ID}___"}
        response = client.post("/ocr", json=post_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": f"signed_url split path, filename part is empty"
            f", /rag/{FILE_ID}___"
        }


def test_ocr_ok(mocker):
    """test ocr"""

    mocker.patch("app.ocr.ocr.Ocr._perform_ocr")

    with TestClient(app) as client:
        post_data = {"signed_url": SIGNED_URL}
        response = client.post("/ocr", json=post_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "status": "processing",
            "file_id": FILE_ID,
        }


def test_ocr_progress_bad_case():
    """test ocr_progress"""

    with TestClient(app) as client:
        bad_file_id = "1"
        response = client.get(f"/ocr_progress/{bad_file_id}")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    with TestClient(app) as client:
        bad_file_id = "1234567890"
        response = client.get(f"/ocr_progress/{bad_file_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": f"{bad_file_id} file_id not found"}


def test_extract_bad_case_payload_invalid(mocker):
    """test extract"""

    answer = "my_answer"
    mocker.patch(
        "app.extract.extract.Extract.generate_answer", return_value=answer
    )

    # payload query len invalid
    with TestClient(app) as client:
        post_data = {"query": "my"}
        response = client.post("/extract", json=post_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # payload file_id len invalid
    with TestClient(app) as client:
        post_data = {"query": "query ok", "file_id": "bad"}
        response = client.post("/extract", json=post_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # payload api invalid
    with TestClient(app) as client:
        post_data = {"query": "query ok", "file_id": FILE_ID, "api": "bad"}
        response = client.post("/extract", json=post_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # payload miss param
    with TestClient(app) as client:
        post_data = {"query": "query ok"}
        response = client.post("/extract", json=post_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # payload miss param
    with TestClient(app) as client:
        post_data = {"file_id": FILE_ID}
        response = client.post("/extract", json=post_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_extract_ok(mocker):
    """test extract"""

    answer = "my_answer"
    mocker.patch(
        "app.extract.extract.Extract.generate_answer", return_value=answer
    )

    with TestClient(app) as client:
        post_data = {"query": "my_query", "file_id": FILE_ID}
        response = client.post("/extract", json=post_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"answer": answer}

    with TestClient(app) as client:
        post_data = {"query": "my_query", "file_id": FILE_ID, "api": "OpenAI"}
        response = client.post("/extract", json=post_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"answer": answer}

    with TestClient(app) as client:
        post_data = {"query": "my_query", "file_id": FILE_ID, "api": "hunyuan"}
        response = client.post("/extract", json=post_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"answer": answer}
