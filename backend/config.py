import os

class Config:
    # ''' LLM配置 ,deepseek示例 , openai格式''' 
    # LLM_API_URL = "https://api.deepseek.com/v1/chat/completions"
    # LLM_API_KEY = ""    # 填写你的 LLM API 密钥，这里用deepseek，别的还没测试过
    # LLM_MODEL = "deepseek-chat"
    
    ''' LLM配置 ,阿里云示例，但是测试没成功，怀疑是dashscope格式问题 ''' 
    LLM_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    LLM_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    LLM_MODEL = "qwen-plus"  # 新增LLM模型配置

    ''' 向量模型配置 '''
    EMBEDDING_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    EMBEDDING_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-embeddings/embeddings"
    EMBEDDING_MODEL = "text-embedding-v3"
    EMBEDDING_DIMENSION = 1024
    
    ''' TTS服务配置 '''
    FISH_API_KEY =""
    
    FISH_REFERENCE_ID = "e70cc8ccf9fe41809e8e25c4de9ece78"
    
    ''' 对话历史配置 '''
    MAX_TURNS = 20
    
    @classmethod
    def is_tts_enabled(cls) -> bool:
        return bool(cls.FISH_API_KEY and cls.FISH_API_KEY.strip())
