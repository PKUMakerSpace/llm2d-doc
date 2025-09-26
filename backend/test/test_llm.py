import asyncio
import os
import httpx
import json
import logging

# 配置日志输出
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleLLMClient:
    def __init__(self, api_key: str, api_url: str, model_name: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model_name = model_name
        
    async def chat(self, message: str) -> str:
        """与LLM进行简单对话"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "input": {
                "messages": [
                    {"role": "user", "content": message}
                ]
            },
            "parameters": {}
        }
        
        logger.info(f"发送请求到 {self.api_url}")
        logger.info(f"使用模型: {self.model_name}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.status_code}, Response: {response.text}")
                
            result = response.json()
            logger.info(f"API 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            return result["output"]["text"].strip()

async def main():
    # 使用环境变量中的 API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not api_key:
        raise ValueError("请先设置环境变量 DASHSCOPE_API_KEY")
    
    # 初始化 LLM 客户端
    llm = SimpleLLMClient(
        api_key=api_key,
        api_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        model_name="qwen-plus"
    )
    
    # 发起测试对话
    user_message = "你好，请用中文回复，你是通义千问plus吗？"
    print(f"\n发送消息: {user_message}")
    
    try:
        reply = await llm.chat(user_message)
        print("\n收到回复:")
        print(reply)
    except Exception as e:
        logger.error(f"调用LLM失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())