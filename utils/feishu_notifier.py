"""
飞书消息通知模块
用于将新文章通知发送到飞书机器人
"""

import json
from multiprocessing import context
import requests
from typing import List, Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(
    logger_name="feishu_notifier",
    log_file="feishu_notifier.log",
    log_level=20,  # logging.INFO
)


class FeishuNotifier:
    """飞书消息通知器"""

    def __init__(
        self,
        app_id: str = None,
        app_secret: str = None,
        receive_id: str = None,
        receive_id_type: str = "chat_id",
        webhook_url: str = None,
        enabled: bool = True,
    ):
        """
        初始化飞书通知器

        支持两种方式：
        1. 使用 app_id + app_secret（需要获取 access_token）
        2. 使用 webhook_url（简单快捷）

        :param app_id: 飞书应用 ID
        :param app_secret: 飞书应用密钥
        :param receive_id: 接收消息的 ID（chat_id 或 user_id）
        :param receive_id_type: 接收者 ID 类型（chat_id/user_id/email/open_id）
        :param webhook_url: 飞书群机器人 Webhook URL
        :param enabled: 是否启用通知
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.receive_id = receive_id
        self.receive_id_type = receive_id_type
        self.webhook_url = webhook_url
        self.enabled = enabled
        self.access_token = None

        # API 端点
        self.token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        self.message_url = "https://open.feishu.cn/open-apis/im/v1/messages"

        # 如果使用 app_id 方式，获取 access_token
        if self.enabled and self.app_id and self.app_secret:
            self._get_access_token()

    def _get_access_token(self) -> bool:
        """
        获取飞书 tenant_access_token

        :return: 是否获取成功
        """
        try:
            payload = {"app_id": self.app_id, "app_secret": self.app_secret}
            response = requests.post(self.token_url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("code") == 0:
                self.access_token = data.get("tenant_access_token")
                logger.info("✓ 飞书 access_token 获取成功")
                return True
            else:
                logger.error(f"× 飞书 access_token 获取失败: {data.get('msg')}")
                return False

        except Exception as e:
            logger.error(f"× 飞书 access_token 获取异常: {str(e)}")
            return False

    def _send_message_via_api(
        self, content: str, msg_type: str = "text"
    ) -> bool:
        """
        通过飞书 API 发送消息（需要 app_id 和 app_secret）

        :param content: 消息内容
        :param msg_type: 消息类型（text/post/interactive）
        :return: 是否发送成功
        """
        if not self.access_token:
            logger.error("× access_token 未获取，无法发送消息")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json; charset=utf-8",
            }

            payload = {
                "receive_id": self.receive_id,
                "msg_type": msg_type,
                "content": content,
            }

            # 添加 receive_id_type 参数
            params = {"receive_id_type": self.receive_id_type}

            response = requests.post(
                self.message_url,
                headers=headers,
                params=params,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()
            if data.get("code") == 0:
                logger.info("✓ 飞书消息发送成功")
                return True
            else:
                logger.error(f"× 飞书消息发送失败: {data.get('msg')}")
                return False

        except Exception as e:
            logger.error(f"× 飞书消息发送异常: {str(e)}")
            return False

    def _send_message_via_webhook(self, content: Dict) -> bool:
        """
        通过 Webhook 发送消息（最简单的方式）

        :param content: 消息内容（字典格式）
        :return: 是否发送成功
        """
        if not self.webhook_url:
            logger.error("× webhook_url 未配置，无法发送消息")
            return False

        try:
            response = requests.post(
                self.webhook_url,
                json=content,
                timeout=10,
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            response.raise_for_status()

            data = response.json()
            if data.get("code") == 0 or data.get("StatusCode") == 0:
                logger.info("✓ 飞书 Webhook 消息发送成功")
                return True
            else:
                logger.error(
                    f"× 飞书 Webhook 消息发送失败: {data.get('msg', data.get('StatusMessage'))}"
                )
                return False

        except Exception as e:
            logger.error(f"× 飞书 Webhook 消息发送异常: {str(e)}")
            return False

    def send_text_message(self, text: str) -> bool:
        """
        发送文本消息

        :param text: 文本内容
        :return: 是否发送成功
        """
        if not self.enabled:
            logger.info("飞书通知未启用，跳过发送")
            return False

        # 优先使用 Webhook
        if self.webhook_url:
            content = {"msg_type": "text", "content": {"text": text}}
            return self._send_message_via_webhook(content)
        # 使用 API
        elif self.app_id and self.app_secret:
            content = json.dumps({"text": text}, ensure_ascii=False)
            return self._send_message_via_api(content, msg_type="text")
        else:
            logger.error("× 未配置飞书通知方式（webhook_url 或 app_id+app_secret）")
            return False

    def send_rich_text_message(self, title: str, content: list) -> bool:
        """
        发送富文本消息（支持多种样式）

        :param title: 消息标题
        :param content: 富文本内容（二元数组）
        :return: 是否发送成功
        """
        if not self.enabled:
            logger.info("飞书通知未启用，跳过发送")
            return False

        # 将文本内容转换为富文本格式
        post_content = {
            "zh_cn": {
                "title": title,
                "content": content
            }
        }

        # 优先使用 Webhook
        if self.webhook_url:
            payload = {"msg_type": "post", "content": {"post": post_content}}
            return self._send_message_via_webhook(payload)
        # 使用 API
        elif self.app_id and self.app_secret:
            content_str = json.dumps({"post": post_content}, ensure_ascii=False)
            return self._send_message_via_api(content_str, msg_type="post")
        else:
            logger.error("× 未配置飞书通知方式（webhook_url 或 app_id+app_secret）")
            return False

    def notify_new_article(self, article: dict) -> bool:
        """
        发送单篇新文章通知

        :param article: 文章字典
        :param kol_username: KOL 用户名
        :return: 是否发送成功
        """
        if not article:
            logger.info("文章为空，无需发送通知")
            return False

        card_title = article.get("card_title", "").strip()
        card_description = article.get("card_description", "").strip()
        create_time = article.get("create-time", "").strip()
        author = article.get("author", "").strip()

        # 如果没有内容，跳过
        if not card_description:
            logger.info("文章没有内容，跳过发送")
            return False

        # 构建消息标题
        title = f"币安广场新文章 - {author}"

        # 发送富文本消息
        return self.send_rich_text_message(title, [
            [
                {"tag": "text", "text": f"标题: {card_title}\n"},
            ],
            [
                {"tag": "text", "text": f"作者: {author} | 发布时间: {create_time}\n"},
            ],
            [
                {"tag": "text", "text": f"内容: {card_description}\n"},
            ],
            [
                {"tag": "a", "href": f"{img_url}", "text": f"图片{idx + 1}\n"} for idx,img_url in enumerate(article.get("imgs", []))
            ]
        ])


# 便捷函数
def create_feishu_notifier_from_config(config: Dict) -> Optional[FeishuNotifier]:
    """
    从配置字典创建飞书通知器

    :param config: 配置字典
    :return: FeishuNotifier 实例或 None
    """
    feishu_config = config.get("feishu", {})

    if not feishu_config.get("enabled", False):
        logger.info("飞书通知未启用")
        return None

    return FeishuNotifier(
        app_id=feishu_config.get("app_id"),
        app_secret=feishu_config.get("app_secret"),
        receive_id=feishu_config.get("receive_id"),
        receive_id_type=feishu_config.get("receive_id_type", "chat_id"),
        webhook_url=feishu_config.get("webhook_url"),
        enabled=feishu_config.get("enabled", False),
    )
