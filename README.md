```markdown
# image-bridge (MCP Tool)

一个用于 Model Context Protocol (MCP) 的轻量级工具，解决当前 MCP 工具（例如 chrome-devtools-mcp）返回的 `type=image` 文件无法被多模态模型识别的问题。

`image-bridge` 的作用是：

**将 MCP 工具返回的本地图片文件转换为多模态模型可直接使用的 `image_url`（data URL / base64）格式。**

这样模型才能真正“看到”截图，而不是像现在这样只能看到文件名、markdown 或文本描述。

---

## ✨ 背景问题 / Background

目前 MCP 工具（例如 `take_screenshot`）返回的图片格式如下：

```json
{
  "type": "image",
  "fileName": "image-xxxx.png",
  "mimeType": "image/png",
  "markdown": "![Image](./image-xxxx.png)"
}
```

但多模态模型（GPT‑4o、Claude、Qwen 等）**无法读取本地文件，也不会把 markdown 当作视觉输入**。

模型真正需要的是：

```json
{
  "type": "image_url",
  "image_url": { "url": "data:image/png;base64,..." }
}
```

因此模型会出现“幻觉式视觉回答”，声称自己看到了截图，但实际上完全没有看到。

---

## 🚀 功能 / Features

- 将本地图片文件读取为二进制
- 自动推断 MIME 类型
- 转换为 base64
- 生成多模态模型可识别的 `data:image/...;base64,...` URL
- 返回标准的 `image_url` 消息结构（JSON 字符串）

---

## 📦 安装 / Installation

```bash
git clone https://github.com/mingxing0769/image-bridge
cd image-bridge
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
pip install mcp
```

---

## 🛠️ 使用方法 / Usage

在你的 MCP 客户端配置中加入：

```json
{
  "name": "image-bridge",
  "command": "python",
  "args": ["server.py"]
}
```

然后在 LLM 调用链中：

1. 使用 `take_screenshot` 获取文件名，例如：

   ```
   image-1772982036654.png
   ```

2. 调用本工具：

```json
{
  "tool": "image_file_to_image_url",
  "arguments": {
    "filePath": "./image-1772982036654.png"
  }
}
```

3. 工具返回：

```json
{
  "type": "image_url",
  "image_url": {
    "url": "data:image/png;base64,...."
  }
}
```

4. 将其作为下一轮消息传给多模态模型，即可真正看到图片。

---

## 🧩 工具 API / Tool API

### `image_file_to_image_url(filePath: str) -> str`

**参数：**

- `filePath`：图片文件路径（来自 MCP 工具返回的 fileName）

**返回：**

- JSON 字符串，包含 `type=image_url` 和 base64 data URL

---

## 🧪 示例 / Example

### 输入：

```json
{
  "filePath": "./image-1772982036654.png"
}
```

### 输出：

```json
{
  "type": "image_url",
  "image_url": {
    "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
  }
}
```

---

## 🧱 完整代码 / Full Code

```python
import os
import base64
import mimetypes
import json

from mcp.server import Server

server = Server("image-bridge")


@server.tool()
async def image_file_to_image_url(filePath: str) -> str:
    """
    将本地图片文件转换为多模态模型可用的 image_url（data URL 形式）。
    """

    if not os.path.exists(filePath):
        return json.dumps({
            "error": f"file not found: {filePath}"
        }, ensure_ascii=False)

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

    return json.dumps(payload, ensure_ascii=False)


if __name__ == "__main__":
    server.run()
```

---

## 📌 为什么这个工具很重要？

- 解决了 MCP 生态中长期存在的“截图无法被模型看到”的问题  
- 让 chrome-devtools-mcp 的截图功能真正可用  
- 让多模态模型可以执行视觉任务（OCR、识别、统计、理解）  
- 避免模型产生幻觉式视觉回答  
- 让 MCP 工具链更加完整、可用、可靠  

---

## 📝 License

MIT License

---

## ❤️ 作者 / Author

**mingxing0769（建平）**

欢迎提交 Issue 或 PR，一起完善 MCP 生态。
```

---
