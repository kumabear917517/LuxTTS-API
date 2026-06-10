import io
import sys
import time
import tempfile
from pathlib import Path

import os
import warnings
warnings.filterwarnings('ignore')

# ===================== 核心：代码内设置 HF 镜像 =====================
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import numpy as np
import gradio as gr
import torch
import uvicorn
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from gradio import mount_gradio_app
from zipvoice.luxvoice import LuxTTS

# Init Model
device = "cuda" if torch.cuda.is_available() else "cpu"
lux_tts = LuxTTS("checkpoints", device=device, threads=2)


def infer(
    text,
    audio_prompt,
    rms,
    ref_duration,
    t_shift,
    num_steps,
    speed,
    return_smooth,
):
    if audio_prompt is None or not text:
        return None, "❗ 请同时输入文本和参考音频"

    start_time = time.time()

    # Encode reference
    encoded_prompt = lux_tts.encode_prompt(
        audio_prompt,
        duration=ref_duration,
        rms=rms,
    )

    # Generate speech
    final_wav = lux_tts.generate_speech(
        text,
        encoded_prompt,
        num_steps=int(num_steps),
        t_shift=t_shift,
        speed=speed,
        return_smooth=return_smooth,
    )

    duration = round(time.time() - start_time, 2)

    final_wav = final_wav.cpu().squeeze(0).numpy()
    final_wav = (np.clip(final_wav, -1.0, 1.0) * 32767).astype(np.int16)

    stats_msg = f"✨ 生成完成，用时 **{duration} 秒**"
    return (48000, final_wav), stats_msg


# =======================
# FastAPI 接口
# =======================
app = FastAPI(title="LuxTTS API", description="LuxTTS 语音克隆 API")


@app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/ui/")


def _wav_to_bytes(wav_np: np.ndarray, sample_rate: int = 48000) -> bytes:
    """将 int16 numpy 数组写入内存 WAV 并返回 bytes"""
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(wav_np.tobytes())
    return buf.getvalue()


@app.post("/api/tts", summary="语音合成（multipart）")
async def api_tts(
    request: Request,
    audio_prompt: UploadFile = File(..., description="参考音频文件（WAV/MP3 等）"),
    text: str = Form(..., description="待合成文本"),
    rms: float = Form(0.01),
    ref_duration: float = Form(5),
    t_shift: float = Form(0.9),
    num_steps: int = Form(4),
    speed: float = Form(0.8),
    return_smooth: bool = Form(False),
    output_format: str = Form("wav", description="输出格式: wav 或 mp3"),
):
    """通过 multipart/form-data 调用 LuxTTS 进行语音克隆合成。返回音频文件流。"""
    if not text:
        raise HTTPException(status_code=400, detail="文本不能为空")

    # 修复 Windows 下 multipart 中文编码问题：
    print(f'[DEBUG] 原始 text repr: {repr(text)}')
    try:
        raw_bytes = text.encode('latin-1')
        try:
            text = raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            text = raw_bytes.decode('gbk')
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    print(f'[DEBUG] 修复后 text: {text}')

    # 将上传的音频写入临时文件
    suffix = Path(audio_prompt.filename or "ref.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio_prompt.read())
        tmp_path = tmp.name

    try:
        encoded_prompt = lux_tts.encode_prompt(
            tmp_path,
            duration=ref_duration,
            rms=rms,
        )
        final_wav = lux_tts.generate_speech(
            text,
            encoded_prompt,
            num_steps=int(num_steps),
            t_shift=t_shift,
            speed=speed,
            return_smooth=return_smooth,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"合成失败: {str(e)}")
    finally:
        os.unlink(tmp_path)

    final_wav = final_wav.cpu().squeeze(0).numpy()
    final_wav = (np.clip(final_wav, -1.0, 1.0) * 32767).astype(np.int16)

    if output_format.lower() == "mp3":
        try:
            from pydub import AudioSegment
            wav_bytes = _wav_to_bytes(final_wav)
            seg = AudioSegment.from_raw(
                io.BytesIO(wav_bytes).read(),
                sample_width=2,
                frame_rate=48000,
                channels=1,
            )
            mp3_buf = io.BytesIO()
            seg.export(mp3_buf, format="mp3")
            mp3_buf.seek(0)
            return StreamingResponse(
                mp3_buf,
                media_type="audio/mpeg",
                headers={"Content-Disposition": "attachment; filename=tts_output.mp3"},
            )
        except Exception:
            # ffmpeg 不可用时回退到 WAV
            pass

    wav_bytes = _wav_to_bytes(final_wav)
    return StreamingResponse(
        io.BytesIO(wav_bytes),
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=tts_output.wav"},
    )


@app.get("/api/health", summary="健康检查")
async def health():
    return {"status": "ok", "device": device}


# =======================
# Gradio UI
# =======================
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎙️ LuxTTS 语音克隆演示")

    gr.Markdown(
        """
        > **说明：** 当前示例默认运行在 **2 核 CPU** 上，推理速度可能较慢。
        > **使用建议：**
        > - 如果出现"吞字 / 断词"，请 **降低语速（Speed）** 或 **增大参考音频时长**
        > - 参考音频越清晰，克隆效果越稳定
        """
    )

    with gr.Row():
        with gr.Column():
            input_text = gr.Textbox(
                label="待合成文本",
                value="你好，这是一个语音克隆的示例效果。",
            )

            input_audio = gr.Audio(
                label="参考音频（WAV 格式）",
                type="filepath",
            )

            with gr.Row():
                rms_val = gr.Number(
                    value=0.01,
                    label="RMS 音量（响度）",
                )
                ref_duration_val = gr.Number(
                    value=5,
                    label="参考音频时长（秒）",
                    info="越小越快，若出现音质异常可设置较大值（如 10~20）",
                )
                t_shift_val = gr.Number(
                    value=0.9,
                    label="T-Shift（音色偏移）",
                )

            with gr.Row():
                steps_val = gr.Slider(
                    1,
                    10,
                    value=4,
                    step=1,
                    label="采样步数（Steps）",
                )
                speed_val = gr.Slider(
                    0.5,
                    2.0,
                    value=0.8,
                    step=0.1,
                    label="语速（越小越慢 / 越清晰）",
                )
                smooth_val = gr.Checkbox(
                    label="启用平滑输出",
                    value=False,
                )

            btn = gr.Button("开始生成语音", variant="primary")

        with gr.Column():
            audio_out = gr.Audio(label="生成结果")
            status_text = gr.Markdown("🟢 等待生成中…")

    btn.click(
        fn=infer,
        inputs=[
            input_text,
            input_audio,
            rms_val,
            ref_duration_val,
            t_shift_val,
            steps_val,
            speed_val,
            smooth_val,
        ],
        outputs=[audio_out, status_text],
    )

# 将 Gradio 挂载到 FastAPI，路径为 /ui
mount_gradio_app(app, demo, path="/ui")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
