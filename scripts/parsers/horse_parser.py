"""
Horse Parser

地方競馬情報サイト 出馬表Parser
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup
from bs4.element import Tag

from scripts.models import Horse


BASE_URL = "https://www.keiba.go.jp"


class HorseParser:

    def parse(
        self,
        html: str,
        race_id: int,
    ) -> list[Horse]:

        soup = BeautifulSoup(html, "html.parser")

        table = soup.find("table")

        if table is None:
            return []

        rows = table.find_all("tr")

        horses: list[Horse] = []

        current_frame = 0

        i = 0

        while i < len(rows):

            row = rows[i]

            horse_td = row.find("td", class_="horseNum")

            if horse_td is None:
                i += 1
                continue

            frame_td = row.find(
                "td",
                class_=re.compile("courseNum"),
            )

            if frame_td:
                current_frame = self._to_int(
                    frame_td.get_text(strip=True)
                )

            if self._is_cancelled(row):
                i = self._next_horse_index(rows, i)
                continue

            horse = self._parse_horse_block(
                rows=rows,
                index=i,
                race_id=race_id,
                frame_no=current_frame,
            )

            if horse:
                horses.append(horse)

            i = self._next_horse_index(rows, i)

        horses.sort(
            key=lambda x: (
                x.frame_no,
                x.horse_no,
            )
        )

        return horses

    def _parse_horse_block(
        self,
        rows,
        index: int,
        race_id: int,
        frame_no: int,
    ) -> Horse | None:

        if index + 4 >= len(rows):
            return None

        r1 = rows[index]
        r3 = rows[index + 2]

        horse_no = 0
        horse_name = ""
        horse_detail_url = ""
        jockey = ""
        trainer = ""
        odds = 0.0
        popularity = 0
        weight = 0.0

        # 馬番
        td = r1.find("td", class_="horseNum")
        if td:
            horse_no = self._to_int(td.get_text(strip=True))

        # 馬名 + 詳細URL
        horse_link = r1.find("a", class_="horseName")

        if horse_link:

            horse_name = horse_link.get_text(strip=True)

            href = horse_link.get("href")

            if href:

                if href.startswith("http"):
                    horse_detail_url = href
                else:
                    horse_detail_url = BASE_URL + href

        if horse_name == "":
            return None

        # 騎手
        jockey_link = r1.find("a", class_="jockeyName")

        if jockey_link:
            jockey = jockey_link.get_text(" ", strip=True)

        # 調教師
        trainer_link = r3.find("a")

        if trainer_link:
            trainer = trainer_link.get_text(" ", strip=True)

        # オッズ
        odds_td = r1.find("td", class_="odds_weight")

        if odds_td:

            odds_span = odds_td.find(
                "span",
                class_=re.compile("odds"),
            )

            if odds_span:

                try:
                    odds = float(
                        odds_span.get_text(strip=True)
                    )
                except Exception:
                    odds = 0.0

            text = odds_td.get_text(" ", strip=True)

            m = re.search(
                r"\((\d+)人気\)",
                text,
            )

            if m:
                popularity = int(m.group(1))

        # 馬体重
        weight_text = r3.get_text(" ", strip=True)

        m = re.search(r"(\d{3})", weight_text)

        if m:

            try:
                weight = float(m.group(1))
            except Exception:
                weight = 0.0

        return Horse(
            race_id=race_id,
            frame_no=frame_no,
            horse_no=horse_no,
            horse_name=horse_name,
            horse_detail_url=horse_detail_url,
            jockey=jockey,
            trainer=trainer,
            odds=odds,
            popularity=popularity,
            weight=weight,
        )

    @staticmethod
    def _to_int(value: str) -> int:

        try:
            return int(value.strip())
        except Exception:
            return 0

    @staticmethod
    def _is_cancelled(row: Tag) -> bool:

        text = row.get_text(" ", strip=True)

        return any(
            keyword in text
            for keyword in (
                "取消",
                "除外",
                "競走除外",
                "出走取消",
            )
        )

    @staticmethod
    def _next_horse_index(
        rows,
        start: int,
    ) -> int:

        for i in range(start + 1, len(rows)):
            if rows[i].find("td", class_="horseNum"):
                return i

        return len(rows)