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

    RaceListページから取得する情報を保持する。
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

    jockey: str
    trainer: str

    odds: float
    popularity: int

    weight: float


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