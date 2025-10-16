import os

class Config:
    # ''' LLM配置 ,deepseek示例 , openai格式''' 
    # LLM_API_URL = "https://api.deepseek.com/v1/chat/completions"
    # LLM_API_KEY = ""    # 填写你的 LLM API 密钥，这里用deepseek，别的还没测试过
    # LLM_MODEL = "deepseek-chat"

    ''' LLM配置 ,智谱示例 , openai格式'''
    LLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    LLM_API_KEY = os.getenv("ZHIPU_API_KEY") # 填写你的 智谱 API 密钥
    LLM_MODEL = "glm-4-flash"
    
    # ''' LLM配置 ,阿里云示例，测试成功，dashscope格式已支持 ''' 
    # LLM_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    # LLM_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    # LLM_MODEL = "qwen-plus"  # 新增LLM模型配置

    ''' 向量模型配置 '''
    EMBEDDING_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    EMBEDDING_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-embeddings/embeddings"
    EMBEDDING_MODEL = "text-embedding-v3"
    EMBEDDING_DIMENSION = 1024
    
    ''' TTS服务配置 - 通义千问 '''
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    TTS_ENABLED = True  # TTS开关，设为True启用，False禁用
    
    ''' 对话历史配置 '''
    MAX_TURNS = 20
    
    @classmethod
    def is_tts_enabled(cls) -> bool:
        # 只根据TTS_ENABLED配置决定是否启用TTS
        return cls.TTS_ENABLED
