import os
from llm.openai_client import OpenAILLM

def get_llm(config):
    if config["provider"] == "openai":
        return OpenAILLM(
            api_key=os.getenv(config["api_key_env"]),
            model=config["model"],
            base_url=config["base_url"],
        )

    raise ValueError("Unsupported LLM")
