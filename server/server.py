import socket
import threading
import json
import uuid
import logging
import time
import sys
import os
import random
from typing import Dict, Optional, List, Tuple

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.models import Player, Match, GameState, PlayerState, Move
from shared.protocol import (
    MessageType,
    create_message,
    send_message,
    receive_message,
    create_start_match_message,
    create_game_update_message,
    create_end_game_message,
    create_error_message,
    create_chat_message,
    create_queue_update_message
)
from shared.game import Puissance4Game

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class Puissance4Server:
    def __init__(self, host: str = "0.0.0.0", port: int = 5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients: Dict[socket.socket, str] = {}
        self.queue: List[socket.socket] = []
        self.matches: Dict[int, Tuple[socket.socket, Optional[socket.socket], Puissance4Game]] = {}
        self.running = False
        self.match_counter = 0
        self.logger = logging.getLogger(__name__)
        self.ai_preferences: Dict[socket.socket, bool] = {}  # Préférence des joueurs concernant l'IA

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            self.logger.info(f"Serveur démarré sur {self.host}:{self.port}")
            threading.Thread(target=self.queue_manager, daemon=True).start()

            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_socket.settimeout(30)
                    self.logger.info(f"Nouvelle connexion de {address}")
                    threading.Thread(
                        target=self.handle_client,
                        args=(client_socket,),
                        daemon=True
                    ).start()
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Erreur lors de l'acceptation d'une connexion: {e}")
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage du serveur: {e}")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        for client in list(self.clients.keys()):
            try:
                client.close()
            except:
                pass
        self.logger.info("Serveur arrêté")

    def queue_manager(self):
        while self.running:
            try:
                # Envoyer une mise à jour du nombre de joueurs en attente à tous les joueurs dans la file
                if self.queue:
                    queue_size = len(self.queue)
                    queue_update = create_queue_update_message(queue_size)
                    for client in self.queue:
                        try:
                            send_message(client, queue_update)
                        except:
                            pass
                
                # Créer des matchs entre joueurs si possible
                if len(self.queue) >= 2:
                    player1 = self.queue.pop(0)
                    player2 = self.queue.pop(0)
                    
                    # Vérifier que les sockets sont toujours valides
                    if player1 not in self.clients or player2 not in self.clients:
                        logging.error(f"Un des joueurs n'est plus connecté: player1 valide: {player1 in self.clients}, player2 valide: {player2 in self.clients}")
                        # Remettre les joueurs valides dans la file
                        if player1 in self.clients:
                            self.queue.append(player1)
                        if player2 in self.clients:
                            self.queue.append(player2)
                        continue
                    
                    # Vérifier que les sockets sont différents
                    if player1 == player2:
                        logging.error(f"Même socket pour les deux joueurs: {player1.getpeername() if hasattr(player1, 'getpeername') else 'inconnu'}")
                        self.queue.append(player1)  # Remettre le joueur dans la file
                        continue
                        
                    # Récupérer les noms des joueurs pour le log
                    player1_name = self.clients.get(player1, "inconnu")
                    player2_name = self.clients.get(player2, "inconnu")
                    
                    logging.info(f"Création d'un match entre {player1_name} (socket: {player1.getpeername() if hasattr(player1, 'getpeername') else 'inconnu'}) et {player2_name} (socket: {player2.getpeername() if hasattr(player2, 'getpeername') else 'inconnu'})")
                    
                    game = Puissance4Game()
                    match_id = self.match_counter
                    self.match_counter += 1
                    self.matches[match_id] = (player1, player2, game)
                    
                    # Log détaillé des joueurs
                    logging.info(f"Création du match {match_id}:")
                    logging.info(f"  - Joueur 1: {self.clients[player1]} (socket: {player1.getpeername()})")
                    logging.info(f"  - Joueur 2: {self.clients[player2]} (socket: {player2.getpeername()})")
                    
                    try:
                        # Création et envoi des messages
                        start_msg1 = create_start_match_message(
                            self.clients[player1],
                            self.clients[player2],
                            1
                        )
                        logging.info(f"Envoi du message de début à {self.clients[player1]}: {start_msg1}")
                        send_result1 = send_message(player1, start_msg1)
                        logging.info(f"Résultat de l'envoi à {self.clients[player1]}: {send_result1}")
                        
                        start_msg2 = create_start_match_message(
                            self.clients[player2],
                            self.clients[player1],
                            2
                        )
                        logging.info(f"Envoi du message de début à {self.clients[player2]}: {start_msg2}")
                        send_result2 = send_message(player2, start_msg2)
                        logging.info(f"Résultat de l'envoi à {self.clients[player2]}: {send_result2}")
                        
                        if not send_result1 or not send_result2:
                            logging.error(f"Échec de l'envoi des messages de début: joueur1: {send_result1}, joueur2: {send_result2}")
                            del self.matches[match_id]
                            # Remettre les joueurs dans la file si l'envoi échoue
                            if send_result1:
                                self.queue.append(player1)
                            if send_result2:
                                self.queue.append(player2)
                            continue
                            
                        self.logger.info(f"Match {match_id} créé entre {self.clients[player1]} et {self.clients[player2]}")
                    except Exception as e:
                        self.logger.error(f"Erreur lors de l'envoi des messages de début de match: {e}")
                        del self.matches[match_id]
                        # Remettre les joueurs dans la file en cas d'erreur
                        self.queue.append(player1)
                        self.queue.append(player2)
                
                # Vérifier si un joueur veut jouer contre l'IA
                elif len(self.queue) == 1 and self.running:
                    player = self.queue[0]  # On regarde le joueur sans le retirer de la file
                    
                    # Vérifier si le joueur a demandé à jouer contre l'IA
                    if player in self.ai_preferences and self.ai_preferences[player]:
                        # Retirer le joueur de la file
                        self.queue.pop(0)
                        
                        if player in self.clients:
                            game = Puissance4Game()
                            match_id = self.match_counter
                            self.match_counter += 1
                            self.matches[match_id] = (player, None, game)
                            try:
                                start_msg = create_start_match_message(
                                    self.clients[player],
                                    "IA",
                                    1
                                )
                                send_message(player, start_msg)
                                self.logger.info(f"Match {match_id} créé entre {self.clients[player]} et l'IA")
                                if game.current_player == 2:
                                    self.play_ai_move(match_id)
                            except Exception as e:
                                self.logger.error(f"Erreur lors de l'envoi du message de début de match avec l'IA: {e}")
                                del self.matches[match_id]
                                self.queue.append(player)  # Remettre le joueur dans la file
                time.sleep(1)  # Attendre plus longtemps pour donner une chance aux joueurs humains de se connecter
            except Exception as e:
                self.logger.error(f"Erreur dans le gestionnaire de file d'attente: {e}")

    def play_ai_move(self, match_id: int):
        if match_id not in self.matches:
            return
        player, _, game = self.matches[match_id]
        if game.is_game_over():
            return
            
        # Ajouter un court délai pour simuler la réflexion de l'IA
        time.sleep(1)
        
        # Faire jouer l'IA
        row, col = game.play_ai_move()
        if row is not None:
            logging.info(f"L'IA joue en (ligne {row}, colonne {col})")
            # Jouer le coup sans spécifier le joueur, laisser le jeu gérer
            success = game.play_move(row, col)
            logging.info(f"Résultat du coup de l'IA: {success}")
            
            if success:
                try:
                    # Envoyer la mise à jour au joueur humain
                    update_msg = create_game_update_message(
                        game.board,
                        game.current_player
                    )
                    logging.info(f"Envoi de la mise à jour après le coup de l'IA: {update_msg}")
                    send_message(player, update_msg)
                    
                    # Vérifier si la partie est terminée
                    if game.is_game_over():
                        winner = game.get_winner()
                        end_msg = create_end_game_message(winner)
                        logging.info(f"Partie terminée, envoi du message de fin: {end_msg}")
                        send_message(player, end_msg)
                        del self.matches[match_id]
                except Exception as e:
                    self.logger.error(f"Erreur lors de l'envoi du coup de l'IA: {e}")
        else:
            logging.error("L'IA n'a pas pu jouer de coup valide")

    def handle_client(self, client_socket: socket.socket):
        try:
            while self.running:
                try:
                    message = receive_message(client_socket)
                    if not message:
                        break
                    self.logger.info(f"Message reçu de {client_socket.getpeername()}: {message}")
                    self.process_message(client_socket, message)
                except socket.error as e:
                    self.logger.error(f"Erreur de socket avec le client {client_socket.getpeername()}: {e}")
                    break
                except Exception as e:
                    self.logger.error(f"Erreur avec le client {client_socket.getpeername()}: {e}")
                    continue
        except Exception as e:
            self.logger.error(f"Erreur fatale avec le client {client_socket.getpeername()}: {e}")
        finally:
            self.remove_client(client_socket)

    def process_message(self, client_socket: socket.socket, message: dict):
        """Traite un message reçu d'un client"""
        try:
            msg_type = message.get("type")
            logging.info(f"Message reçu de type: {msg_type}")
            
            if msg_type == MessageType.JOIN_QUEUE.value:
                username = message.get("username")
                play_with_ai = message.get("play_with_ai", False)
                
                if not username:
                    error_msg = create_error_message("Nom d'utilisateur manquant")
                    send_message(client_socket, error_msg)
                    return
                
                # Si le client était déjà connecté avec un autre pseudo, le nettoyer
                if client_socket in self.clients:
                    old_username = self.clients[client_socket]
                    if old_username != username:
                        self.logger.info(f"Client {old_username} se reconnecte en tant que {username}")
                        # Retirer l'ancien pseudo
                        if client_socket in self.queue:
                            self.queue.remove(client_socket)
                        # Nettoyer les anciens matchs
                        for match_id, (p1, p2, _) in list(self.matches.items()):
                            if client_socket in (p1, p2):
                                del self.matches[match_id]
                
                # Mettre à jour les informations du client
                self.clients[client_socket] = username
                self.ai_preferences[client_socket] = play_with_ai
                
                # Ajouter à la file d'attente si pas déjà dedans
                if client_socket not in self.queue:
                    self.queue.append(client_socket)
                
                self.logger.info(f"{username} a rejoint la file d'attente (IA: {play_with_ai})")
                
                # Envoyer une mise à jour immédiate du nombre de joueurs en attente
                queue_update = create_queue_update_message(len(self.queue))
                for client in self.queue:
                    try:
                        send_message(client, queue_update)
                    except:
                        pass
                
            elif msg_type == MessageType.PLAY_TURN.value:
                match = self.get_match_by_client(client_socket)
                if not match:
                    error_msg = create_error_message("Vous n'êtes pas dans une partie")
                    send_message(client_socket, error_msg)
                    return
                    
                row = message.get("row")
                col = message.get("col")
                if not self.is_valid_move(match, row, col):
                    error_msg = create_error_message("Coup invalide")
                    send_message(client_socket, error_msg)
                    return
                    
                self.update_game_state(match, row, col, client_socket)
                
            elif msg_type == MessageType.CHAT_MESSAGE.value:
                sender = message.get("sender")
                msg = message.get("message")
                logging.info(f"Message de chat reçu de {sender}: {msg}")
                
                # Trouver le match du client
                match = self.get_match_by_client(client_socket)
                logging.info(f"Match trouvé pour {sender}: {match is not None}")
                if not match:
                    logging.error(f"Client {sender} n'est pas dans un match")
                    error_msg = create_error_message("Vous n'êtes pas dans une partie")
                    send_message(client_socket, error_msg)
                    return
                    
                # Vérifier les sockets des joueurs
                p1_info = f"{match['player1'].getpeername()} ({self.clients.get(match['player1'], 'inconnu')})"
                p2_info = "None" if not match['player2'] else f"{match['player2'].getpeername()} ({self.clients.get(match['player2'], 'inconnu')})"
                logging.info(f"Détails du match: joueur1={p1_info}, joueur2={p2_info}")
                    
                # Envoyer le message à l'autre joueur
                if client_socket == match["player1"]:
                    other_client = match["player2"]
                    logging.info(f"Expéditeur est joueur1, destinataire est joueur2")
                else:
                    other_client = match["player1"]
                    logging.info(f"Expéditeur est joueur2, destinataire est joueur1")
                    
                logging.info(f"Autre joueur trouvé: {other_client is not None}, client actuel est player1: {match['player1'] == client_socket}")
                
                if other_client:
                    other_player_name = self.clients.get(other_client, "inconnu")
                    logging.info(f"Envoi du message de {sender} à {other_player_name} (socket: {other_client.getpeername()})")
                    
                    chat_msg = create_chat_message(sender, msg)
                    logging.info(f"Message formaté: {chat_msg}")
                    
                    # Essayer d'envoyer le message avec 3 tentatives
                    success = False
                    max_retries = 3
                    
                    for attempt in range(max_retries):
                        try:
                            success = send_message(other_client, chat_msg)
                            if success:
                                logging.info(f"Message envoyé avec succès à {other_player_name} (tentative {attempt+1})")
                                break
                            else:
                                logging.warning(f"Échec de l'envoi du message à {other_player_name} (tentative {attempt+1})")
                                time.sleep(0.1)  # Petite pause avant de réessayer
                        except Exception as e:
                            logging.error(f"Erreur lors de l'envoi du message (tentative {attempt+1}): {e}")
                            time.sleep(0.1)
                    
                    if not success:
                        logging.error(f"Impossible d'envoyer le message de chat à {other_player_name} après {max_retries} tentatives")
                        error_msg = create_error_message("Impossible d'envoyer le message")
                        send_message(client_socket, error_msg)
                else:
                    # Si c'est une partie contre l'IA, on peut simuler une réponse
                    if match["player2"] is None:
                        ai_responses = [
                            "Bien joué !",
                            "Je réfléchis à mon prochain coup...",
                            "Tu es fort à ce jeu !",
                            "Je vais gagner cette fois-ci !",
                            "Intéressante stratégie...",
                        ]
                        ai_msg = create_chat_message("IA", random.choice(ai_responses))
                        send_message(client_socket, ai_msg)
                
        except Exception as e:
            logging.error(f"Erreur lors du traitement du message: {e}")
            error_msg = create_error_message("Erreur lors du traitement du message")
            send_message(client_socket, error_msg)

    def remove_client(self, client_socket: socket.socket):
        """Gère la déconnexion d'un client"""
        if client_socket in self.clients:
            username = self.clients[client_socket]
            self.logger.info(f"{username} s'est déconnecté")
            
            # Retirer le client de la file d'attente
            if client_socket in self.queue:
                self.queue.remove(client_socket)
                
            # Gérer les matchs en cours
            for match_id, (p1, p2, game) in list(self.matches.items()):
                if client_socket in (p1, p2):
                    other_player = p2 if client_socket == p1 else p1
                    if other_player:
                        try:
                            # Informer l'autre joueur et le remettre dans la file d'attente
                            send_message(other_player, create_error_message("L'adversaire s'est déconnecté"))
                            if other_player not in self.queue:
                                self.queue.append(other_player)
                        except:
                            pass
                    del self.matches[match_id]
            
            # Nettoyer les préférences et le client
            del self.clients[client_socket]
            if client_socket in self.ai_preferences:
                del self.ai_preferences[client_socket]
        
        try:
            client_socket.close()
        except:
            pass

    def get_match_by_client(self, client_socket: socket.socket) -> Optional[Dict]:
        """Trouve le match d'un client"""
        for match_id, (p1, p2, game) in self.matches.items():
            if client_socket in (p1, p2):
                return {
                    "id": match_id,
                    "player1": p1,
                    "player2": p2,
                    "game": game
                }
        return None

    def is_valid_move(self, match: Dict, row: int, col: int) -> bool:
        """Vérifie si un coup est valide"""
        if not match or not match["game"]:
            return False
            
        game = match["game"]
        
        # Pour le Puissance 4, on vérifie que la colonne est valide et pas pleine
        if not (0 <= col < game.COLS):
            return False
            
        # Vérifier que la colonne n'est pas pleine (il existe au moins une case libre)
        for r in range(game.ROWS):
            if game.board[r][col] == 0:
                return True
                
        return False

    def update_game_state(self, match: Dict, row: int, col: int, client_socket: socket.socket):
        """Met à jour l'état du jeu après un coup"""
        if not match or not match["game"]:
            return

        game = match["game"]
        
        # Déterminer quel joueur fait le coup
        if client_socket == match["player1"]:
            player = 1
        elif client_socket == match["player2"]:
            player = 2
        else:
            logging.error(f"Socket client non trouvé dans le match: {client_socket.getpeername() if hasattr(client_socket, 'getpeername') else 'inconnu'}")
            return
        
        # Vérifier si c'est bien le tour du joueur
        if game.current_player != player:
            logging.error(f"Ce n'est pas le tour du joueur {player}, tour actuel: {game.current_player}")
            error_msg = create_error_message("Ce n'est pas votre tour")
            send_message(client_socket, error_msg)
            return
        
        # Pour Puissance 4, on n'utilise pas la ligne passée par le client
        # Mais plutôt celle calculée par le jeu
        logging.info(f"Joueur {player} joue en colonne {col}")
        if game.play_move(None, col):
            # Envoyer la mise à jour aux deux joueurs
            update_msg = create_game_update_message(game.board, game.current_player)
            try:
                send_message(match["player1"], update_msg)
                if match["player2"]:
                    send_message(match["player2"], update_msg)
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi de la mise à jour: {e}")

            # Vérifier si la partie est terminée
            if game.is_game_over():
                winner = game.get_winner()
                end_msg = create_end_game_message(winner)
                try:
                    send_message(match["player1"], end_msg)
                    if match["player2"]:
                        send_message(match["player2"], end_msg)
                    # Supprimer le match
                    del self.matches[match["id"]]
                except Exception as e:
                    logging.error(f"Erreur lors de l'envoi du message de fin: {e}")
            # Si c'est une partie contre l'IA et que c'est au tour de l'IA
            elif match["player2"] is None and game.current_player == 2:
                # Faire jouer l'IA
                self.play_ai_move(match["id"])

if __name__ == "__main__":
    server = Puissance4Server()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
