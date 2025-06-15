from loguru import logger

from utils.Create_model_client import AsyncAnamnesisModelClient

from assets.mock_text import MOCK_TEXT

async def run_xinference_test(xinference_model_uid,xinference_base_url,xinference_api_key,prompt_file_path):
    """
    一个独立的协程，用于测试 Xinference 服务。
    :param xinference_model_uid: Xinference的模型ID
    :param xinference_base_url: Xinference的URL
    :param xinference_api_key: Xinference的api_key
    :param prompt_file_path: 提示词的路径
    """
    logger.info("调用Xinference")
    xinference_client = AsyncAnamnesisModelClient(
        model_uid=xinference_model_uid,
        base_url=xinference_base_url,
        api_key=xinference_api_key,
        prompt_file_path=prompt_file_path
    )
    final_json_str = await xinference_client.run(user_input=MOCK_TEXT, enable_thinking=False)
    return final_json_str