import asyncio

from loguru import logger

from utils.PlayWright_Helper import PlaywrightHelper

class PlaywrightServer:
    """模拟Playwright操作"""

    def __init__(self) -> None:
        self.page = None

    async def run(self):
        try:
            
            logger.info("开始模拟Playwright操作")
            self.playwright_helper = PlaywrightHelper()

            self.page = await self.playwright_helper.start()

            await self.page.goto("https://www.baidu.com")

            for i in range(1,100):
                logger.info(f"Playwright正在输入{i}")
                await self.page.locator('//input[@id="kw"]').fill(f"{i}")

                await self.page.keyboard.press('Enter')

                await self.page.wait_for_timeout(3000) 

            await self.page.pause()

        except Exception as e:
            logger.error(f"Playwright有问题: {e}")
        finally:
            await self.playwright_helper.close()
