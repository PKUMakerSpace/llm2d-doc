# API接口规范文档

本文档详细描述了llm2d-doc项目中的前后端API接口规范，包括请求方法、参数、返回格式等信息，为前后端开发提供统一的接口标准。

## 1. 基础信息

- **基础URL**：`http://localhost:8000`（开发环境）
- **内容类型**：`application/json`（除文件上传外）
- **字符编码**：UTF-8

## 2. 接口列表

| 接口路径 | 请求方法 | 功能描述 |
|---------|---------|---------|
| `/api/chat` | POST | 处理用户聊天消息，返回AI回复、表情和可选的语音 |
| `/api/upload` | POST | 上传并处理文档，返回文档总结和可选的语音 |
| `/api/tts/status` | GET | 获取当前TTS服务状态 |
| `/api/tts/toggle` | POST | 切换TTS服务的启用状态 |

## 3. 具体接口规范

### 3.1 聊天接口

**路径**：`/api/chat`

**方法**：POST

**功能**：接收用户消息，调用大语言模型生成回复，并返回文本、表情和可选的语音数据

**请求体**：
```json
{
  "message": "用户输入的聊天内容",
  "session_id": "default",
  "frontend_tts_enabled": false
}
```

**参数说明**：
- `message`：字符串，必填，用户输入的聊天内容
- `session_id`：字符串，可选，会话ID，默认为"default"
- `frontend_tts_enabled`：布尔值，可选，前端TTS开关状态，默认为false

**响应体**：

**成功响应（带分句语音）**：
```json
{
  "message": "完整的AI回复内容",
  "sentences": ["分句1", "分句2", "分句3"...],
  "audio_segments": ["base64编码的音频数据1", "base64编码的音频数据2"...],
  "expression": "表情标识"
}
```

**成功响应（带整体语音）**：
```json
{
  "message": "完整的AI回复内容",
  "audio": "base64编码的音频数据",
  "expression": "表情标识"
}
```

**参数说明**：
- `message`：字符串，AI生成的完整回复内容
- `sentences`：数组，将回复内容按句子分割后的列表（可选）
- `audio_segments`：数组，与sentences对应的分段语音数据（base64编码，可选）
- `audio`：字符串，完整回复的语音数据（base64编码，可选）
- `expression`：字符串，与回复内容匹配的表情标识

**错误响应**：
```json
{
  "detail": "错误描述信息"
}
```

### 3.2 文件上传接口

**路径**：`/api/upload`

**方法**：POST

**功能**：接收用户上传的文件（PDF、Word或文本文件），解析文件内容，生成文档总结，并返回总结内容和可选的语音数据

**请求体**：
- `file`：文件，必填，通过multipart/form-data格式上传的文件

**响应体**：

**成功响应（带分句语音）**：
```json
{
  "summary": "文档总结内容",
  "sentences": ["分句1", "分句2", "分句3"...],
  "audio_segments": ["base64编码的音频数据1", "base64编码的音频数据2"...]
}
```

**成功响应（带整体语音）**：
```json
{
  "summary": "文档总结内容",
  "audio": "base64编码的音频数据"
}
```

**参数说明**：
- `summary`：字符串，文档的总结内容
- `sentences`：数组，将总结内容按句子分割后的列表（可选）
- `audio_segments`：数组，与sentences对应的分段语音数据（base64编码，可选）
- `audio`：字符串，完整总结的语音数据（base64编码，可选）

**错误响应**：
```json
{
  "detail": "错误描述信息"
}
```

### 3.3 TTS状态查询接口

**路径**：`/api/tts/status`

**方法**：GET

**功能**：获取当前TTS服务的启用状态和API密钥有效性

**请求参数**：无

**响应体**：
```json
{
  "enabled": true,
  "api_key_valid": true
}
```

**参数说明**：
- `enabled`：布尔值，TTS服务是否启用
- `api_key_valid`：布尔值，TTS服务的API密钥是否有效

### 3.4 TTS状态切换接口

**路径**：`/api/tts/toggle`

**方法**：POST

**功能**：切换TTS服务的启用状态

**请求体**：
```json
{
  "enabled": true
}
```

**参数说明**：
- `enabled`：布尔值，必填，设置TTS服务的新状态

**响应体**：
```json
{
  "enabled": true,
  "message": "TTS服务已启用"
}
```

**参数说明**：
- `enabled`：布尔值，切换后的TTS服务状态
- `message`：字符串，操作结果的提示信息

## 4. TTS开关状态传递机制

为了实现前端TTS开关状态对后端语音生成的控制，系统采用了以下机制：

1. **前端传递状态**：
   - 前端在调用`/api/chat`接口时，通过`frontend_tts_enabled`参数传递当前TTS开关的状态
   - 该参数为布尔值，表示用户是否希望启用语音播报功能

2. **后端双重验证**：
   - 后端在生成语音数据前，会同时检查两个条件：
     - 系统配置中的TTS全局开关是否开启（`Config.is_tts_enabled()`）
     - 前端传递的用户TTS开关状态是否开启（`request.frontend_tts_enabled`）
   - 只有当两个条件都为`true`时，后端才会生成并返回语音数据

3. **实现原理**：
```python
# 语音生成条件判断
if Config.is_tts_enabled() and request.frontend_tts_enabled:
    # 生成语音数据的逻辑
    # ...
else:
    # 不生成语音数据，或返回空的语音数据
    audio_data = ''
```

## 5. 状态码说明

| 状态码 | 含义 | 说明 |
|-------|------|-----|
| 200 | OK | 请求成功处理 |
| 400 | Bad Request | 请求参数错误或格式不符合要求 |
| 401 | Unauthorized | 未授权或API密钥无效 |
| 404 | Not Found | 请求的资源不存在 |
| 500 | Internal Server Error | 服务器内部错误 |

## 6. 最佳实践

1. **请求处理**：
   - 所有请求应设置正确的Content-Type
   - 对于可能失败的请求，实现适当的错误处理和重试机制

2. **响应处理**：
   - 检查响应状态码以确定请求是否成功
   - 对于成功响应，正确解析JSON格式的响应体
   - 对于错误响应，显示用户友好的错误信息

3. **TTS相关**：
   - 在发送聊天请求时，始终包含`frontend_tts_enabled`参数以确保用户TTS偏好被正确传递
   - 定期调用`/api/tts/status`接口以获取最新的TTS服务状态

## 7. 接口版本控制

当前版本：v1.0

后续接口变更将通过修改路径（如`/api/v2/chat`）或添加版本参数进行版本控制。