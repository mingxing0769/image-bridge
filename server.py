import os
import base64
import mimetypes
import json
import aiohttp
import asyncio
from urllib.parse import urlparse
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("image-bridge")

@mcp.tool()
async def image_to_data_url(input: str) -> str:
    """
    将本地图片文件或网络图片链接转换为多模态模型可用的 data URL。
    解决多模态模型无法直接查看网络图片的问题。

    参数:
        input (str): 图片的**本地文件路径**或**网络图片 URL**。
            - 本地路径示例：`"C:/photos/cat.png"`、`"./images/dog.jpg"`（支持绝对/相对路径）
            - 网络 URL 示例：`"https://example.com/image.png"`、`"http://placekitten.com/200/300"`

    返回:
        str: 一个 JSON 字符串，格式如下：
            {
              "type": "image_url",
              "image_url": {
                "url": "data:image/png;base64,...."
              }
            }
        此格式与 OpenAI、Anthropic 等多模态 API 兼容，可直接插入消息内容。
        如果输入无效或处理失败，返回的 JSON 包含 `error` 字段，例如：
            {"error": "File not found: ..."}
            {"error": "Failed to download image from URL, status: 404"}

    使用示例:
        # 处理本地文件
        result1 = await image_to_data_url("./my_photo.jpg")
        # 处理网络图片
        result2 = await image_to_data_url("https://example.com/logo.png")
        # 在消息中使用：
        # {
        #   "role": "user",
        #   "content": [
        #     {"type": "text", "text": "这张图片里有什么？"},
        #     json.loads(result1)
        #   ]
        # }

    注意事项:
        - 支持的图片格式取决于底层库（本地文件由 mimetypes 判断，网络图片根据 Content-Type 或文件扩展名）。
        - 网络图片下载使用 aiohttp，默认超时 10 秒，支持重定向。
        - 生成的 data URL 体积约为原图的 4/3，超大图片可能导致上下文超限，请确保图片尺寸适中。
        - 函数是异步的，调用时请使用 await。
    """
    # 判断输入是本地路径还是 URL
    parsed = urlparse(input)
    is_url = parsed.scheme in ('http', 'https')

    try:
        if is_url:
            # 处理网络图片
            async with aiohttp.ClientSession() as session:
                async with session.get(input, timeout=10) as resp:
                    if resp.status != 200:
                        return json.dumps({"error": f"Failed to download image from URL, status: {resp.status}"}, ensure_ascii=False)
                    data = await resp.read()
                    # 从 Content-Type 或 URL 中获取 MIME 类型
                    content_type = resp.headers.get('Content-Type', '')
                    if content_type.startswith('image/'):
                        mime_type = content_type
                    else:
                        # 回退：根据文件扩展名猜测
                        ext = os.path.splitext(parsed.path)[1]
                        mime_type, _ = mimetypes.guess_type(f"dummy{ext}")
                        if mime_type is None:
                            mime_type = "image/png"  # 默认
        else:
            # 处理本地文件
            if not os.path.exists(input):
                return json.dumps({"error": f"File not found: {input}"}, ensure_ascii=False)
            mime_type, _ = mimetypes.guess_type(input)
            if mime_type is None:
                mime_type = "image/png"
            with open(input, "rb") as f:
                data = f.read()

        # 转换为 base64 data URL
        b64 = base64.b64encode(data).decode("ascii")
        data_url = f"data:{mime_type};base64,{b64}"
        payload = {
            "type": "image_url",
            "image_url": {"url": data_url}
        }
        return json.dumps(payload, ensure_ascii=False)

    except asyncio.TimeoutError:
        return json.dumps({"error": "Timeout while downloading image"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run(transport="stdio")
