# main.py
# 
# 项目的主要入口文件，提供后端API服务
# 
# 主要功能包括：
# 1. 提供聊天接口 (/api/chat) - 处理用户聊天请求，生成回复和语音
# 2. 提供文档上传接口 (/api/upload) - 接收并处理用户上传的文档文件，
#    支持PDF、Word文档等格式，自动生成内容总结和语音播报
# 3. 集成TTS（文本转语音）服务，为聊天回复和文档总结生成语音片段
# 4. 支持按句子分割文本并生成对应的语音片段
# 5. 处理跨域请求，使前端能够正常访问后端API
# 
# 使用FastAPI框架构建RESTful API，通过CORS中间件解决跨域问题
# 集成了聊天服务(ChatService)和语音合成服务(TTSService)
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
    message: str  # 用户消息内容
    session_id: Optional[str] = "default"  # 会话ID，默认为"default"

chat_service = ChatService()  # 初始化聊天服务
tts_service = TTSService(Config.FISH_API_KEY, Config.FISH_REFERENCE_ID)  # 初始化TTS服务

# 分句辅助函数
def split_sentences(text):
    # 按常见句末标点分割文本
    sentences = re.split(r'[。！？\?!]', text)
    # 过滤空句并去除首尾空格
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # 处理聊天请求
    return await normal_chat_flow(request)

# 聊天流程处理函数
async def normal_chat_flow(request: ChatRequest):
    # 调用聊天服务生成回复、语音数据和表情
    reply, audio_data, expression = await chat_service.generate_reply(
        request.message, 
        request.session_id
    )
    
    print("-- /api/chat --")  # 打印接口调用信息
    print("reply:", reply)     # 打印回复内容
    print("expression:", expression)  # 打印表情信息

    # 将回复文本按句子分割
    sentences = split_sentences(reply)
    
    # 为每个句子生成语音片段
    audio_segments = []
    if Config.is_tts_enabled():
        for sentence in sentences:
            sentence_audio = tts_service.generate_audio(sentence)  # 生成语音数据
            if sentence_audio:
                # 转为base64字符串，便于前端播放
                audio_segments.append(base64.b64encode(sentence_audio).decode('ascii'))
    
    # 如果每句都生成了语音，则返回分句语音
    if audio_segments and len(audio_segments) == len(sentences):
        return JSONResponse(
            content={
                "message": reply,           # 回复文本
                "sentences": sentences,     # 分句列表
                "audio_segments": audio_segments,  # 每句对应的语音片段
                "expression": expression    # 表情信息
            }
        )
    else:
        # 否则为整体回复生成一个语音片段
        audio_base64 = base64.b64encode(audio_data).decode('ascii') if audio_data else ''
        return JSONResponse(
            content={
                "message": reply,           # 回复文本
                "audio": audio_base64,      # 整体语音
                "expression": expression    # 表情信息
            }
        )

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    # 保存临时文件
    # 获取上传文件的后缀名（如 .pdf, .docx）
    suffix = os.path.splitext(file.filename)[-1].lower()
    # 创建一个临时文件用于保存上传内容
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        # 读取上传文件的全部内容
        content = await file.read()
        # 写入临时文件
        tmp.write(content)
        # 记录临时文件路径
        tmp_path = tmp.name

    # 读取文本内容
    text = ""
    if suffix == ".pdf":
        # 如果是 PDF 文件，使用 PyPDF2 读取每一页的文本
        with open(tmp_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                # 提取每页文本并拼接
                text += page.extract_text() or ""
    elif suffix in [".doc", ".docx"]:
        # 如果是 Word 文档，使用 python-docx 读取所有段落
        doc = Document(tmp_path)
        for para in doc.paragraphs:
            # 拼接每个段落的文本
            text += para.text + "\n"
    else:
        # 其他类型文件，按 utf-8 解码为字符串
        text = content.decode("utf-8", errors="ignore")

    # 删除临时文件，释放空间
    os.remove(tmp_path)

    # 用 LLM 总结，加入性格设定
    # 设定虚拟助手的性格
    character_setting = "你是一个温柔、乐观、喜欢用比喻和鼓励的话语和用户交流的虚拟助手。"
    # 构造用于总结的 prompt，要求自然口语、完整段落等
    prompt = (
        f"{character_setting}\n"
        "请用自然口语、完整段落、不要列表、不要星号、不要编号，像和朋友聊天一样总结以下文档内容。"
        "表达要富有情感和语气，适当使用强调和重音词汇，让听起来更像真人说话：\n"
        f"{text[:4000]}"  # 只取前4000字符，防止内容过长
    )
    # 调用 LLM 服务生成总结回复
    reply = await chat_service.llm_service.generate_response(prompt)
    
 # 手动将文档总结对话添加到历史记录中
    chat_service.conversation_history.add_dialog(
        f"请总结上传的{suffix}文档内容", 
        reply
    )

    # Split reply into sentences
    sentences = split_sentences(reply)
    
    # 为每个句子生成语音片段
    audio_segments = []
    if Config.is_tts_enabled():
        for sentence in sentences:
            # 生成当前句子的语音数据
            audio_data = tts_service.generate_audio(sentence)
            if audio_data:
                # 转为 base64 字符串，便于前端播放
                audio_segments.append(base64.b64encode(audio_data).decode('ascii'))
    
    # 如果每个句子都生成了语音，则返回分句语音
    if audio_segments and len(audio_segments) == len(sentences):
        return {
            "summary": reply,           # 总结文本
            "sentences": sentences,     # 分句列表
            "audio_segments": audio_segments  # 每句对应的语音片段
        }
    else:
        # 否则为整个总结生成一个语音片段
        audio_data = None
        if Config.is_tts_enabled():
            audio_data = tts_service.generate_audio(reply)
        # 转为 base64 字符串
        audio_base64 = base64.b64encode(audio_data).decode('ascii') if audio_data else ''
        
        return {
            "summary": reply,           # 总结文本
            "audio": audio_base64       # 总结整体语音
        }