import requests
import os

url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

payload = {
    "model": "glm-4-flash",
    "messages": [
        {
            "role": "system",
            "content": "你是一个有用的AI助手。"
        },
        {
            "role": "user",
            "content": "你是智谱glm吗"
        }
    ],
    "temperature": 0.6,
   
    "stream": False
}
headers = {
    "Authorization":f"Bearer {os.getenv('ZHIPU_API_KEY')}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())