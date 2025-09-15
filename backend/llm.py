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
        
    from typing import Union  # 添加导入
    
    async def generate_response(
        self, 
        message: str,
        temperature: float = 0.7,
        max_retries: int = 3,
        is_json: bool = False
    ) -> Union[str, Dict]:
        """
        异步生成响应。
    
        Args:
            message (str): 用户输入的消息。
            temperature (float, optional): 温度参数，控制生成文本的随机性。默认为0.7。
            max_retries (int, optional): 最大重试次数。默认为3。
            is_json (bool, optional): 是否返回JSON格式的响应。默认为False。
    
        Returns:
            Union[str, Dict]: 生成的响应文本或解析后的JSON对象。
        """
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
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
                    
                    raw_response = self._parse_response(result)
                    print("parsed_response:", raw_response)
                    
                    if is_json:
                        return self._parse_json_response(raw_response)  # 返回 Dict
                    else:
                        return raw_response  # 返回 str
                        
            except Exception as e:
                retry_count += 1
                print(f"LLM Error (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    await asyncio.sleep(1)
        
        raise Exception(f"Failed to get response from LLM after {max_retries} attempts")


    @staticmethod
    def _parse_json_response(raw_response: str) -> Dict:
        """
        解析 JSON 格式的响应，支持多种格式和包含思考过程的响应
        
        Args:
            raw_response (str): 原始响应字符串
            
        Returns:
            Dict: 解析后的 JSON 对象
            
        Raises:
            ValueError: 当无法解析 JSON 时抛出异常
        """
        try:
            cleaned_response = raw_response.strip()
            
            # 处理<think>标签的情况
            # 移除<think>...</think>部分
            if "<think>" in cleaned_response and "</think>" in cleaned_response:
                # 使用正则表达式移除<think>标签及其内容
                cleaned_response = re.sub(r'<think>.*?</think>', '', cleaned_response, flags=re.DOTALL).strip()
            
            # 处理XML风格标签（如果还有其他类似标签）
            cleaned_response = re.sub(r'<[^>]+>', '', cleaned_response).strip()
            
            # 如果有多个JSON对象，尝试找到最后一个完整的JSON
            if "```json" in cleaned_response:
                # 提取最后一个代码块中的内容
                matches = re.findall(r"```json\s*(.*?)\s*```", cleaned_response, re.DOTALL)
                if matches:
                    cleaned_response = matches[-1]  # 取最后一个匹配项
            elif "```" in cleaned_response:
                # 处理其他代码块标记
                matches = re.findall(r"```\s*(.*?)\s*```", cleaned_response, re.DOTALL)
                if matches:
                    cleaned_response = matches[-1]
            
            # 尝试从文本中提取JSON对象
            # 查找第一个 { 和最后一个 } 之间的内容
            start = cleaned_response.find('{')
            end = cleaned_response.rfind('}')
            if start != -1 and end != -1 and start < end:
                cleaned_response = cleaned_response[start:end+1]
            
            # 如果还是没有找到有效的JSON格式，尝试其他方法
            if not cleaned_response.startswith('{') or not cleaned_response.endswith('}'):
                # 尝试找到任何可能的JSON对象
                json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned_response)
                if json_matches:
                    cleaned_response = json_matches[-1]  # 取最后一个匹配的JSON对象
            
            # 解析 JSON
            return json.loads(cleaned_response)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON response: {str(e)}. Raw response: {raw_response[:200]}...")