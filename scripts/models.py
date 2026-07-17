from dataclasses import dataclass


# ==========================
# 開催情報
# ==========================
@dataclass
class RaceMeeting:
    """
    開催情報
    """

    race_date: str
    organization: str
    place: str
    race_list_url: str


# ==========================
# レース情報
# ==========================
@dataclass
class Race:
    """
    レース基本情報
    """

    race_date: str
    organization: str
    place: str

    race_no: int
    race_name: str

    start_time: str

    distance: int
    track: str

    weather: str
    track_condition: str

    horse_count: int

    deba_table_url: str


# ==========================
# 出走馬情報
# ==========================
@dataclass
class Horse:
    """
    出走馬情報
    """

    race_id: int

    frame_no: int
    horse_no: int

    horse_name: str

    # 馬プロフィールページ
    horse_detail_url: str

    jockey: str
    trainer: str

    odds: float
    popularity: int

    weight: float


# ==========================
# 過去走情報
# ==========================
@dataclass
class PastRace:
    """
    能力評価に使用する過去走データ
    """

    horse_id: int

    race_date: str

    place: str

    race_name: str
    race_class: str

    distance: int
    track: str

    weather: str
    track_condition: str

    finish: int

    margin: float

    time: str

    weight: float
    weight_diff: float

    jockey: str

    popularity: int
    odds: float

    # 通過順位（例: "2-2-2-1"）。未取得時は空文字。
    passing_order: str = ""

    # 4コーナー通過順位。未取得時は0。
    fourth_corner_position: int = 0


# ==========================
# AI予想
# ==========================
@dataclass
class Prediction:
    """
    AI予想結果
    """

    race_id: int

    prediction_time: str

    rank: str
    score: float

    buy_flag: bool

    comment: str


# ==========================
# 購入情報
# ==========================
@dataclass
class Bet:
    """
    馬券購入情報
    """

    prediction_id: int

    bet_type: str

    amount: int

    odds: float


# ==========================
# レース結果
# ==========================
@dataclass
class Result:
    """
    レース結果
    """

    race_id: int

    horse_name: str

    finish: int

    payout: int


# ==========================
# AI分析
# ==========================
@dataclass
class Analysis:
    """
    AI分析結果
    """

    race_id: int

    good_points: str
    bad_points: str

    next_action: str
