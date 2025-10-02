from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from llm.oai.chat_openai import ChatOpenAI, OpenaiApiType
from config.enums import (
    LLMType,
)

def get_llm(config: dict) -> ChatOpenAI:
    """Get the LLM client."""
    is_azure_client = (
        config['llm']['type'] == LLMType.AzureOpenAIChat
        or config['llm']['type'] == LLMType.AzureOpenAI
    )
    debug_llm_key = config['llm']['api_key'] or ""
    llm_debug_info = {
        **config['llm'], #.model_dump(),
        "api_key": f"REDACTED,len={len(debug_llm_key)}",
    }
    if config['llm']['cognitive_services_endpoint'] is None:
        cognitive_services_endpoint = "https://cognitiveservices.azure.com/.default"
    else:
        cognitive_services_endpoint = config['llm']['cognitive_services_endpoint']
    print(f"Creating llm client with {llm_debug_info}")  # noqa T201
    
    return ChatOpenAI(
        api_key=config['llm']['api_key'],
        azure_ad_token_provider=(
            get_bearer_token_provider(
                DefaultAzureCredential(), cognitive_services_endpoint
            )
            if is_azure_client and not config['llm']['api_key']
            else None
        ),
        api_base=config['llm']['api_base'],
        organization=config['llm']['organization'],
        model=config['llm']['model'],
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        deployment_name=config['llm']['deployment_name'],
        api_version=config['llm']['api_version'],
        max_retries=config['llm']['max_retries'],
        request_timeout=config['llm']['request_timeout'],
    )
