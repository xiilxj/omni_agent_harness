"""
Unit Tests for File & Image Upload and Multimodal Payload Generation
"""

import io
import uuid
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from harness.ui.app import create_app
from harness.core.models import Message
from harness.providers.openai_provider import OpenAICompatibleProvider
from harness.tools.uploader import save_upload_bytes, encode_image_to_data_uri, is_image_file


def test_uploader_save_and_encode(tmp_path: Path):
    """测试文件保存与 Base64 编码"""
    # 1. 保存文本文件
    txt_bytes = b"Hello, Antigravity Omni Agent!"
    res_txt = save_upload_bytes(txt_bytes, "test_doc.txt", tmp_path, session_id="sess_123")
    assert "test_doc" in res_txt["name"]
    assert res_txt["is_image"] is False
    assert Path(res_txt["path"]).exists()
    assert Path(res_txt["path"]).read_bytes() == txt_bytes

    # 2. 保存图片文件
    img_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    res_img = save_upload_bytes(img_bytes, "sample.png", tmp_path, session_id="sess_123")
    assert "sample" in res_img["name"]
    assert res_img["is_image"] is True
    assert res_img["mime_type"] == "image/png"

    # 3. Base64 编码测试
    b64_uri = encode_image_to_data_uri(res_img["path"])
    assert b64_uri is not None
    assert b64_uri.startswith("data:image/png;base64,")


def test_api_upload_and_raw_endpoints(tmp_path: Path):
    """测试 FastAPI /api/upload 与 /api/uploads/raw 接口"""
    app = create_app()
    client = TestClient(app)

    # 1. 上传文件 (使用唯一文件名避免冲突)
    fname = f"script_{uuid.uuid4().hex[:6]}.py"
    file_content = b"print('Hello World from uploaded code!')"
    files = {"file": (fname, io.BytesIO(file_content), "text/x-python")}
    session_id = f"test_session_{uuid.uuid4().hex[:6]}"
    response = client.post("/api/upload", files=files, data={"session_id": session_id})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    uploaded_name = data["file"]["name"]
    assert uploaded_name.startswith("script_")

    # 2. 读取上传的静态文件
    raw_res = client.get(f"/api/uploads/raw?filename={uploaded_name}&session_id={session_id}")
    assert raw_res.status_code == 200
    assert raw_res.content == file_content


def test_openai_multimodal_payload_conversion(tmp_path: Path):
    """测试将附带图片的 Message 转换为 OpenAI/Gemini 规范的多模态 payload"""
    img_path = tmp_path / "mock.png"
    img_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

    provider = OpenAICompatibleProvider(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key="test_key"
    )

    msg = Message(
        role="user",
        content="请帮我分析这张图片",
        attachments=[
            {
                "name": "mock.png",
                "path": str(img_path),
                "is_image": True
            },
            {
                "name": "data.csv",
                "path": "/tmp/data.csv",
                "size": 512,
                "is_image": False
            }
        ]
    )

    payload = provider._convert_messages_to_payload([msg])
    assert len(payload) == 1
    assert payload[0]["role"] == "user"
    content_list = payload[0]["content"]
    assert isinstance(content_list, list)
    assert content_list[0]["type"] == "text"
    assert "请帮我分析这张图片" in content_list[0]["text"]
    assert "data.csv" in content_list[0]["text"]
    assert content_list[1]["type"] == "image_url"
    assert content_list[1]["image_url"]["url"].startswith("data:image/png;base64,")
