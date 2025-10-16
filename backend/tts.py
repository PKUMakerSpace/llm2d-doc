import os
import requests
import dashscope
from typing import Optional
import time

class TTSService:
    def __init__(self, api_key: str, reference_id: str):
        self.api_key = api_key
        self.reference_id = reference_id
        # 设置API密钥到环境变量或dashscope配置
        dashscope.api_key = api_key if api_key else os.getenv("DASHSCOPE_API_KEY")
    
    def generate_audio(self, text: str) -> bytes:
        max_retries = 3
        retry_delay = 1  # 初始延迟1秒
        
        for attempt in range(max_retries):
            try:
                # 调用通义千问TTS服务
                response = dashscope.MultiModalConversation.call(
                    model="qwen3-tts-flash",
                    api_key=self.api_key if self.api_key else os.getenv("DASHSCOPE_API_KEY"),
                    text=text,
                    voice="Cherry",
                    language_type="Chinese", # 建议与文本语种一致
                    stream=False
                )
                
                # 获取音频URL并下载
                audio_url = response.output.audio.url
                
                # 下载音频数据
                response = requests.get(audio_url)
                response.raise_for_status()  # 检查请求是否成功
                
                return response.content  # 返回音频二进制数据
                
            except Exception as e:
                if attempt < max_retries - 1:  # 如果不是最后一次尝试
                    print(f"TTS Error on attempt {attempt + 1}: {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避，每次失败后等待时间翻倍
                else:
                    print(f"TTS Error: All {max_retries} attempts failed. Last error: {str(e)}")
                    return b""  # 所有重试都失败后返回空音频数据