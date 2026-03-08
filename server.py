import os
import base64
import mimetypes
import json

from mcp.server import Server
from mcp.types import Tool, TextContent, Content

server = Server("image-bridge")


@server.tool()
async def image_file_to_image_url(filePath: str) -> str:
    """
    将本地图片文件转换为多模态模型可用的 image_url（data URL 形式）。

    参数:
        filePath: 图片文件路径，例如 ./image-1772982036654.png

    返回:
        JSON 字符串，形如：
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/png;base64,...."
          }
        }
    """
    if not os.path.exists(filePath):
        return json.dumps({
            "error": f"file not found: {filePath}"
        }, ensure_ascii=False)

    # 猜测 MIME 类型
    mime_type, _ = mimetypes.guess_type(filePath)
    if mime_type is None:
        mime_type = "image/png"

    with open(filePath, "rb") as f:
        data = f.read()

    b64 = base64.b64encode(data).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64}"

    payload = {
        "type": "image_url",
        "image_url": {
            "url": data_url
        }
    }

    # 返回 JSON 字符串，方便 LLM 直接解析
    return json.dumps(payload, ensure_ascii=False)


if __name__ == "__main__":
    # 以 stdio 方式运行 MCP server
    server.run()
