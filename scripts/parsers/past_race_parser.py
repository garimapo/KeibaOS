"""競走馬ページに掲載された過去走テーブルを解析するモジュール。"""

from __future__ import annotations

import re
import unicodedata

from bs4 import BeautifulSoup
from bs4.element import Tag

from scripts.models import PastRace


class PastRaceParser:
    """HTMLから競走馬の過去走情報だけを抽出するパーサー。

    HTTP通信およびデータベース操作は行わない。テーブル見出しを使って
    列を特定するため、列順の変更や不要な列の追加にある程度対応できる。
    """

    _HEADER_ALIASES = {
        "race_date": ("開催日", "日付", "年月日"),
        "place": ("競馬場", "開催場", "場名"),
        "race_name": ("レース名", "競走名", "レース"),
        "race_class": ("クラス", "条件", "格"),
        "distance": ("距離",),
        "weather": ("天候",),
        "track_condition": ("馬場状態", "馬場状況", "状態"),
        "track": ("コース", "馬場種別", "馬場"),
        "finish": ("着順", "着"),
        "margin": ("着差",),
        "time": ("タイム", "走破"),
        "weight_diff": ("馬体重増減", "馬体重差", "増減"),
        "weight": ("馬体重", "体重"),
        "jockey": ("騎手",),
        "popularity": ("人気",),
        "odds": ("オッズ", "単勝"),
    }

    _FALLBACK_COLUMNS = (
        "race_date",
        "place",
        "race_name",
        "race_class",
        "distance",
        "track",
        "weather",
        "track_condition",
        "finish",
        "margin",
        "time",
        "weight",
        "jockey",
        "popularity",
        "odds",
    )

    def parse(self, html: str, horse_id: int) -> list[PastRace]:
        """競走馬ページHTMLを解析して過去走情報を返す。

        Args:
            html: 取得済みの競走馬ページHTML。
            horse_id: 保存対象となる ``horses.id``。

        Returns:
            解析できた過去走情報。対象テーブルや有効な行がない場合は空リスト。
        """

        if not html or horse_id <= 0:
            return []

        soup = BeautifulSoup(html, "html.parser")
        past_races: list[PastRace] = []

        for table in soup.find_all("table"):
            columns = self._get_columns(table)

            if columns is None:
                continue

            for row in table.find_all("tr"):
                cells = row.find_all("td", recursive=False)

                if not cells:
                    continue

                values = [self._text(cell) for cell in cells]
                past_race = self._parse_row(values, columns, horse_id)

                if past_race is not None:
                    past_races.append(past_race)

        return past_races

    def _get_columns(self, table: Tag) -> dict[str, int] | None:
        """テーブル見出しからPastRaceのフィールドと列番号を対応付ける。"""

        for row in table.find_all("tr"):
            headers = row.find_all("th", recursive=False)

            if not headers:
                continue

            columns = self._columns_from_headers(headers)

            if {"race_date", "finish"}.issubset(columns):
                return columns

        class_names = " ".join(table.get("class", []))

        if re.search(r"past|history|result", class_names, re.IGNORECASE):
            return {
                name: index
                for index, name in enumerate(self._FALLBACK_COLUMNS)
            }

        return None

    def _columns_from_headers(self, headers: list[Tag]) -> dict[str, int]:
        """colspanを考慮して見出しの列番号を取得する。"""

        columns: dict[str, int] = {}
        index = 0

        for header in headers:
            name = self._field_name(self._text(header))

            if name is not None and name not in columns:
                columns[name] = index

            index += self._to_int(header.get("colspan", "1"), default=1)

        return columns

    def _parse_row(
        self,
        values: list[str],
        columns: dict[str, int],
        horse_id: int,
    ) -> PastRace | None:
        """1行分のセル値をPastRaceへ安全に変換する。"""

        value = lambda field: self._value(values, columns, field)
        race_date = self._normalize_date(value("race_date"))
        race_name = value("race_name")

        if not race_date or not race_name:
            return None

        weight, inline_weight_diff = self._parse_weight(value("weight"))
        weight_diff_text = value("weight_diff")

        return PastRace(
            horse_id=horse_id,
            race_date=race_date,
            place=value("place"),
            race_name=race_name,
            race_class=value("race_class"),
            distance=self._to_int(value("distance")),
            track=self._normalize_track(value("track")),
            weather=value("weather"),
            track_condition=value("track_condition"),
            finish=self._to_int(value("finish")),
            margin=self._to_margin(value("margin")),
            time=value("time"),
            weight=weight,
            weight_diff=(
                self._to_float(weight_diff_text)
                if weight_diff_text
                else inline_weight_diff
            ),
            jockey=value("jockey"),
            popularity=self._to_int(value("popularity")),
            odds=self._to_float(value("odds")),
        )

    def _field_name(self, header: str) -> str | None:
        """正規化済みの見出し文字列からモデルのフィールド名を取得する。"""

        normalized = self._normalize(header)
        matches: list[tuple[int, str]] = []

        for field, aliases in self._HEADER_ALIASES.items():
            for alias in aliases:
                if alias in normalized:
                    matches.append((len(alias), field))

        if not matches:
            return None

        return max(matches)[1]

    @staticmethod
    def _value(
        values: list[str],
        columns: dict[str, int],
        field: str,
    ) -> str:
        """存在しない列や不足したセルを空文字として扱う。"""

        index = columns.get(field)

        if index is None or index >= len(values):
            return ""

        return values[index]

    @staticmethod
    def _text(element: Tag) -> str:
        """セルの文字列を空白・全角記号の揺れを抑えて取得する。"""

        return PastRaceParser._normalize(element.get_text(" ", strip=True))

    @staticmethod
    def _normalize(value: str) -> str:
        """空白と全半角の表記揺れを正規化する。"""

        return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()

    @classmethod
    def _normalize_date(cls, value: str) -> str:
        """日付表記を YYYY-MM-DD にそろえ、解釈不能な値は空文字にする。"""

        match = re.search(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})", cls._normalize(value))

        if match is None:
            return ""

        year, month, day = (int(part) for part in match.groups())

        if not 1 <= month <= 12 or not 1 <= day <= 31:
            return ""

        return f"{year:04d}-{month:02d}-{day:02d}"

    @classmethod
    def _to_int(cls, value: str, default: int = 0) -> int:
        """数値を含む文字列を整数へ変換し、欠損値は既定値にする。"""

        match = re.search(r"[-+]?\d+", cls._normalize(str(value)))

        if match is None:
            return default

        try:
            return int(match.group())
        except ValueError:
            return default

    @classmethod
    def _to_float(cls, value: str) -> float:
        """数値を含む文字列を浮動小数点へ変換し、欠損値は0.0にする。"""

        match = re.search(r"[-+]?\d+(?:\.\d+)?", cls._normalize(value).replace(",", ""))

        if match is None:
            return 0.0

        try:
            return float(match.group())
        except ValueError:
            return 0.0

    @classmethod
    def _parse_weight(cls, value: str) -> tuple[float, float]:
        """馬体重と括弧内の増減を抽出する。"""

        normalized = cls._normalize(value)
        weight_match = re.search(r"(\d{2,3})", normalized)

        if weight_match is None:
            return 0.0, 0.0

        diff_match = re.search(r"\(\s*([-+]?\d+)\s*\)", normalized)

        return (
            float(weight_match.group(1)),
            float(diff_match.group(1)) if diff_match else 0.0,
        )

    @classmethod
    def _to_margin(cls, value: str) -> float:
        """着差の分数表記と代表的な文字表記を数値に変換する。"""

        normalized = cls._normalize(value)
        fractions = {
            "ハナ": 0.05,
            "アタマ": 0.1,
            "クビ": 0.2,
        }

        if normalized in fractions:
            return fractions[normalized]

        fraction_match = re.search(r"(\d+)\s*/\s*(\d+)", normalized)

        if fraction_match:
            numerator, denominator = (int(part) for part in fraction_match.groups())

            if denominator != 0:
                return numerator / denominator

        return cls._to_float(normalized)

    @classmethod
    def _normalize_track(cls, value: str) -> str:
        """芝・ダート等の代表的な表記を統一し、未知の表記は保持する。"""

        normalized = cls._normalize(value)

        if "ダ" in normalized:
            return "dirt"
        if "芝" in normalized:
            return "turf"
        if "障" in normalized:
            return "obstacle"

        return normalized
