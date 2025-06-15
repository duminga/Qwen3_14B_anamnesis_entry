from playwright.async_api import (
    async_playwright,
    Page,
    Browser,
    Playwright,
    BrowserContext,
)
from loguru import logger

class PlaywrightHelper:
    """Playwright 工具类，用于封装 Playwright 的页面初始化和浏览器接管"""

    def __init__(self):
        """初始化 Playwright 工具类"""
        self.playwright: Playwright = None
        self.browser: Browser = None
        self.page: Page = None
        self.context: BrowserContext = None
        # Edge 浏览器路径
        self.edge_path = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
        # 存储所有创建的上下文
        self.contexts = {}
        # 标记是否为接管模式
        self.is_takeover_mode = False

    async def connect_to_browser(self, cdp_url: str = "http://localhost:9222", page_index: int = 0) -> Page:
        """
        通过 CDP 连接到现有的浏览器实例并接管页面

        :param cdp_url (str): CDP 连接地址，默认为 "http://localhost:9222"
        :param page_index (int): 要接管的页面索引，默认为 0（第一个页面）

        :return Page: 接管的页面对象
        """
        try:
            logger.info(f"正在连接到浏览器实例: {cdp_url}")
            
            if not self.playwright:
                self.playwright = await async_playwright().start()

            # 通过 CDP 连接到现有浏览器
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            self.is_takeover_mode = True
            
            # 获取现有的上下文和页面
            if self.browser.contexts:
                self.context = self.browser.contexts[0]
                if self.context.pages:
                    if page_index < len(self.context.pages):
                        self.page = self.context.pages[page_index]
                        logger.info(f"成功接管页面: {self.page.url}")
                    else:
                        logger.warning(f"页面索引 {page_index} 超出范围，使用第一个页面")
                        self.page = self.context.pages[0]
                        logger.info(f"成功接管页面: {self.page.url}")
                else:
                    # 如果没有现有页面，创建新页面
                    self.page = await self.context.new_page()
                    logger.info("没有现有页面，已创建新页面")
            else:
                logger.error("没有找到可用的浏览器上下文")
                raise Exception("没有找到可用的浏览器上下文")

            return self.page

        except Exception as e:
            logger.error(f"连接到浏览器失败: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            await self.close()
            raise

    async def start(
                    self, 
                    headless: bool = False, 
                    context_name: str = "default", 
                    use_local_browser: bool = True, 
                    debug_port: int = None
                    ) -> Page:
        """
        启动 Playwright 并返回页面对象

        :param headless (bool): 是否使用无头模式，默认为 False
        :param context_name (str): 上下文名称，用于创建独立的会话，默认为 "default"
        :param use_local_browser (bool): 是否使用本地 Edge 浏览器，默认为 True(使用默认的 Chromium)
        :param debug_port (int): 调试端口，默认为空

        :return Page: Playwright 页面对象
        """
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()

            if not self.browser:
                # 基础启动参数
                base_args = [
                    "--guest",  # 来宾模式
                    "--disable-popup-blocking",  # 禁用弹窗拦截
                    "--start-maximized",  # 启动时最大化窗口
                    "--disable-blink-features=AutomationControlled",  # 禁用自动化标志
                    "--disable-infobars",  # 隐藏自动化提示
                    "--disable-dev-shm-usage",  # 避免内存不足
                    "--disable-web-security",  # 禁用同源策略
                    "--disable-features=IsolateOrigins,site-per-process"  # 禁用站点隔离
                ]
                
                # 如果指定了调试端口，添加远程调试端口参数
                if debug_port is not None:
                    base_args.append(f"--remote-debugging-port={debug_port}")

                if use_local_browser:
                    # 使用本地 Edge 浏览器
                    self.browser = await self.playwright.chromium.launch(
                        executable_path=self.edge_path,
                        headless=headless,
                        args=base_args,
                    )
                else:
                    # 使用默认的 Chromium 浏览器
                    self.browser = await self.playwright.chromium.launch(
                        headless=headless,
                        args=base_args
                    )

            # 如果上下文不存在，创建新的上下文
            if context_name not in self.contexts:
                self.contexts[context_name] = await self.browser.new_context(
                    no_viewport=True,  # 禁用视口大小限制
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                )
                # 设置弹窗权限
                await self.contexts[context_name].grant_permissions(["notifications"])

            # 使用指定的上下文
            self.context = self.contexts[context_name]
            # 创建新页面
            self.page = await self.context.new_page()
            return self.page

        except Exception as e:
            logger.error(f"启动 Playwright 失败: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback

            logger.error(f"详细错误信息: {traceback.format_exc()}")
            await self.close()
            raise

    async def get_all_pages(self) -> list[Page]:
        """
        获取当前浏览器中的所有页面
        
        :return list[Page]: 所有页面的列表
        """
        try:
            all_pages = []
            if self.browser and self.browser.contexts:
                for context in self.browser.contexts:
                    all_pages.extend(context.pages)
            return all_pages
        except Exception as e:
            logger.error(f"获取所有页面失败: {str(e)}")
            return []

    async def switch_to_page(self, page_index: int) -> Page:
        """
        切换到指定索引的页面
        
        :param page_index (int): 页面索引
        :return Page: 切换后的页面对象
        """
        try:
            all_pages = await self.get_all_pages()
            if 0 <= page_index < len(all_pages):
                self.page = all_pages[page_index]
                logger.info(f"已切换到页面 {page_index}: {self.page.url}")
                return self.page
            else:
                logger.error(f"页面索引 {page_index} 超出范围 (0-{len(all_pages)-1})")
                raise IndexError(f"页面索引 {page_index} 超出范围")
        except Exception as e:
            logger.error(f"切换页面失败: {str(e)}")
            raise

    async def close(self) -> None:
        """关闭所有 Playwright 资源"""
        logger.info("开始清理资源...")
        try:
            # 如果是接管模式，不关闭浏览器，只断开连接
            if self.is_takeover_mode:
                logger.info("接管模式：断开连接但不关闭浏览器")
                if self.playwright:
                    await self.playwright.stop()
            else:
                # 正常模式：关闭所有资源
                if self.page:
                    await self.page.close()
                # 关闭所有上下文
                for context_name, context in self.contexts.items():
                    await context.close()
                self.contexts.clear()
                if self.browser:
                    await self.browser.close()
                if self.playwright:
                    await self.playwright.stop()
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")



"""
接管示例代码:
import asyncio
from loguru import logger
from Playwright_Helper import PlaywrightHelper


async def main():
    使用 PlaywrightHelper 接管浏览器的示例
    helper = PlaywrightHelper()
    
    try:
        # 方法1: 接管现有浏览器实例
        logger.info("=== 接管现有浏览器实例 ===")
        page = await helper.connect_to_browser("http://localhost:9222", page_index=0)
        
        # 获取当前页面信息
        logger.info(f"当前页面URL: {page.url}")
        logger.info(f"当前页面标题: {await page.title()}")
        
        # 获取所有页面
        all_pages = await helper.get_all_pages()
        logger.info(f"浏览器中共有 {len(all_pages)} 个页面")
        for i, p in enumerate(all_pages):
            logger.info(f"页面 {i}: {p.url}")
        
        # 示例操作：在当前页面执行一些操作
        # await page.goto("https://www.baidu.com")
        # await page.locator("input#kw").fill("Playwright 接管浏览器")
        
        # 暂停以便手动操作
        await page.pause()
        
    except Exception as e:
        logger.error(f"接管浏览器失败: {str(e)}")
    finally:
        # 清理资源（接管模式下不会关闭浏览器）
        await helper.close()


async def switch_page_example():
    切换页面的示例
    helper = PlaywrightHelper()
    
    try:
        # 接管浏览器
        await helper.connect_to_browser("http://localhost:9222")
        
        # 获取所有页面
        all_pages = await helper.get_all_pages()
        logger.info(f"找到 {len(all_pages)} 个页面")
        
        # 切换到不同的页面
        for i in range(len(all_pages)):
            page = await helper.switch_to_page(i)
            logger.info(f"切换到页面 {i}: {page.url}")
            await asyncio.sleep(2)  # 等待2秒
            
    except Exception as e:
        logger.error(f"切换页面失败: {str(e)}")
    finally:
        await helper.close()


if __name__ == '__main__':
    # 运行主示例
    asyncio.run(main())
    
    # 如果要运行切换页面示例，取消下面的注释
    # asyncio.run(switch_page_example()) 
"""