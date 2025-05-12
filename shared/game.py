class MorpionGame:
    def __init__(self):
        self.board = [[0 for _ in range(3)] for _ in range(3)]  # 0: vide, 1: X, 2: O
        self.current_player = 1  # 1: X, 2: O
        self.game_over = False
        self.winner = None

    def play_move(self, row: int, col: int) -> bool:
        """
        Joue un coup sur le plateau.
        Retourne True si le coup est valide et joué, False sinon.
        """
        if self.game_over:
            return False
            
        if not (0 <= row < 3 and 0 <= col < 3):
            return False
            
        if self.board[row][col] != 0:
            return False
            
        self.board[row][col] = self.current_player
        
        # Vérifier si le coup gagne la partie
        if self.check_winner():
            self.game_over = True
            self.winner = self.current_player
        # Vérifier si c'est une égalité
        elif self.is_draw():
            self.game_over = True
        else:
            # Changer de joueur
            self.current_player = 3 - self.current_player  # Alterne entre 1 et 2
            
        return True

    def check_winner(self) -> bool:
        """
        Vérifie s'il y a un gagnant.
        Retourne True si un joueur a gagné, False sinon.
        """
        # Vérifier les lignes
        for row in range(3):
            if (self.board[row][0] != 0 and 
                self.board[row][0] == self.board[row][1] == self.board[row][2]):
                return True
                
        # Vérifier les colonnes
        for col in range(3):
            if (self.board[0][col] != 0 and 
                self.board[0][col] == self.board[1][col] == self.board[2][col]):
                return True
                
        # Vérifier la diagonale principale
        if (self.board[0][0] != 0 and 
            self.board[0][0] == self.board[1][1] == self.board[2][2]):
            return True
            
        # Vérifier la diagonale secondaire
        if (self.board[0][2] != 0 and 
            self.board[0][2] == self.board[1][1] == self.board[2][0]):
            return True
            
        return False

    def is_draw(self) -> bool:
        """
        Vérifie si le jeu est une égalité (plateau plein).
        Retourne True si c'est une égalité, False sinon.
        """
        for row in range(3):
            for col in range(3):
                if self.board[row][col] == 0:
                    return False
        return True

    def reset(self):
        """
        Réinitialise le jeu à son état initial.
        """
        self.board = [[0 for _ in range(3)] for _ in range(3)]
        self.current_player = 1
        self.game_over = False
        self.winner = None


