"""
NAR Provider

地方競馬公式サイトへの接続を管理する。
"""

from __future__ import annotations

from pathlib import Path

import requests

from scripts.logger import get_logger


class NARProvider:
    """地方競馬公式サイト(NAR)への通信を担当する。"""

    BASE_URL = "https://www.keiba.go.jp/"
    TODAY_RACE_LIST_URL = (
        "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/TopTodayRaceListMini"
    )

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/138.0 Safari/537.36"
                )
            }
        )

    def _get(self, url: str) -> str:
        """
        HTMLを取得する共通処理
        """

        self.logger.info(f"GET {url}")

        response = self.session.get(
            url,
            timeout=10,
        )

        response.raise_for_status()

        response.encoding = response.apparent_encoding

        return response.text

    def fetch_top_page(self) -> str:
        """
        NARトップページ取得
        """

        html = self._get(self.BASE_URL)

        Path("logs").mkdir(exist_ok=True)

        with open(
            "logs/nar_top.html",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(html)

        self.logger.info("Top page loaded.")

        return html

    def fetch_today_race_list(self) -> str:
        """
        今日の開催一覧HTML取得
        """

        html = self._get(self.TODAY_RACE_LIST_URL)

        Path("logs").mkdir(exist_ok=True)

        with open(
            "logs/today_race_list.html",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(html)

        self.logger.info("Today's race list loaded.")

        return html

    def fetch_race_list(self, url: str) -> str:
        """
        指定された開催ページのレース一覧HTMLを取得する。
        """

        html = self._get(url)

        Path("logs").mkdir(exist_ok=True)

        file_name = url.rstrip("/").split("/")[-1]
        file_path = f"logs/{file_name}.html"

        with open(
            file_path,
            "w",
            encoding="utf-8",
        ) as f:
            f.write(html)

        self.logger.info(f"Race page loaded: {file_name}")

        return html