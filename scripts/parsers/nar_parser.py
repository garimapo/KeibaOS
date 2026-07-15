"""
NAR Parser

NAR開催一覧HTMLを解析する。
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from scripts.models import RaceMeeting


class NARParser:
    """NAR開催一覧HTML解析"""

    BASE_URL = "https://www.keiba.go.jp"

    def parse_today_race_list(
        self,
        html: str,
    ) -> list[RaceMeeting]:
        """
        今日開催している競馬場一覧を取得する。
        """

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        table = soup.find(
            "table",
            id="raceInfoToday",
        )

        if table is None:
            return []

        meetings: list[RaceMeeting] = []

        rows = table.find_all("tr")

        for row in rows:

            cols = row.find_all("td")

            if len(cols) < 3:
                continue

            place = cols[0].get_text(strip=True)

            menu = cols[2].find("a")

            if menu is None:
                continue

            href = menu.get("href")

            if href is None:
                continue

            meetings.append(
                RaceMeeting(
                    race_date="",
                    organization="地方",
                    place=place,
                    race_list_url=self.BASE_URL + href,
                )
            )

        return meetings