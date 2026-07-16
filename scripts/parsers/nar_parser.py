"""
NAR Parser

NAR開催一覧・レース一覧HTMLを解析する。
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from scripts.models import Race, RaceMeeting


class NARParser:
    """NAR HTML解析"""

    BASE_URL = "https://www.keiba.go.jp"

    def parse_today_race_list(
        self,
        html: str,
    ) -> list[RaceMeeting]:

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

        meetings = []

        for row in table.find_all("tr"):

            cols = row.find_all("td")

            if len(cols) < 3:
                continue

            link = cols[2].find("a")

            if link is None:
                continue

            href = link.get("href")

            if href is None:
                continue

            race_url = urljoin(
                self.BASE_URL,
                href,
            )

            meetings.append(
                RaceMeeting(
                    race_date=self._extract_date_from_url(
                        race_url
                    ),
                    organization="地方",
                    place=cols[0].get_text(
                        strip=True
                    ),
                    race_list_url=race_url,
                )
            )

        return meetings


    def parse_race_list(
        self,
        html: str,
        meeting: RaceMeeting,
    ) -> list[Race]:

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        races = []

        for row in soup.find_all(
            "tr",
            class_="data",
        ):

            cols = row.find_all("td")

            if len(cols) < 9:
                continue

            course = cols[5].get_text(
                strip=True
            )

            link = cols[4].find("a")

            races.append(
                Race(
                    race_date=meeting.race_date,
                    organization=meeting.organization,
                    place=meeting.place,

                    race_no=self._number(
                        cols[0].get_text(
                            strip=True
                        )
                    ),

                    race_name=(
                        link.get_text(
                            strip=True
                        )
                        if link
                        else ""
                    ),

                    start_time=cols[1].get_text(
                        strip=True
                    ),

                    distance=self._distance(
                        course
                    ),

                    track=self._track(
                        course
                    ),

                    weather=cols[6].get_text(
                        strip=True
                    ),

                    track_condition=cols[7].get_text(
                        strip=True
                    ),

                    horse_count=self._number(
                        cols[8].get_text(
                            strip=True
                        )
                    ),

                    deba_table_url=(
                        urljoin(
                            self.BASE_URL,
                            link.get("href"),
                        )
                        if link and link.get("href")
                        else ""
                    ),
                )
            )

        return races


    def _extract_date_from_url(
        self,
        url: str,
    ) -> str:
        """
        RaceList URLから開催日取得。

        例:
        k_raceDate=2026/07/15
        ↓
        2026/07/15
        """

        parsed = urlparse(
            url
        )

        params = parse_qs(
            parsed.query
        )

        race_date = params.get(
            "k_raceDate"
        )

        if not race_date:
            return ""

        return race_date[0]


    def _number(
        self,
        text: str,
    ) -> int:

        match = re.search(
            r"\d+",
            text,
        )

        return (
            int(match.group())
            if match
            else 0
        )


    def _distance(
        self,
        text: str,
    ) -> int:

        match = re.search(
            r"(\d+)m",
            text,
        )

        return (
            int(match.group(1))
            if match
            else 0
        )


    def _track(
        self,
        text: str,
    ) -> str:

        if "芝" in text:
            return "芝"

        if "障害" in text:
            return "障害"

        return "ダート"