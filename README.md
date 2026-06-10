# LuxTTS-API

[中文文档](README_CN.md)

A local **FastAPI REST API** and **Gradio Web UI** service for the [LuxTTS](https://github.com/ysharma3501/LuxTTS) voice cloning model.

## Features

- 🎙️ **Voice Cloning API** — Upload reference audio + text, get cloned speech back
- 🖥️ **Gradio Web UI** — Browser-based visual interface
- 📖 **Swagger Docs** — Interactive API documentation with built-in testing
- 🔧 **Encoding Compatibility** — Auto-handles Windows curl GBK encoding for CJK text

## Quick Start

### 1. Setup

Clone the [LuxTTS](https://github.com/ysharma3501/LuxTTS) project and download model weights to the `checkpoints/` directory, then:

```bash
pip install -r requirements.txt
```

### 2. Launch

```bash
python app.py
```

Or double-click `runapi.bat` (Windows).

### 3. Access

| URL | Description |
|---|---|
| `http://127.0.0.1:7860/` | Redirects to Gradio UI |
| `http://127.0.0.1:7860/ui/` | Gradio Web UI |
| `http://127.0.0.1:7860/docs` | Swagger Interactive API Docs |

---

## API Reference

### Health Check

```
GET /api/health
```

**Response:**
```json
{"status": "ok", "device": "cuda"}
```

### Text-to-Speech

```
POST /api/tts
Content-Type: multipart/form-data
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `text` | string | ✅ | — | Text to synthesize |
| `audio_prompt` | file | ✅ | — | Reference audio file (WAV/MP3) |
| `rms` | float | ❌ | 0.01 | Loudness control; higher = louder |
| `ref_duration` | float | ❌ | 5 | Reference audio clip length (seconds); shorter = faster, increase if quality issues |
| `t_shift` | float | ❌ | 0.9 | Timbre shift; higher = better quality but may cause errors |
| `num_steps` | int | ❌ | 4 | Sampling steps; higher = better but slower (3–4 optimal) |
| `speed` | float | ❌ | 0.8 | Speech rate; lower = slower/clearer |
| `return_smooth` | bool | ❌ | false | Enable smooth output; turn on if you hear metallic artifacts |
| `output_format` | string | ❌ | wav | Output format: `wav` or `mp3` (MP3 requires ffmpeg) |

**Response:** Audio file stream (`audio/wav` or `audio/mpeg`)

### Examples

**curl:**
```bash
curl -X POST http://127.0.0.1:7860/api/tts \
  -F "text=Hello, this is a voice cloning test" \
  -F "audio_prompt=@voice_ref.wav" \
  -o output.wav
```

With optional parameters:
```bash
curl -X POST http://127.0.0.1:7860/api/tts \
  -F "text=The weather is really nice today" \
  -F "audio_prompt=@voice_ref.wav" \
  -F "speed=0.7" \
  -F "num_steps=6" \
  -F "output_format=wav" \
  -o output.wav
```

**Python (requests):**
```python
import requests

url = "http://127.0.0.1:7860/api/tts"

with open("voice_ref.wav", "rb") as f:
    resp = requests.post(url, data={
        "text": "Hello, this is a voice cloning test",
        "speed": 0.8,
        "num_steps": 4,
    }, files={
        "audio_prompt": ("ref.wav", f, "audio/wav"),
    })

with open("output.wav", "wb") as out:
    out.write(resp.content)
print("Saved to output.wav")
```

**Python (httpx, async):**
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
    print(f"Saved to {output}")

asyncio.run(tts("Hello, this is a voice cloning test", "voice_ref.wav"))
```

---

## Notes

- Reference audio should be at least 3 seconds; clearer audio = better cloning
- If you encounter skipped words, try lowering `speed` or increasing `ref_duration`

## Troubleshooting: Windows CJK Encoding Issue

**Symptom:** English TTS works fine (curl returns 200), but Chinese/CJK TTS returns 500 Internal Server Error.

**Root cause:** Windows `curl` encodes multipart form fields in GBK by default. FastAPI/uvicorn parses them as latin-1 (per HTTP spec), turning CJK characters into mojibake. The garbled text fails tokenization in the TTS model, producing insufficient audio frames and triggering an exception.

**Encoding chain:**
```
curl sends GBK bytes → FastAPI parses as latin-1 → CJK becomes mojibake → model tokenizer fails → 500
```

**Fix:** Add encoding recovery in the API handler to restore the original bytes:
```python
# latin-1 is a single-byte encoding, encode('latin-1') recovers raw bytes
raw_bytes = text.encode('latin-1')
try:
    text = raw_bytes.decode('utf-8')   # Python clients send UTF-8
except UnicodeDecodeError:
    text = raw_bytes.decode('gbk')     # Windows curl sends GBK
```

**Note:** Python's `requests` library sends multipart as UTF-8 by default and is not affected. This issue only occurs with Windows curl from the command line.

## Acknowledgements

- [LuxTTS](https://github.com/ysharma3501/LuxTTS) — Original voice cloning model
- [ZipVoice](https://github.com/k2-fsa/ZipVoice) — Underlying TTS architecture
- [Vocos](https://github.com/gemelo-ai/vocos.git) — 48kHz vocoder

## License

Apache-2.0
