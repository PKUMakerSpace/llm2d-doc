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

# CORS设置，使前端应用（可能部署在与后端不同的域名或端口上）能够正常访问后端API，避免浏览器的同源策略限制。在当前项目中，由于使用了前后端分离架构（有单独的frontend目录），所以需要进行这样的CORS设置来确保前端可以顺利调用后端提供的各种API接口，如聊天接口(/api/chat)和文档上传接口(/api/upload)等。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    #设置允许访问后端API的源（域名），这里使用通配符 * 表示允许所有域名的请求
    allow_methods=["*"],    #设置允许的HTTP方法，包括GET、POST、PUT、DELETE等， * 表示允许所有方法
    allow_headers=["*"],    #设置允许的HTTP请求头， * 表示允许所有请求头。
)

# 请求数据模型
class ChatRequest(BaseModel):
    message: str  # 用户消息内容
    session_id: Optional[str] = "default"  # 会话ID，默认为"default"
    frontend_tts_enabled: Optional[bool] = True  # 前端TTS开关状态，默认为True

# TTS开关请求模型
class TTSRequest(BaseModel):
    enabled: bool  # 是否启用TTS

chat_service = ChatService()  # 初始化聊天服务
tts_service = TTSService(Config.DASHSCOPE_API_KEY, None)  # 初始化TTS服务（通义不需要reference_id）

