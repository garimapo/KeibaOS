"""
Horse Parser

NAR出馬表HTMLから出走馬情報を解析する。
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from scripts.models import Horse


class HorseParser:
    """
    NAR出馬表解析
    """


    def parse(
        self,
        html: str,
        race_id: int,
    ) -> list[Horse]:
        """
        出馬表HTMLからHorse一覧を取得する。
        """

        soup = BeautifulSoup(
            html,
            "html.parser",
        )


        horses: list[Horse] = []


        # 馬名リンクを基準に行を探す
        horse_links = soup.find_all(
            "a",
            href=re.compile(
                "Horse"
            ),
        )


        for link in horse_links:

            row = link.find_parent(
                "tr"
            )

            if row is None:
                continue


            cols = row.find_all(
                "td"
            )

            if len(cols) < 5:
                continue


            text = row.get_text(
                " ",
                strip=True,
            )


            numbers = re.findall(
                r"\d+",
                text,
            )


            if len(numbers) < 2:
                continue


            frame_no = int(
                numbers[0]
            )

            horse_no = int(
                numbers[1]
            )


            horse_name = (
                link
                .get_text(strip=True)
            )


            if not horse_name:
                continue


            jockey = ""

            jockey_link = row.find(
                "a",
                href=re.compile(
                    "Jockey"
                ),
            )


            if jockey_link:

                jockey = (
                    jockey_link
                    .get_text(strip=True)
                )


            horses.append(
                Horse(
                    race_id=race_id,

                    frame_no=frame_no,
                    horse_no=horse_no,

                    horse_name=horse_name,

                    jockey=jockey,
                    trainer="",

                    odds=0.0,
                    popularity=0,

                    weight=0.0,
                )
            )


        return horses