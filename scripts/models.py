from dataclasses import dataclass


# ==========================
# 開催情報
# ==========================
@dataclass
class RaceMeeting:
    race_date: str
    organization: str
    place: str
    race_list_url: str


# ==========================
# レース情報
# ==========================
@dataclass
class Race:
    race_date: str
    organization: str
    place: str
    race_no: int
    race_name: str
    distance: int
    track: str
    weather: str


# ==========================
# 出走馬情報
# ==========================
@dataclass
class Horse:
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
    prediction_id: int
    bet_type: str
    amount: int
    odds: float


# ==========================
# レース結果
# ==========================
@dataclass
class Result:
    race_id: int
    horse_name: str
    finish: int
    payout: int


# ==========================
# AI分析
# ==========================
@dataclass
class Analysis:
    race_id: int
    good_points: str
    bad_points: str
    next_action: str