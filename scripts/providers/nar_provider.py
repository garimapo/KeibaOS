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
        "https://www.keiba.go.jp/KeibaWeb/"
        "TodayRaceInfo/TopTodayRaceListMini"
    )

    def __init__(self) -> None:

        self.logger = get_logger(
            __name__
        )

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/138.0 Safari/537.36"
                )
            }
        )


    def _get(
        self,
        url: str,
    ) -> str:
        """
        HTML取得共通処理。
        """

        self.logger.info(
            f"GET {url}"
        )

        response = self.session.get(
            url,
            timeout=10,
        )

        response.raise_for_status()

        response.encoding = (
            response.apparent_encoding
        )

        return response.text



    def _save_html(
        self,
        file_name: str,
        html: str,
    ) -> None:
        """
        HTMLログ保存。
        """

        Path("logs").mkdir(
            exist_ok=True
        )

        with open(
            f"logs/{file_name}",
            "w",
            encoding="utf-8",
        ) as f:

            f.write(html)



    def fetch_top_page(self) -> str:
        """
        NARトップページ取得。
        """

        html = self._get(
            self.BASE_URL
        )

        self._save_html(
            "nar_top.html",
            html,
        )

        self.logger.info(
            "Top page loaded."
        )

        return html



    def fetch_today_race_list(self) -> str:
        """
        今日の開催一覧HTML取得。
        """

        html = self._get(
            self.TODAY_RACE_LIST_URL
        )

        self._save_html(
            "today_race_list.html",
            html,
        )

        self.logger.info(
            "Today's race list loaded."
        )

        return html



    def fetch_race_list(
        self,
        url: str,
    ) -> str:
        """
        指定開催のRaceList HTML取得。
        """

        html = self._get(
            url
        )

        file_name = (
            "race_list_"
            + str(
                abs(
                    hash(url)
                )
            )
            + ".html"
        )

        self._save_html(
            file_name,
            html,
        )

        self.logger.info(
            f"Race page loaded: {file_name}"
        )

        return html



    def fetch_deba_table(
        self,
        url: str,
    ) -> str:
        """
        出馬表HTML取得。

        Ver0.8 Horse Engine用。

        Args:
            url:
                出馬表URL

        Returns:
            HTML文字列
        """

        html = self._get(
            url
        )

        file_name = (
            "deba_table_"
            + str(
                abs(
                    hash(url)
                )
            )
            + ".html"
        )

        self._save_html(
            file_name,
            html,
        )

        self.logger.info(
            f"Deba table loaded: {file_name}"
        )

        return html