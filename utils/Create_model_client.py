import json

import openai
from loguru import logger

from utils.logServer import logServer

class AsyncAnamnesisModelClient:
    """
    一个用于与部署在Xinference或官方API上的既往病史判别模型进行异步交互的客户端类。
    """
    def __init__(self, model_uid: str, base_url: str, api_key: str, prompt_file_path: str):
        """
        初始化客户端。
        :param model_uid: Xinference或云服务商处指定的模型 ID。
        :param base_url: 服务的基础 URL。
        :param api_key: API 密钥。
        :param prompt_file_path: 系统提示词文件的路径。
        """
        self.model_uid = model_uid
        self.base_url = base_url
        self.api_key = api_key
        self.prompt_file_path = prompt_file_path
        
        self.system_prompt_template = self._load_system_prompt()
        # 初始化异步客户端
        self.async_client = self._initialize_openai_async_client()

    def _load_system_prompt(self) -> str:
        """
        从文件加载系统提示词。
        :return: 从文件中读取的提示词字符串。
        """
        logger.info(f"加载系统提示词 '{self.prompt_file_path}' ")
        try:
            with open(self.prompt_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"系统提示词文件未找到: {self.prompt_file_path}")
            exit()

    def _initialize_openai_async_client(self) -> openai.AsyncOpenAI:
        """
        初始化并返回配置好的异步 OpenAI 客户端。
        :return: openai.AsyncOpenAI 客户端实例。
        """
        return openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def _prepare_messages(self, user_input: str, enable_thinking: bool) -> list:
        """
        根据用户输入和思考模式开关准备发送给模型的消息列表。
        :param user_input: 用户的输入文本。
        :param enable_thinking: 是否启用模型的思考模式。
        :return: 一个符合 OpenAI API 格式的消息列表。
        """
        system_content = self.system_prompt_template
        final_user_input = user_input
        if not enable_thinking:
            # 如果不启用思考模式，在用户输入开头加入/no_think指令
            final_user_input = "/no_think\n" + user_input
        
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": final_user_input}
        ]

    async def _stream_and_process_response_async(self, messages: list) -> tuple[str, str]:
        """
        发起流式请求,解析两种不同API格式的响应。
        :param messages: 准备好的消息列表。
        :return: 一个包含 (思考过程, 最终JSON字符串) 的元组。
        """
        stream = await self.async_client.chat.completions.create(
            model=self.model_uid,
            messages=messages,
            max_tokens=4096,
            temperature=0.1,
            top_p=0.1,
            stream=True,
        )

        full_response_content = ""
        thinking_process = ""
        final_answer = ""
        is_official_api = False

        logger.debug("流式输出\n")
        # 异步迭代并打印数据流
        async for chunk in stream:
            delta = chunk.choices[0].delta
            
            # 智能适配：检查是否存在官方API特有的 'reasoning_content' 字段
            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                is_official_api = True
                print(delta.reasoning_content, end="", flush=True)
                thinking_process += delta.reasoning_content
            
            # 处理标准的内容字段
            content_delta = delta.content
            if content_delta is not None:
                if not is_official_api:
                    # 如果不是官方API，则所有内容先统一接收
                    full_response_content += content_delta
                else:
                    # 如果是官方API，则这部分就是最终答案
                    final_answer += content_delta
                print(content_delta, end="", flush=True)

        print("\n")

        # 根据API类型进行最终解析
        if is_official_api:
            return thinking_process if thinking_process else "未找到思考过程。", final_answer
        else:
            # 沿用原有的 <think> 标签解析逻辑，处理 Xinference 的响应
            if "<think>" in full_response_content and "</think>" in full_response_content:
                start_tag = "<think>"
                end_tag = "</think>"
                start_index = full_response_content.find(start_tag)
                end_index = full_response_content.find(end_tag)

                if start_index != -1 and end_index != -1 and start_index < end_index:
                    thinking_process = full_response_content[start_index + len(start_tag):end_index].strip()
                    final_json_str = full_response_content[end_index + len(end_tag):].strip()
                    return thinking_process, final_json_str
            
            return "未找到思考过程。", full_response_content.strip()


    async def run(self, user_input: str, enable_thinking: bool = True):
        """
        (异步公共方法) 执行与模型交互的完整流程。
        :param user_input: 用户的输入文本。
        :param enable_thinking: 是否启用模型的思考模式，默认为 True。
        :return final_json_str: AI处理的结果
        """
        try:
            messages = self._prepare_messages(user_input, enable_thinking)
            thinking_process, final_json_str = await self._stream_and_process_response_async(messages)
            
            if thinking_process != "未找到思考过程." and len(thinking_process) > 0:
                logger.info(f"模型思考过程:\n{thinking_process}\n")
            
            parsed_json_obj = json.loads(final_json_str)
            pretty_json_output = json.dumps(
                parsed_json_obj, 
                ensure_ascii=False,
                indent=2
            )
            logger.info(f"模型最终输出:\n{pretty_json_output}\n")

            return final_json_str

        except Exception as e:
            logger.error(f"\n调用模型时发生错误: {e}")
            logger.error("请检查：")
            logger.error(f"1. 服务是否已正确启动？")
            logger.error(f"2. base_url ('{self.base_url}') 是否正确？")
            logger.error(f"3. 模型 UID/名称 ('{self.model_uid}') 是否正确无误？")