from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class GameState(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"

class PlayerState(Enum):
    IDLE = "idle"
    QUEUED = "queued"
    PLAYING = "playing"

@dataclass
class Player:
    id: str
    username: str
    state: PlayerState
    rating: int = 1000

@dataclass
class Match:
    id: str
    player1: Player
    player2: Player
    state: GameState
    board: List[List[int]]
    current_player: Optional[Player] = None
    winner: Optional[Player] = None

@dataclass
class Move:
    match_id: str
    player_id: str
    column: int 