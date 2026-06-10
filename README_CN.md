# LuxTTS-API

[English](README.md)

该项目是为 [LuxTTS](https://github.com/ysharma3501/LuxTTS) 语音克隆模型提供 **FastAPI REST API** 和 **Gradio Web UI** 的本地服务。

## 功能

- 🎙️ **语音克隆 API** — 上传参考音频 + 文本，返回克隆语音
- 🖥️ **Gradio Web UI** — 浏览器可视化操作界面
- 📖 **Swagger 文档** — 交互式 API 文档，可直接在线测试
- 🔧 **编码兼容** — 自动处理 Windows curl 中文 GBK 编码问题

## 快速开始

### 1. 安装

本仓库仅包含 API 层代码，需要先准备原项目环境：

```bash
# 1. 克隆 LuxTTS 原项目
git clone https://github.com/ysharma3501/LuxTTS.git
cd LuxTTS

# 2. 下载模型权重到 checkpoints/ 目录（见原项目说明）

# 3. 安装依赖
pip install -r requirements.txt
```

然后将本仓库的 API 文件复制到 LuxTTS 目录下：

```bash
# 只下载 API 相关文件
curl -O https://raw.githubusercontent.com/kumabear917517/LuxTTS-API/main/app.py
curl -O https://raw.githubusercontent.com/kumabear917517/LuxTTS-API/main/runapi.bat
```

### 2. 启动

```bash
python app.py
```

或双击 `runapi.bat`（Windows）。

### 3. 访问

| 地址 | 说明 |
|---|---|
| `http://127.0.0.1:7860/` | 自动跳转到 Gradio UI |
| `http://127.0.0.1:7860/ui/` | Gradio Web UI |
| `http://127.0.0.1:7860/docs` | Swagger 交互式 API 文档 |

---

## API 接口

### 健康检查

```
GET /api/health
```

**响应示例：**
```json
{"status": "ok", "device": "cuda"}
```

### 语音合成

```
POST /api/tts
Content-Type: multipart/form-data
```

**参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `text` | string | ✅ | — | 待合成的文本 |
| `audio_prompt` | file | ✅ | — | 参考音频文件（WAV/MP3） |
| `rms` | float | ❌ | 0.01 | 响度控制，越大声音越大 |
| `ref_duration` | float | ❌ | 5 | 参考音频截取时长（秒），越小越快，音质异常时可调大 |
| `t_shift` | float | ❌ | 0.9 | 音色偏移，越高音质越好但可能出错 |
| `num_steps` | int | ❌ | 4 | 采样步数，越高越好但越慢（3-4 最佳） |
| `speed` | float | ❌ | 0.8 | 语速，越小越慢/越清晰 |
| `return_smooth` | bool | ❌ | false | 启用平滑输出，有金属音时可开启 |
| `output_format` | string | ❌ | wav | 输出格式：`wav` 或 `mp3`（MP3 需要安装 ffmpeg） |

**响应：** 音频文件流（`audio/wav` 或 `audio/mpeg`）

### 调用示例

**curl：**
```bash
curl -X POST http://127.0.0.1:7860/api/tts \
  -F "text=你好，这是语音克隆的测试效果" \
  -F "audio_prompt=@voice_ref.wav" \
  -o output.wav
```

带可选参数：
```bash
curl -X POST http://127.0.0.1:7860/api/tts \
  -F "text=你好，今天天气真不错" \
  -F "audio_prompt=@voice_ref.wav" \
  -F "speed=0.7" \
  -F "num_steps=6" \
  -F "output_format=wav" \
  -o output.wav
```

**Python（requests）：**
```python
import requests

url = "http://127.0.0.1:7860/api/tts"

with open("voice_ref.wav", "rb") as f:
    resp = requests.post(url, data={
        "text": "你好，这是语音克隆的测试效果",
        "speed": 0.8,
        "num_steps": 4,
    }, files={
        "audio_prompt": ("ref.wav", f, "audio/wav"),
    })

with open("output.wav", "wb") as out:
    out.write(resp.content)
print("已保存到 output.wav")
```

**Python（httpx + 异步）：**
```python
import httpx
import asyncio

async def tts(text: str, ref_audio: str, output: str = "output.wav"):
    async with httpx.AsyncClient(timeout=120) as client:
        with open(ref_audio, "rb") as f:
            resp = await client.post(
                "http://127.0.0.1:7860/api/tts",
                data={"text": text, "speed": "0.8"},
                files={"audio_prompt": ("ref.wav", f, "audio/wav")},
            )
        with open(output, "wb") as out:
            out.write(resp.content)
    print(f"已保存到 {output}")

asyncio.run(tts("你好，这是语音克隆的测试效果", "voice_ref.wav"))
```

---

## 注意事项

- 参考音频至少 3 秒，越清晰克隆效果越好
- 如果出现"吞字/断词"，请降低语速（`speed`）或增大参考音频时长（`ref_duration`）

## 踩坑记录：Windows 中文编码问题

**现象：** 英文 TTS 正常（curl 返回 200），中文 TTS 返回 500 Internal Server Error。

**原因：** Windows 的 `curl` 默认用 GBK 编码发送 multipart form 表单字段中的中文文本。而 FastAPI/uvicorn 底层按 latin-1 解析 multipart 字段，导致中文变成乱码。乱码文本送入 TTS 模型后，分词器无法识别，生成的音频帧数不足，最终抛出异常返回 500。

**编码链路：**
```
curl 发送 GBK bytes → FastAPI 按 latin-1 解析 → 中文变乱码 → 模型分词失败 → 500
```

**修复方法：** 在 API handler 中加入编码修复，将 FastAPI 解析出的乱码文本还原为正确的 UTF-8/GBK：
```python
# latin-1 是单字节编码，encode('latin-1') 可以还原出原始字节
raw_bytes = text.encode('latin-1')
try:
    text = raw_bytes.decode('utf-8')   # Python 客户端发的 UTF-8
except UnicodeDecodeError:
    text = raw_bytes.decode('gbk')     # Windows curl 发的 GBK
```

**注意：** Python 的 `requests` 库默认用 UTF-8 发送 multipart，不受此问题影响。纯 Windows curl 命令行才会触发。

## 致谢

- [LuxTTS](https://github.com/ysharma3501/LuxTTS) — 原始语音克隆模型
- [ZipVoice](https://github.com/k2-fsa/ZipVoice) — 底层 TTS 架构
- [Vocos](https://github.com/gemelo-ai/vocos.git) — 48kHz 声码器

## License

Apache-2.0
