from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import base64
import tempfile
import os
import re

from chat_service import ChatService
from tts import TTSService
from config import Config
from docx import Document
import PyPDF2

app = FastAPI()

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

chat_service = ChatService()
tts_service = TTSService(Config.FISH_API_KEY, Config.FISH_REFERENCE_ID)

# Add this helper function
def split_sentences(text):
    # Split by common sentence ending punctuation
    sentences = re.split(r'[。！？\?!]', text)
    # Filter out empty sentences and strip whitespace
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

@app.post("/api/chat")
async def chat(request: ChatRequest):
    return await normal_chat_flow(request)

async def normal_chat_flow(request: ChatRequest):
    reply, audio_data, expression = await chat_service.generate_reply(
        request.message, 
        request.session_id
    )
    
    print("-- /api/chat --")
    print("reply:", reply)
    print("expression:", expression)

    # Split reply into sentences
    sentences = split_sentences(reply)
    
    # Try to generate audio for each sentence
    audio_segments = []
    if Config.is_tts_enabled():
        for sentence in sentences:
            sentence_audio = tts_service.generate_audio(sentence)
            if sentence_audio:
                audio_segments.append(base64.b64encode(sentence_audio).decode('ascii'))
    
    # If we have separate audio segments, return them; otherwise use single audio
    if audio_segments and len(audio_segments) == len(sentences):
        return JSONResponse(
            content={
                "message": reply,
                "sentences": sentences,
                "audio_segments": audio_segments,
                "expression": expression
            }
        )
    else:
        # Fallback to single audio file
        audio_base64 = base64.b64encode(audio_data).decode('ascii') if audio_data else ''
        return JSONResponse(
            content={
                "message": reply,
                "audio": audio_base64,
                "expression": expression
            }
        )

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    # 保存临时文件
    suffix = os.path.splitext(file.filename)[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # 读取文本内容
    text = ""
    if suffix == ".pdf":
        with open(tmp_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    elif suffix in [".doc", ".docx"]:
        doc = Document(tmp_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    else:
        text = content.decode("utf-8", errors="ignore")

    os.remove(tmp_path)

    # 用 LLM 总结，加入性格设定
    character_setting = "你是一个温柔、乐观、喜欢用比喻和鼓励的话语和用户交流的虚拟助手。"
    prompt = (
        f"{character_setting}\n"
        "请用自然口语、完整段落、不要列表、不要星号、不要编号，像和朋友聊天一样总结以下文档内容。"
        "表达要富有情感和语气，适当使用强调和重音词汇，让听起来更像真人说话：\n"
        f"{text[:4000]}"
    )
    reply = await chat_service.llm_service.generate_response(prompt)
    
    # Split reply into sentences
    sentences = split_sentences(reply)
    
    # Generate audio for each sentence
    audio_segments = []
    if Config.is_tts_enabled():
        for sentence in sentences:
            audio_data = tts_service.generate_audio(sentence)
            if audio_data:
                audio_segments.append(base64.b64encode(audio_data).decode('ascii'))
    
    # If we have separate audio segments, return them; otherwise generate one for the whole text
    if audio_segments and len(audio_segments) == len(sentences):
        return {
            "summary": reply,
            "sentences": sentences,
            "audio_segments": audio_segments
        }
    else:
        # Fallback to single audio file
        audio_data = None
        if Config.is_tts_enabled():
            audio_data = tts_service.generate_audio(reply)
        audio_base64 = base64.b64encode(audio_data).decode('ascii') if audio_data else ''
        
        return {
            "summary": reply,
            "audio": audio_base64
        }