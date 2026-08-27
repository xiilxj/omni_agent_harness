"""
File & Image Upload Manager
负责处理 Web 界面上传的图片、文档与代码文件，提供持久化归档与 Base64 多模态 Payload 转换
"""

import base64
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}


def is_image_file(filename: str) -> bool:
    """判断文件是否属于支持预览与 Vision 推理的图片格式"""
    ext = Path(filename).suffix.lower()
    return ext in IMAGE_EXTENSIONS


def get_file_mime_type(file_path: Path) -> str:
    """获取文件 MIME 类型"""
    mime, _ = mimetypes.guess_type(str(file_path))
    if mime:
        return mime
    ext = file_path.suffix.lower()
    if ext == ".png":
        return "image/png"
    elif ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    elif ext == ".webp":
        return "image/webp"
    elif ext == ".gif":
        return "image/gif"
    return "application/octet-stream"


def save_upload_bytes(
    file_bytes: bytes,
    filename: str,
    workspace_dir: Path,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    持久化保存上传的文件字节到工作区专属目录 .omni_uploads/
    """
    safe_filename = os.path.basename(filename).replace(" ", "_")
    target_dir = workspace_dir / ".omni_uploads"
    if session_id:
        target_dir = target_dir / session_id
    target_dir.mkdir(parents=True, exist_ok=True)

    dest_path = target_dir / safe_filename
    
    # 避免文件名冲突
    counter = 1
    stem = dest_path.stem
    ext = dest_path.suffix
    while dest_path.exists():
        dest_path = target_dir / f"{stem}_{counter}{ext}"
        counter += 1

    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    rel_path = str(dest_path.relative_to(workspace_dir))
    mime_type = get_file_mime_type(dest_path)
    is_img = is_image_file(dest_path.name)

    return {
        "name": dest_path.name,
        "path": str(dest_path.resolve()),
        "rel_path": rel_path,
        "size": len(file_bytes),
        "mime_type": mime_type,
        "is_image": is_img,
        "url": f"/api/uploads/raw?filename={dest_path.name}&session_id={session_id or ''}"
    }


def encode_image_to_data_uri(image_path: str) -> Optional[str]:
    """
    将本地图片文件编码为标准 Data URI (Base64) 格式，供 OpenAI/Gemini Vision 模型直接输入
    """
    p = Path(image_path)
    if not p.exists() or not is_image_file(p.name):
        return None

    mime_type = get_file_mime_type(p)
    try:
        with open(p, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime_type};base64,{b64_str}"
    except Exception as e:
        print(f"Warning encoding image {image_path}: {e}")
        return None
