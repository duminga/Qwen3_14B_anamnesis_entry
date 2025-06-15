import os
import asyncio

from utils.logServer import logServer

from servers.ModelServer import run_xinference_test
from servers.PlaywrightServer import PlaywrightServer

# 日志配置
logServer().set_config(console_log_level="DEBUG", file_log_level="DEBUG")

class main():

    def __init__(self) -> None:
        self.XINFERENCE_BASE_URL=os.getenv('XINFERENCE_BASE_URL')
        self.XINFERENCE_API_KEY=os.getenv('XINFERENCE_API_KEY')
        self.XINFERENCE_MODEL_UID=os.getenv('XINFERENCE_MODEL_UID')
        self.PROMPT_FILE_PATH=os.path.join('assets', 'prompt.md')

    async def main(self):
        """
        主异步函数，使用 asyncio.create_task启动并等待所有测试任务。
        """
        # 使用 asyncio.create_task 将协程包装成任务并立即开始调度
        ai_client_task = asyncio.create_task(run_xinference_test(
            xinference_model_uid=self.XINFERENCE_MODEL_UID,
            xinference_base_url=self.XINFERENCE_BASE_URL,
            xinference_api_key=self.XINFERENCE_API_KEY,
            prompt_file_path=self.PROMPT_FILE_PATH,
        ))
        playwright_task = asyncio.create_task(PlaywrightServer().run())
        await ai_client_task
        await playwright_task

if __name__ == '__main__':
    # 运行主异步函数
    app = main()
    asyncio.run(app.main())