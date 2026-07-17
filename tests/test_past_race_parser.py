"""PastRaceParserの通過順位解析テスト。"""

from __future__ import annotations

import unittest

try:
    import bs4  # noqa: F401
except ImportError:
    BS4_AVAILABLE = False
else:
    BS4_AVAILABLE = True

if BS4_AVAILABLE:
    from scripts.parsers.past_race_parser import PastRaceParser


@unittest.skipUnless(BS4_AVAILABLE, "beautifulsoup4 is required")
class PastRaceParserTest(unittest.TestCase):
    """通過順位と4角位置の解析を検証する。"""

    def test_parses_passing_order_and_fourth_corner_position(self) -> None:
        """通過順位の最後の順位を4角位置として保存する。"""

        html = """
        <table>
          <tr>
            <th>開催日</th><th>競馬場</th><th>レース名</th><th>着順</th>
            <th>通過順位</th>
          </tr>
          <tr>
            <td>2026/07/01</td><td>大井</td><td>テストレース</td><td>1</td>
            <td>3-3-2-1 (16頭)</td>
          </tr>
        </table>
        """

        races = PastRaceParser().parse(html, horse_id=1)

        self.assertEqual(len(races), 1)
        self.assertEqual(races[0].passing_order, "3-3-2-1 (16頭)")
        self.assertEqual(races[0].fourth_corner_position, 1)

    def test_handles_missing_passing_order_safely(self) -> None:
        """通過順位が空なら4角位置は0として扱う。"""

        html = """
        <table>
          <tr><th>開催日</th><th>レース名</th><th>着順</th><th>通過順位</th></tr>
          <tr><td>2026/07/01</td><td>テストレース</td><td>1</td><td>-</td></tr>
        </table>
        """

        races = PastRaceParser().parse(html, horse_id=1)

        self.assertEqual(races[0].passing_order, "-")
        self.assertEqual(races[0].fourth_corner_position, 0)


if __name__ == "__main__":
    unittest.main()
