"""
LLMService 模块

该模块提供了一个与大语言模型 (LLM) API 交互的异步服务类。
主要功能包括：
1. 向 LLM API 发送请求并获取响应
2. 处理不同格式的响应（普通文本或 JSON）
3. 实现重试机制以提高请求的稳定性
4. 支持解析 JSON 格式的响应内容

支持多种风格的 LLM API，包括 OpenAI 风格和 DashScope 风格。
"""

import httpx
import asyncio
from typing import List, Dict
import json
import re

# 模型风格分类
MODEL_STYLE_OPENAI = ["deepseek-chat", "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]
MODEL_STYLE_DASHSCOPE = ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-vl-plus", "qwen-vl-max"]

def get_model_style(model: str) -> str:
    """
    根据模型名称获取模型风格
    
    Args:
        model (str): 模型名称
        
    Returns:
        str: 模型风格 ("openai" 或 "dashscope")
        
    Raises:
        ValueError: 不支持的模型
    """
    if model in MODEL_STYLE_OPENAI:
        return "openai"
    elif model in MODEL_STYLE_DASHSCOPE:
        return "dashscope"
    else:
        # 默认使用 OpenAI 风格
        return "openai"

class LLMService:
    def __init__(self, api_key: str, api_url: str, model: str = "deepseek-chat"):
        """
        初始化 LLM 服务
        
        Args:
            api_key (str): API 访问密钥
            api_url (str): API 端点 URL
            model (str): 模型名称，默认为 "deepseek-chat"
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.model_style = get_model_style(model)
    
    def _build_openai_request(self, message: str, temperature: float) -> dict:
        """构建 OpenAI 风格的请求体"""
        return {
            "model": self.model,
            "messages": [
                {"role": "user", "content": message}
            ],
            "temperature": temperature
        }
    
    def _build_dashscope_request(self, message: str, temperature: float) -> dict:
        """构建 DashScope 风格的请求体"""
        return {
            "model": self.model,
            "input": {
                "messages": [
                    {"role": "user", "content": message}
                ]
            },
            "parameters": {
                "temperature": temperature
            }
        }
    
    def _build_request(self, message: str, temperature: float) -> dict:
        """根据模型风格构建请求体"""
        if self.model_style == "openai":
            return self._build_openai_request(message, temperature)
        elif self.model_style == "dashscope":
            return self._build_dashscope_request(message, temperature)
        else:
            # 默认使用 OpenAI 风格
            return self._build_openai_request(message, temperature)
    
    def _parse_openai_response(self, response: dict) -> str:
        """解析 OpenAI 风格的响应"""
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"].strip()
        else:
            raise ValueError(f"Unexpected response structure: {response}")
    
    def _parse_dashscope_response(self, response: dict) -> str:
        """解析 DashScope 风格的响应"""
        if "output" in response and "text" in response["output"]:
            return response["output"]["text"].strip()
        else:
            raise ValueError(f"Unexpected response structure: {response}")
    
    def _parse_response(self, response: dict) -> str:
        """根据模型风格解析响应"""
        if self.model_style == "openai":
            return self._parse_openai_response(response)
        elif self.model_style == "dashscope":
            return self._parse_dashscope_response(response)
        else:
            # 默认使用 OpenAI 风格
            return self._parse_openai_response(response)
        
    async def generate_response(
        self, 
        message: str,
        temperature: float = 0.7,
        max_retries: int = 3,
        is_json: bool = False
    ) -> str:
        """
        异步生成响应。

        Args:
            message (str): 用户输入的消息。
            temperature (float, optional): 温度参数，控制生成文本的随机性。默认为0.7。
            max_retries (int, optional): 最大重试次数。默认为3。
            is_json (bool, optional): 是否返回JSON格式的响应。默认为False。

        Returns:
            str: 生成的响应文本。

        Raises:
            Exception: 如果在重试次数内未能成功生成响应，则抛出异常。
        """
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    # 根据模型风格构建请求体
                    request_body = self._build_request(message, temperature)
                    
                    response = await client.post(
                        self.api_url,
                        json=request_body,
                        headers=headers
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"LLM API error: {response.status_code}")
                    
                    result = response.json()
                    print("raw_response:", result)
                    
                    # 根据模型风格解析响应
                    raw_response = self._parse_response(result)
                    print("parsed_response:", raw_response)
                    
                    if is_json:
                        return self._parse_json_response(raw_response)
                    else:
                        return raw_response
                        
            except Exception as e:
                retry_count += 1
                print(f"LLM Error (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    await asyncio.sleep(1)
        
        # 如果所有重试都失败了，抛出异常
        raise Exception(f"Failed to get response from LLM after {max_retries} attempts")

    @staticmethod
    def _parse_json_response(raw_response: str) -> Dict:
        """
        解析 JSON 格式的响应
        
        Args:
            raw_response (str): 原始响应字符串
            
        Returns:
            Dict: 解析后的 JSON 对象
            
        Raises:
            ValueError: 当无法解析 JSON 时抛出异常
        """
        try:
            return json.loads(raw_response)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON response: {str(e)}")