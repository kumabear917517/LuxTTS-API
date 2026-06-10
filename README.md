# LuxTTS
<p align="center">
  <a href="https://huggingface.co/YatharthS/LuxTTS">
    <img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Model-FFD21E" alt="Hugging Face Model">
  </a>
  &nbsp;
  <a href="https://huggingface.co/spaces/YatharthS/LuxTTS">
    <img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Space-blue" alt="Hugging Face Space">
  </a>
  &nbsp;
  <a href="https://colab.research.google.com/drive/1cDaxtbSDLRmu6tRV_781Of_GSjHSo1Cu?usp=sharing">
    <img src="https://img.shields.io/badge/Colab-Notebook-F9AB00?logo=googlecolab&logoColor=white" alt="Colab Notebook">
  </a>
</p>

LuxTTS is an lightweight zipvoice based text-to-speech model designed for high quality voice cloning and realistic generation at speeds exceeding 150x realtime.

https://github.com/user-attachments/assets/a3b57152-8d97-43ce-bd99-26dc9a145c29


### The main features are
- Voice cloning: SOTA voice cloning on par with models 10x larger.
- Clarity: Clear 48khz speech generation unlike most TTS models which are limited to 24khz.
- Speed: Reaches speeds of 150x realtime on a single GPU and faster then realtime on CPU's as well.
- Efficiency: Fits within 1gb vram meaning it can fit in any local gpu.

## Usage
You can try it locally, colab, or spaces.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1cDaxtbSDLRmu6tRV_781Of_GSjHSo1Cu?usp=sharing)
[![Open in Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/YatharthS/LuxTTS)

#### Simple installation:
```
git clone https://github.com/ysharma3501/LuxTTS.git
cd LuxTTS
pip install -r requirements.txt
```

#### Load model:
```python
from zipvoice.luxvoice import LuxTTS

# load model on GPU
lux_tts = LuxTTS('YatharthS/LuxTTS', device='cuda')

# load model on CPU
# lux_tts = LuxTTS('YatharthS/LuxTTS', device='cpu', threads=2)

# load model on MPS for macs
# lux_tts = LuxTTS('YatharthS/LuxTTS', device='mps')
```

#### Simple inference
```python
import soundfile as sf
from IPython.display import Audio

text = "Hey, what's up? I'm feeling really great if you ask me honestly!"

## change this to your reference file path, can be wav/mp3
prompt_audio = 'audio_file.wav'

## encode audio(takes 10s to init because of librosa first time)
encoded_prompt = lux_tts.encode_prompt(prompt_audio, rms=0.01)

## generate speech
final_wav = lux_tts.generate_speech(text, encoded_prompt, num_steps=4)

## save audio
final_wav = final_wav.numpy().squeeze()
sf.write('output.wav', final_wav, 48000)

## display speech
if display is not None:
  display(Audio(final_wav, rate=48000))
```

#### Inference with sampling params:
```python
import soundfile as sf
from IPython.display import Audio

text = "Hey, what's up? I'm feeling really great if you ask me honestly!"

## change this to your reference file path, can be wav/mp3
prompt_audio = 'audio_file.wav'

rms = 0.01 ## higher makes it sound louder(0.01 or so recommended)
t_shift = 0.9 ## sampling param, higher can sound better but worse WER
num_steps = 4 ## sampling param, higher sounds better but takes longer(3-4 is best for efficiency)
speed = 1.0 ## sampling param, controls speed of audio(lower=slower)
return_smooth = False ## sampling param, makes it sound smoother possibly but less cleaner
ref_duration = 5 ## Setting it lower can speedup inference, set to 1000 if you find artifacts.

## encode audio(takes 10s to init because of librosa first time)
encoded_prompt = lux_tts.encode_prompt(prompt_audio, duration=ref_duration, rms=rms)

## generate speech
final_wav = lux_tts.generate_speech(text, encoded_prompt, num_steps=num_steps, t_shift=t_shift, speed=speed, return_smooth=return_smooth)

## save audio
final_wav = final_wav.numpy().squeeze()
sf.write('output.wav', final_wav, 48000)

## display speech
if display is not None:
  display(Audio(final_wav, rate=48000))
```
## Tips
- Please use at minimum a 3 second audio file for voice cloning.
- You can use return_smooth = True if you hear metallic sounds.
- Lower t_shift for less possible pronunciation errors but worse quality and vice versa.

---

## API 接口

服务启动后（`runapi.bat` 或 `python app.py`），提供以下 HTTP 接口，默认端口 `7860`。

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

**curl（命令行）：**
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

### 其他地址

| 路径 | 说明 |
|---|---|
| `http://127.0.0.1:7860/` | 自动跳转到 Gradio UI |
| `http://127.0.0.1:7860/ui/` | Gradio Web UI |
| `http://127.0.0.1:7860/docs` | Swagger 交互式 API 文档 |

### 注意事项

- 参考音频至少 3 秒，越清晰克隆效果越好
- 如果出现"吞字/断词"，请降低语速（`speed`）或增大参考音频时长（`ref_duration`）

### 踩坑记录：Windows 中文编码问题

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


## Info

Q: How is this different from ZipVoice?

A: LuxTTS uses the same architecture but distilled to 4 steps with an improved sampling technique. It also uses a custom 48khz vocoder instead of the default 24khz version.

Q: Can it be even faster?

A: Yes, currently it uses float32. Float16 should be significantly faster(almost 2x).

## Roadmap

- [x] Release model and code
- [x] Huggingface spaces demo
- [x] Release MPS support (thanks to @builtbybasit)
- [ ] Release code for float16 inference

## Acknowledgments

- [ZipVoice](https://github.com/k2-fsa/ZipVoice) for their excellent code and model.
- [Vocos](https://github.com/gemelo-ai/vocos.git) for their great vocoder.
  
## Final Notes

The model and code are licensed under the Apache-2.0 license. See LICENSE for details.

Stars/Likes would be appreciated, thank you.

Email: yatharthsharma350@gmail.com
