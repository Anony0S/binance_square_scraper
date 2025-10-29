"""
基础爬虫类
提供通用的浏览器初始化和配置功能
"""

from utils.logger import setup_logger

try:
    from DrissionPage import ChromiumPage, ChromiumOptions

    DRISSION_AVAILABLE = True
except ImportError:
    DRISSION_AVAILABLE = False


logger = setup_logger(
    logger_name="base_scraper",
    log_file="base_scraper.log",
    log_level=20,  # logging.INFO
)


class BaseScraper:
    """基础爬虫类，提供通用的浏览器配置和管理"""

    def __init__(self, headless: bool = False):
        """
        初始化基础爬虫

        :param headless: 是否使用无头模式（不显示浏览器窗口）
        """
        if not DRISSION_AVAILABLE:
            raise ImportError("请先安装 DrissionPage: pip install DrissionPage")

        self.headless = headless
        self.page = None
        self.options = self._setup_options()

    def _setup_options(self) -> ChromiumOptions:
        """
        配置浏览器选项

        :return: 配置好的 ChromiumOptions 对象
        """
        options = ChromiumOptions()

        # 无头模式
        if self.headless:
            options.headless()

        # 设置用户代理
        options.set_user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        return options

    def init_browser(self):
        """初始化浏览器"""
        logger.info("正在启动浏览器...")
        self.page = ChromiumPage(addr_or_opts=self.options)
        logger.info("✓ 浏览器启动成功")

    def close(self):
        """关闭浏览器"""
        if self.page:
            self.page.quit()
            logger.info("✓ 浏览器已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        self.init_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        # self.close()
