"""競走馬ページから過去走を取得・保存するオーケストレーター。"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import logging

import requests

from scripts import database
from scripts.logger import get_logger
from scripts.parsers.past_race_parser import PastRaceParser


@dataclass(frozen=True)
class PastRaceFetchTarget:
    """過去走取得に必要な、保存済み馬情報の識別子と詳細ページURL。"""

    horse_id: int
    horse_detail_url: str


@dataclass
class PastRaceFetchResult:
    """過去走取得処理の集計結果。"""

    fetched_count: int = 0
    saved_count: int = 0
    failed_count: int = 0


class PastRaceFetcher:
    """HTTP取得、PastRaceParserによる解析、DB保存を順に実行する。

    ``PastRaceFetchTarget`` 単位で処理が独立しているため、将来は
    ``_process_target`` をワーカーへ委譲して並列取得へ拡張できる。
    ``max_retries`` は一時的な通信エラーへの再試行回数を表す。
    """

    def __init__(
        self,
        parser: PastRaceParser | None = None,
        session: requests.Session | None = None,
        logger: logging.Logger | None = None,
        timeout: float = 10.0,
        max_retries: int = 0,
    ) -> None:
        """取得器を初期化する。

        Args:
            parser: 使用するHTMLパーサー。テスト時に差し替え可能。
            session: 使用するHTTPセッション。テスト時に差し替え可能。
            logger: 使用するロガー。
            timeout: 各HTTPリクエストのタイムアウト秒数。
            max_retries: 通信失敗時の追加試行回数。
        """

        self.parser = parser or PastRaceParser()
        self.session = session or requests.Session()
        self.logger = logger or get_logger(__name__)
        self.timeout = timeout
        self.max_retries = max(0, max_retries)

        headers = getattr(self.session, "headers", None)

        if headers is not None:
            headers.setdefault(
                "User-Agent",
                "KeibaAI/0.9 (+https://www.keiba.go.jp/)",
            )

    def fetch_and_save(
        self,
        targets: Iterable[PastRaceFetchTarget],
    ) -> PastRaceFetchResult:
        """各対象の過去走を取得・解析・保存し、集計結果を返す。

        通信・解析・保存の失敗は対象単位またはレコード単位で記録し、
        以降の対象を継続して処理する。
        """

        result = PastRaceFetchResult()

        for target in targets:
            self._process_target(target, result)

        return result

    def _process_target(
        self,
        target: PastRaceFetchTarget,
        result: PastRaceFetchResult,
    ) -> None:
        """1頭分の取得・解析・保存を実行する。"""

        if target.horse_id <= 0 or not target.horse_detail_url:
            result.failed_count += 1
            self.logger.error(
                "Invalid past-race target: horse_id=%s, url=%r",
                target.horse_id,
                target.horse_detail_url,
            )
            return

        html = self._fetch_html(target)

        if html is None:
            result.failed_count += 1
            return

        try:
            past_races = self.parser.parse(html, target.horse_id)
        except Exception:
            result.failed_count += 1
            self.logger.exception(
                "Failed to parse past races: horse_id=%s, url=%s",
                target.horse_id,
                target.horse_detail_url,
            )
            return

        result.fetched_count += len(past_races)

        for past_race in past_races:
            try:
                if database.save_past_race(past_race):
                    result.saved_count += 1
                else:
                    result.failed_count += 1
                    self.logger.warning(
                        "Failed to save past race: horse_id=%s, date=%s, race=%s",
                        past_race.horse_id,
                        past_race.race_date,
                        past_race.race_name,
                    )
            except Exception:
                result.failed_count += 1
                self.logger.exception(
                    "Unexpected error while saving past race: horse_id=%s, date=%s, race=%s",
                    past_race.horse_id,
                    past_race.race_date,
                    past_race.race_name,
                )

    def _fetch_html(self, target: PastRaceFetchTarget) -> str | None:
        """詳細ページHTMLを取得する。通信失敗時は設定回数まで再試行する。"""

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(
                    target.horse_detail_url,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.text

            except requests.RequestException:
                if attempt == self.max_retries:
                    self.logger.exception(
                        "Failed to fetch past races: horse_id=%s, url=%s, attempts=%s",
                        target.horse_id,
                        target.horse_detail_url,
                        attempt + 1,
                    )
                else:
                    self.logger.warning(
                        "Retrying past-race fetch: horse_id=%s, attempt=%s/%s",
                        target.horse_id,
                        attempt + 1,
                        self.max_retries + 1,
                    )

        return None


def fetch_past_races(
    targets: Iterable[PastRaceFetchTarget],
    *,
    max_retries: int = 0,
) -> PastRaceFetchResult:
    """標準設定のPastRaceFetcherで過去走を取得・保存する便利関数。"""

    return PastRaceFetcher(max_retries=max_retries).fetch_and_save(targets)
