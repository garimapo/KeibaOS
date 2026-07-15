"""
NAR Provider

地方競馬公式サイトへの接続を管理する。
"""

from __future__ import annotations

import requests

from scripts.logger import get_logger


class NARProvider:
    """地方競馬公式サイト(NAR)へ接続するProvider。"""

    BASE_URL = "https://www.keiba.go.jp/"

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def fetch_top_page(self) -> str:
        """
        NAR公式トップページのHTMLを取得する。

        Returns
        -------
        str
            HTML文字列

        Raises
        ------
        requests.RequestException
            通信エラー
        """

        self.logger.info("Connecting to NAR...")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/138.0 Safari/537.36"
            )
        }

        response = requests.get(
            self.BASE_URL,
            headers=headers,
            timeout=10,
        )

        response.raise_for_status()

        response.encoding = response.apparent_encoding

        self.logger.info("Connected to NAR successfully.")

        # HTML保存（解析用）
        with open(
            "logs/nar_top.html",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(response.text)

        return response.text