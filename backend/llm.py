"""
LLMService 模块

该模块提供了一个与大语言模型 (LLM) API 交互的异步服务类。
主要功能包括：
1. 向 LLM API 发送请求并获取响应
2. 处理不同格式的响应（普通文本或 JSON）
3. 实现重试机制以提高请求的稳定性
4. 支持解析 JSON 格式的响应内容

当前实现主要针对 DeepSeek API，但也适用于其他兼容 OpenAI 格式的 API。
"""

import httpx
import asyncio
from typing import List, Dict
import json
import re

class LLMService:
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
    
        
    async def generate_response(
        self, 
        message: str,
        temperature: float = 0.7,
        max_retries: int = 3,
        is_json: bool = False
    ) -> str:
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    response = await client.post(
                        self.api_url,
                        json={
                            "model": "deepseek-chat",
                            "messages": [
                                {"role": "user", "content": message}
                            ],
                            "temperature": temperature
                        },
                        headers=headers
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"LLM API error: {response.status_code}")
                    
                    result = response.json()
                    # DeepSeek/OpenAI风格
                    if "choices" in result and len(result["choices"]) > 0:
                        raw_response = result["choices"][0]["message"]["content"].strip()
                    else:
                        raise ValueError(f"Unexpected response structure: {result}")
                    print("raw_response:", raw_response)
                    if is_json:
                        return self._parse_json_response(raw_response)
                    else:
                        return raw_response
                        
            except Exception as e:
                retry_count += 1
                print(f"LLM Error (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    await asyncio.sleep(1)

    @staticmethod
    def _parse_json_response(raw_response: str) -> Dict:
        try:
            return json.loads(raw_response)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON response: {str(e)}")
