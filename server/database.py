import sqlite3
import json
from typing import List, Optional, Tuple
from shared.models import Player, Match, GameState, PlayerState

class Database:
    def __init__(self, db_path: str = "matchmaking.db"):
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Établit la connexion à la base de données"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def create_tables(self):
        """Crée les tables nécessaires"""
        cursor = self.conn.cursor()
        
        # Table des joueurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                state TEXT NOT NULL,
                rating INTEGER DEFAULT 1000
            )
        """)
        
        # Table des matchs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                player1_id TEXT NOT NULL,
                player2_id TEXT NOT NULL,
                state TEXT NOT NULL,
                board TEXT NOT NULL,
                current_player_id TEXT,
                winner_id TEXT,
                FOREIGN KEY (player1_id) REFERENCES players(id),
                FOREIGN KEY (player2_id) REFERENCES players(id),
                FOREIGN KEY (current_player_id) REFERENCES players(id),
                FOREIGN KEY (winner_id) REFERENCES players(id)
            )
        """)
        
        self.conn.commit()

    def add_player(self, player: Player) -> None:
        """Ajoute un joueur à la base de données"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO players (id, username, state, rating) VALUES (?, ?, ?, ?)",
            (player.id, player.username, player.state.value, player.rating)
        )
        self.conn.commit()

    def get_player(self, player_id: str) -> Optional[Player]:
        """Récupère un joueur par son ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM players WHERE id = ?", (player_id,))
        row = cursor.fetchone()
        if row:
            return Player(
                id=row['id'],
                username=row['username'],
                state=PlayerState(row['state']),
                rating=row['rating']
            )
        return None

    def update_player_state(self, player_id: str, state: PlayerState) -> None:
        """Met à jour l'état d'un joueur"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE players SET state = ? WHERE id = ?",
            (state.value, player_id)
        )
        self.conn.commit()

    def create_match(self, match: Match) -> None:
        """Crée un nouveau match"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO matches 
            (id, player1_id, player2_id, state, board, current_player_id, winner_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                match.id,
                match.player1.id,
                match.player2.id,
                match.state.value,
                json.dumps(match.board),
                match.current_player.id if match.current_player else None,
                match.winner.id if match.winner else None
            )
        )
        self.conn.commit()

    def get_match(self, match_id: str) -> Optional[Match]:
        """Récupère un match par son ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
        row = cursor.fetchone()
        if row:
            player1 = self.get_player(row['player1_id'])
            player2 = self.get_player(row['player2_id'])
            current_player = self.get_player(row['current_player_id']) if row['current_player_id'] else None
            winner = self.get_player(row['winner_id']) if row['winner_id'] else None
            
            if player1 and player2:
                return Match(
                    id=row['id'],
                    player1=player1,
                    player2=player2,
                    state=GameState(row['state']),
                    board=json.loads(row['board']),
                    current_player=current_player,
                    winner=winner
                )
        return None

    def update_match_state(self, match_id: str, state: GameState) -> None:
        """Met à jour l'état d'un match"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE matches SET state = ? WHERE id = ?",
            (state.value, match_id)
        )
        self.conn.commit()

    def update_match_board(self, match_id: str, board: List[List[int]]) -> None:
        """Met à jour le plateau de jeu d'un match"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE matches SET board = ? WHERE id = ?",
            (json.dumps(board), match_id)
        )
        self.conn.commit()

    def set_match_winner(self, match_id: str, winner_id: str) -> None:
        """Définit le gagnant d'un match"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE matches SET winner_id = ? WHERE id = ?",
            (winner_id, match_id)
        )
        self.conn.commit()

    def get_queued_players(self) -> List[Player]:
        """Récupère la liste des joueurs en attente"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM players WHERE state = ?",
            (PlayerState.QUEUED.value,)
        )
        return [
            Player(
                id=row['id'],
                username=row['username'],
                state=PlayerState(row['state']),
                rating=row['rating']
            )
            for row in cursor.fetchall()
        ]

    def close(self):
        """Ferme la connexion à la base de données"""
        if self.conn:
            self.conn.close() 