class Puissance4Game:
    def __init__(self):
        """Initialise un jeu de Puissance 4 avec un tableau de 6x7"""
        self.ROWS = 6
        self.COLS = 7
        self.board = [[0 for _ in range(self.COLS)] for _ in range(self.ROWS)]  # 0: vide, 1: Rouge, 2: Jaune
        self.current_player = 1  # 1: Rouge, 2: Jaune
        self.game_over = False
        self.winner = None
        
    def play_move(self, row: int, col: int, player=None) -> bool:
        """
        Joue un coup sur le plateau.
        Retourne True si le coup est valide et joué, False sinon.
        
        Noter que pour le Puissance 4, normalement on spécifie seulement la colonne,
        mais pour la compatibilité avec le protocole existant, nous acceptons également une coordonnée de ligne.
        """
        if self.game_over:
            print("Jeu déjà terminé")
            return False
            
        # Vérifier que la colonne est valide
        if not (0 <= col < self.COLS):
            print(f"Colonne {col} invalide")
            return False
            
        # Si un joueur spécifique est passé, utiliser ce joueur
        current = player if player is not None else self.current_player
        
        print(f"Joueur actuel: {current}, player passé: {player}")
        
        # Trouver la position la plus basse disponible dans la colonne
        row_to_play = -1
        for r in range(self.ROWS - 1, -1, -1):
            if self.board[r][col] == 0:
                row_to_play = r
                break
                
        # Si la colonne est pleine, le coup est invalide
        if row_to_play == -1:
            print("Colonne pleine")
            return False
            
        # Jouer le coup
        self.board[row_to_play][col] = current
        
        # Vérifier si le coup gagne la partie
        if self.check_winner(row_to_play, col):
            self.game_over = True
            self.winner = current
            print(f"Joueur {current} a gagné")
        # Vérifier si c'est une égalité
        elif self.is_draw():
            self.game_over = True
            print("Match nul")
        else:
            # Changer de joueur seulement si aucun joueur spécifique n'a été passé
            # ou si un joueur spécifique a été passé mais c'est le joueur courant
            if player is None or player == self.current_player:
                self.current_player = 3 - self.current_player  # Alterne entre 1 et 2
                print(f"Tour suivant: joueur {self.current_player}")
            
        return True
        
    def check_winner(self, row: int, col: int) -> bool:
        """
        Vérifie s'il y a un gagnant à partir de la dernière pièce jouée.
        Retourne True si un joueur a gagné, False sinon.
        """
        player = self.board[row][col]
        
        # Vérifier horizontalement
        count = 0
        for c in range(max(0, col - 3), min(self.COLS, col + 4)):
            if self.board[row][c] == player:
                count += 1
                if count >= 4:
                    return True
            else:
                count = 0
                
        # Vérifier verticalement
        count = 0
        for r in range(max(0, row - 3), min(self.ROWS, row + 4)):
            if self.board[r][col] == player:
                count += 1
                if count >= 4:
                    return True
            else:
                count = 0
                
        # Vérifier diagonale (haut gauche à bas droite)
        count = 0
        r_start = row - min(row, col, 3)
        c_start = col - min(row, col, 3)
        for i in range(7):  # Max 7 positions à vérifier
            r = r_start + i
            c = c_start + i
            if 0 <= r < self.ROWS and 0 <= c < self.COLS:
                if self.board[r][c] == player:
                    count += 1
                    if count >= 4:
                        return True
                else:
                    count = 0
                    
        # Vérifier diagonale (haut droite à bas gauche)
        count = 0
        r_start = row - min(row, self.COLS - 1 - col, 3)
        c_start = col + min(row, self.COLS - 1 - col, 3)
        for i in range(7):  # Max 7 positions à vérifier
            r = r_start + i
            c = c_start - i
            if 0 <= r < self.ROWS and 0 <= c < self.COLS:
                if self.board[r][c] == player:
                    count += 1
                    if count >= 4:
                        return True
                else:
                    count = 0
                    
        return False
        
    def is_draw(self) -> bool:
        """
        Vérifie si le jeu est une égalité (plateau plein).
        Retourne True si c'est une égalité, False sinon.
        """
        # Vérifier si la première ligne (tout en haut) est pleine
        for col in range(self.COLS):
            if self.board[0][col] == 0:
                return False
        return True
        
    def is_game_over(self) -> bool:
        """Retourne True si le jeu est terminé, False sinon."""
        return self.game_over
        
    def get_winner(self) -> int:
        """Retourne le numéro du joueur gagnant, ou None s'il n'y a pas de gagnant."""
        return self.winner
        
    def play_ai_move(self):
        """
        Fonction intelligente pour que l'IA joue un coup.
        Retourne la ligne et la colonne du coup joué.
        """
        import random
        
        print(f"IA réfléchit au coup (joueur {self.current_player})")
        
        # Stratégie prioritaire:
        # 1. Jouer un coup gagnant immédiatement s'il existe
        # 2. Bloquer un coup gagnant de l'adversaire
        # 3. Éviter de jouer un coup qui donne la victoire à l'adversaire au tour suivant
        # 4. Jouer au centre si possible
        # 5. Sinon, coup aléatoire
        
        # 1. Vérifier d'abord s'il y a un coup gagnant
        for col in range(self.COLS):
            # Trouver la position la plus basse disponible dans la colonne
            for row in range(self.ROWS - 1, -1, -1):
                if self.board[row][col] == 0:
                    # Simuler le coup
                    self.board[row][col] = self.current_player
                    # Vérifier si c'est un coup gagnant
                    if self.check_winner(row, col):
                        # Annuler le coup simulé
                        self.board[row][col] = 0
                        print(f"IA joue un coup gagnant en colonne {col}")
                        return row, col
                    # Annuler le coup simulé
                    self.board[row][col] = 0
                    break
        
        # 2. Ensuite, vérifier s'il faut bloquer un coup gagnant de l'adversaire
        opponent = 3 - self.current_player
        for col in range(self.COLS):
            # Trouver la position la plus basse disponible dans la colonne
            for row in range(self.ROWS - 1, -1, -1):
                if self.board[row][col] == 0:
                    # Simuler le coup de l'adversaire
                    self.board[row][col] = opponent
                    # Vérifier si c'est un coup gagnant pour l'adversaire
                    if self.check_winner(row, col):
                        # Annuler le coup simulé
                        self.board[row][col] = 0
                        print(f"IA bloque un coup gagnant en colonne {col}")
                        return row, col
                    # Annuler le coup simulé
                    self.board[row][col] = 0
                    break
                    
        # 3. Éviter les coups qui permettraient à l'adversaire de gagner au tour suivant
        bad_columns = []
        for col in range(self.COLS):
            # Vérifier si la colonne est jouable
            if self.board[0][col] != 0:
                continue  # Colonne pleine
                
            # Trouver où notre jeton atterrirait
            for row in range(self.ROWS - 1, -1, -1):
                if self.board[row][col] == 0:
                    our_row = row
                    break
                    
            # Jouer notre coup
            self.board[our_row][col] = self.current_player
            
            # Vérifier si ça donne un coup gagnant à l'adversaire au-dessus
            if our_row > 0:  # S'il y a de la place au-dessus
                self.board[our_row - 1][col] = opponent
                if self.check_winner(our_row - 1, col):
                    bad_columns.append(col)
                self.board[our_row - 1][col] = 0  # Annuler le coup simulé
            
            # Annuler notre coup
            self.board[our_row][col] = 0
        
        # 4. Préférer jouer au centre
        center_col = self.COLS // 2
        for row in range(self.ROWS - 1, -1, -1):
            if self.board[row][center_col] == 0 and center_col not in bad_columns:
                print(f"IA joue au centre (colonne {center_col})")
                return row, center_col
        
        # 5. Sinon, jouer un coup aléatoire parmi les colonnes non pleines et non désavantageuses
        valid_cols = []
        for col in range(self.COLS):
            if self.board[0][col] == 0 and col not in bad_columns:  # Si la colonne n'est pas pleine et pas désavantageuse
                valid_cols.append(col)
                
        if valid_cols:
            col = random.choice(valid_cols)
            # Trouver la position la plus basse disponible dans la colonne
            for row in range(self.ROWS - 1, -1, -1):
                if self.board[row][col] == 0:
                    print(f"IA joue un coup aléatoire en colonne {col}")
                    return row, col
        
        # Si toutes les colonnes sont désavantageuses ou pleines, jouer dans n'importe quelle colonne non pleine
        if bad_columns:
            for col in range(self.COLS):
                if self.board[0][col] == 0:  # Si la colonne n'est pas pleine
                    for row in range(self.ROWS - 1, -1, -1):
                        if self.board[row][col] == 0:
                            print(f"IA joue un coup non optimal en colonne {col}")
                            return row, col
                    
        # Aucun coup valide trouvé (ne devrait pas arriver si is_draw() est vérifié)
        print("IA ne trouve aucun coup valide")
        return None, None
        
    def reset(self):
        """Réinitialise le jeu à son état initial."""
        self.board = [[0 for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.current_player = 1
        self.game_over = False
        self.winner = None 