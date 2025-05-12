import json
import socket
import struct
import logging
from enum import Enum
from typing import Dict, Any, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('protocol.log'),
        logging.StreamHandler()
    ]
)

class MessageType(Enum):
    """Types de messages supportés par le protocole"""
    JOIN_QUEUE = "JOIN_QUEUE"      # Client rejoint la file d'attente
    START_MATCH = "START_MATCH"    # Début d'un match
    PLAY_TURN = "PLAY_TURN"        # Un joueur joue son tour
    GAME_UPDATE = "GAME_UPDATE"    # Mise à jour de l'état du jeu
    END_GAME = "END_GAME"          # Fin du match
    ERROR = "ERROR"                # Message d'erreur
    CHAT_MESSAGE = "CHAT_MESSAGE"  # Nouveau type de message pour le chat
    QUEUE_UPDATE = "QUEUE_UPDATE"  # Mise à jour du nombre de joueurs en attente

def create_message(message_type: MessageType, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Crée un message JSON avec le type et les données spécifiés.
    
    Args:
        message_type: Type de message
        data: Données additionnelles (optionnel)
        
    Returns:
        Dict contenant le message formaté
    """
    message = {"type": message_type.value}
    if data:
        message.update(data)
    return message

def send_message(sock: socket.socket, message: Dict[str, Any]) -> bool:
    """
    Envoie un message JSON sur le socket.
    
    Args:
        sock: Socket de connexion
        message: Message à envoyer
        
    Returns:
        True si l'envoi a réussi, False sinon
    """
    try:
        # Vérifier que le socket est valide
        if sock is None:
            logging.error("Tentative d'envoi sur un socket None")
            return False
            
        # Convertir le message en JSON
        json_message = json.dumps(message)
        
        # Envoyer la taille du message
        size = len(json_message)
        size_data = struct.pack('!I', size)
        
        # Essayer d'envoyer l'en-tête de taille
        try:
            sock.sendall(size_data)
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi de l'en-tête de taille: {e}")
            return False
            
        # Essayer d'envoyer le message
        try:
            sock.sendall(json_message.encode())
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi du corps du message: {e}")
            return False
            
        logging.info(f"Message envoyé avec succès: {message.get('type')}")
        return True
        
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi du message: {e}")
        return False

def receive_message(sock: socket.socket) -> Optional[Dict[str, Any]]:
    """
    Reçoit un message JSON du socket.
    
    Args:
        sock: Socket de connexion
        
    Returns:
        Le message reçu ou None en cas d'erreur
    """
    try:
        # Recevoir la taille du message
        size_data = sock.recv(4)
        if not size_data:
            return None
            
        size = struct.unpack('!I', size_data)[0]
        
        # Vérifier que la taille est raisonnable (pour éviter les problèmes de mémoire)
        if size > 1048576:  # 1 MB max
            logging.error(f"Taille de message trop grande: {size} bytes")
            return None
            
        # Recevoir le message
        data = b''
        bytes_received = 0
        max_attempts = 10  # Nombre maximal de tentatives
        
        while bytes_received < size:
            try:
                # Calculer combien d'octets restent à recevoir
                remaining = size - bytes_received
                
                # Recevoir les données
                chunk = sock.recv(remaining)
                
                # Si on ne reçoit rien, c'est probablement une déconnexion
                if not chunk:
                    logging.error("Connection closed during message reception")
                    return None
                    
                # Ajouter le chunk aux données
                data += chunk
                bytes_received = len(data)
                
            except socket.timeout:
                logging.warning("Socket timeout during message reception, retrying...")
                continue
                
            except Exception as e:
                logging.error(f"Erreur lors de la réception du message (chunk): {e}")
                return None
                
        # Convertir le message en dictionnaire
        try:
            message = json.loads(data.decode())
            return message
        except json.JSONDecodeError as e:
            logging.error(f"Erreur de décodage JSON: {e}, data: {data[:100]}...")
            return None
            
    except socket.timeout:
        logging.warning("Socket timeout during initial header reception")
        return None
        
    except Exception as e:
        logging.error(f"Erreur lors de la réception du message: {e}")
        return None

# Exemples d'utilisation des messages
def create_join_queue_message(username: str) -> Dict[str, Any]:
    """Crée un message pour rejoindre la file d'attente"""
    return {
        "type": MessageType.JOIN_QUEUE.value,
        "username": username
    }

def create_start_match_message(player1: str, player2: str, player: int) -> dict:
    """Crée un message de début de match"""
    return {
        "type": MessageType.START_MATCH.value,
        "player": player,
        "board": [[0 for _ in range(7)] for _ in range(6)],  # Plateau 6x7 pour Puissance 4
        "opponent": player2 if player == 1 else player1
    }

def create_play_turn_message(row: int, col: int) -> Dict[str, Any]:
    """Crée un message pour jouer un coup"""
    return {
        "type": MessageType.PLAY_TURN.value,
        "row": row,
        "col": col
    }

def create_game_update_message(board: list, current_player: int) -> Dict[str, Any]:
    """Crée un message de mise à jour du jeu"""
    return {
        "type": MessageType.GAME_UPDATE.value,
        "board": board,
        "current_player": current_player
    }

def create_end_game_message(winner: int) -> Dict[str, Any]:
    """Crée un message de fin de partie"""
    return {
        "type": MessageType.END_GAME.value,
        "winner": winner
    }

def create_error_message(message: str) -> Dict[str, Any]:
    """Crée un message d'erreur"""
    return {
        "type": MessageType.ERROR.value,
        "message": message
    }

def create_chat_message(sender: str, message: str) -> dict:
    """Crée un message de chat"""
    return {
        "type": MessageType.CHAT_MESSAGE.value,
        "sender": sender,
        "message": message
    }

def create_queue_update_message(queue_size: int) -> dict:
    """Crée un message de mise à jour de la file d'attente"""
    return {
        "type": MessageType.QUEUE_UPDATE.value,
        "queue_size": queue_size
    } 