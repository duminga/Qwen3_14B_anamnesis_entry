import os
import sys
from datetime import datetime
from loguru import logger


class logServer:
    """
    使用 Loguru 实现的日志服务类，仿照原有的 logServer 逻辑。
    提供单例模式，支持文件和控制台输出，自定义格式和颜色。
    """
    _instance = None
    _file_handler_id = None
    _console_handler_id = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._file_handler_id = None
            cls._instance._console_handler_id = None
        return cls._instance

    def __init__(self):
        if getattr(sys, 'frozen', False):
            executable_path = os.path.dirname(os.path.abspath(sys.executable))
        else:
            executable_path = "/hy-tmp/Train_logs"
        executable_path = executable_path.replace('\\', '/')
        self.docs_folder = "/hy-tmp/Train_logs"
        if not os.path.exists(self.docs_folder):
            os.makedirs(self.docs_folder, exist_ok=True)
        current_time = datetime.now().strftime('%Y%m%d_%H%M')
        self.filename = os.path.join(self.docs_folder, f'训练记录_{current_time}.log')

    def set_config(self, file_log_level="DEBUG", console_log_level="DEBUG"):
        """
        配置loguru。
        支持为文件和控制台分别指定日志级别。

        :param file_log_level: 文件日志的最低级别 (例如 "DEBUG", "INFO", "WARNING")
        :type file_log_level: str
        :param console_log_level: 控制台日志的最低级别 (例如 "DEBUG", "INFO", "WARNING")
        :type console_log_level: str
        :rtype: tuple
        """

        # 关键步骤：移除所有现有的 loguru handlers (包括默认的以及之前可能添加的)
        # 这样可以确保我们完全控制日志输出，避免重复
        # logger.remove()

        # 由于上面已经移除了所有 handlers，本实例之前记录的 handler ID 也应视作无效
        # (如果 run 被同一个实例多次调用，这一步是好的实践，确保状态干净)
        self._file_handler_id = None
        self._console_handler_id = None

        # 定义日志颜色 (这些是对全局 loguru logger 的配置，重复调用无害)
        logger.level("DEBUG", color="<cyan>")
        logger.level("INFO", color="<green>")
        logger.level("WARNING", color="<yellow>")
        logger.level("ERROR", color="<red>")
        logger.level("CRITICAL", color="<bold><red><bg white>")

        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} - "
            "{level: <8} - "
            "[{file.name}-{line}] - "
            "[{function}] - "
            "{message}"
        )

        console_format = (
            "<level>"
            "{time:YYYY-MM-DD HH:mm:ss} - "
            "{level: <4} - "
            "[{file.name}-{line}] - "
            "[{function}] - "
            "</level>"
            "{message}"
        )

        self._file_handler_id = logger.add(
            sink=self.filename,
            level=file_log_level.upper(),
            format=file_format,
            encoding='utf-8',
            enqueue=True
        )

        self._console_handler_id = logger.add(
            sink=sys.stderr,
            level=console_log_level.upper(),
            format=console_format,
            colorize=True
        )


if __name__ == '__main__':
    # 注意：run() 方法返回一个元组 (logger, filename)
    # 您在示例代码中调用的是 LogServerLoguru()，但类定义是 class logServer:
    # 这里我使用类名 logServer
    app_logger, log_file = logServer().run(file_log_level="DEBUG", console_log_level="DEBUG")
    app_logger.info(f"日志服务测试，日志文件位于: {log_file}")
    app_logger.debug("这是一条DEBUG级别的测试日志。")
    app_logger.warning("这是一条WARNING级别的测试日志。")