# 分句分段辅助函数
def split_sentences(text):
    """
    智能分句分段函数，根据文本长度和结构进行合理分割，支持中英文标点
    
    Args:
        text (str): 待分割的文本
        
    Returns:
        list: 分割后的句子列表
    """
    # 先按段落分割（基于换行符）
    paragraphs = re.split(r'\n+', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    result = []
    
    # 针对每个段落进行处理
    for para in paragraphs:
        # 如果段落很短（小于50字符），直接作为一个整体保留
        if len(para) < 50:
            result.append(para)
        else:
            # 对于较长的段落，先尝试按句号分割句子
            # 增强分句逻辑，支持中英文标点符号
            sentences = []
            current = ""
            for char in para:
                current += char
                # 同时处理中英文的句号、感叹号、问号
                if char in ["。", "！", "？", "!", "?", "."]:
                    sentences.append(current)
                    current = ""
            # 处理最后一个没有结束符的句子
            if current.strip():
                sentences.append(current)
            
            # 如果分割后的句子仍然很长（大于100字符），进行二次分割
            for sentence in sentences:
                if len(sentence) > 100:
                    # 增强二次分割逻辑，支持更多中英文标点符号
                    # 分割符包括中英文逗号、分号、冒号等
                    sub_sentences = re.split(r'[,，;；:\uff1a]', sentence)
                    sub_sentences = [s.strip() for s in sub_sentences if s.strip()]
                    
                    # 为分割后的子句添加适当的标点
                    # 根据原句判断是中文还是英文语境，使用相应的标点符号
                    for i, sub_sent in enumerate(sub_sentences):
                        if i < len(sub_sentences) - 1:
                            # 检查原句是否包含较多中文字符，决定使用中文还是英文标点
                            # 计算中文字符比例
                            chinese_chars = sum(1 for c in sentence if '\u4e00' <= c <= '\u9fff')
                            if chinese_chars / len(sentence) > 0.3:
                                # 中文语境为主，使用中文逗号
                                result.append(sub_sent + "，")
                            else:
                                # 英文语境为主，使用英文逗号
                                result.append(sub_sent + ",")
                        else:
                            result.append(sub_sent)
                else:
                    result.append(sentence)
    
    # 最终清理空句子
    result = [s.strip() for s in result if s.strip()]
    return result

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # 处理聊天请求，目前直接套用normal_chat_flow
    return await normal_chat_flow(request)

# 聊天流程处理函数
async def normal_chat_flow(request: ChatRequest):
    """
    正常的聊天流程处理函数。首先通过chat_service.generate_reply处理传入的message，返回reply文字内容,audio_data语音内容和expression表情内容。
    然后将reply按句子分割，并为每个句子生成对应的语音片段。

    Args:
    request (ChatRequest): 包含聊天请求信息的对象，包括request.message和request.session_id。

    Returns:
    JSONResponse: 包含聊天回复信息的JSON响应对象。

    """
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
    # 只有当config中启用TTS且前端TTS开关也开启时，才生成语音
    if Config.is_tts_enabled() and request.frontend_tts_enabled:
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
        # 否则为整体回复生成一个语音片段（只有当config中启用TTS且前端TTS开关也开启时，才保留语音）
        if Config.is_tts_enabled() and request.frontend_tts_enabled:
            audio_base64 = base64.b64encode(audio_data).decode('ascii') if audio_data else ''
        else:
            audio_base64 = ''  # 如果TTS关闭，返回空字符串
        return JSONResponse(
            content={
                "message": reply,           # 回复文本
                "audio": audio_base64,      # 整体语音
                "expression": expression    # 表情信息
            }
        )

@app.get("/api/tts/status")
async def get_tts_status():
    """
    获取当前TTS开关状态
    """
    return {
        "enabled": Config.TTS_ENABLED,
        "api_key_valid": bool(Config.DASHSCOPE_API_KEY and Config.DASHSCOPE_API_KEY.strip())
    }

@app.post("/api/tts/toggle")
async def toggle_tts(request: TTSRequest):
    """
    切换TTS开关状态
    """
    Config.TTS_ENABLED = request.enabled
    return {
        "enabled": Config.TTS_ENABLED,
        "message": "TTS服务已" + ("启用" if request.enabled else "禁用")
    }

@app.post("/api/upload")
async def upload(file: UploadFile = File(...), frontend_tts_enabled: bool = True):
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

    # 创建保存文档的目录（如果不存在）
    save_dir = os.path.join(os.path.dirname(__file__), 'save', 'doc')
    os.makedirs(save_dir, exist_ok=True)
    
    # 保存处理的文本到txt文件
    # 使用原始文件名（去除扩展名）作为txt文件名
    base_filename = os.path.splitext(file.filename)[0]
    txt_filename = f"{base_filename}.txt"
    txt_path = os.path.join(save_dir, txt_filename)
    
    # 确保中文文件名能正确处理
    try:
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
    except UnicodeEncodeError:
        # 如果文件名有问题，使用时间戳作为备用文件名
        import time
        timestamp = int(time.time())
        fallback_filename = f"document_{timestamp}.txt"
        fallback_path = os.path.join(save_dir, fallback_filename)
        with open(fallback_path, 'w', encoding='utf-8') as f:
            f.write(text)
    
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
        f"{text[:10000]}"  # 只取前4000字符，防止内容过长
    )
    # 调用 LLM 服务生成总结回复
    reply = await chat_service.llm_service.generate_response(prompt)
    
 # 手动将文档总结对话添加到历史记录中
    chat_service.conversation_history.add_dialog(
        f"请总结上传的{suffix}文档内容", 
        reply
    )
    
    # 记录文档总结到日志文件，与chat对话一样
    chat_service.main_agent._log_conversation('user', f"请总结上传的{suffix}文档内容")
    chat_service.main_agent._log_conversation('assistant', reply)

    # Split reply into sentences
    sentences = split_sentences(reply)
    
    # 为每个句子生成语音片段
    audio_segments = []
    # 只有当config中启用TTS且前端TTS开关也开启时，才生成语音
    if Config.is_tts_enabled() and frontend_tts_enabled:
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
        # 只有当config中启用TTS且前端TTS开关也开启时，才生成语音
        if Config.is_tts_enabled() and frontend_tts_enabled:
            audio_data = tts_service.generate_audio(reply)
        # 转为 base64 字符串
        audio_base64 = base64.b64encode(audio_data).decode('ascii') if audio_data else ''
        
        return {
            "summary": reply,           # 总结文本
            "audio": audio_base64       # 总结整体语音
        }