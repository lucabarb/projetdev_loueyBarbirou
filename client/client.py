import socket
import json
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, font
import threading
import logging
import sys
import os
import time
import math

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import (
    MessageType,
    create_join_queue_message,
    create_play_turn_message,
    send_message,
    receive_message,
    create_chat_message
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('client.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Fonction utilitaire pour dessiner des rectangles arrondis
def rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    """Dessine un rectangle arrondi sur un canvas"""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1
    ]
    
    return canvas.create_polygon(points, **kwargs, smooth=True)

class Puissance4Client:
    def __init__(self, server_ip: str = "127.0.0.1", server_port: int = 5000):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = None
        self.username = None
        self.game = None
        self.is_my_turn = False
        self.player = None
        self.ROWS = 6  # Nombre de lignes pour le Puissance 4
        self.COLS = 7  # Nombre de colonnes pour le Puissance 4
        self.queue_size = 0  # Nombre de joueurs en attente
        
        # Couleurs pour les jetons et l'UI - Version plus moderne
        self.EMPTY_COLOR = "#f5f5f5"  # Blanc plus lumineux
        self.P1_COLOR = "#e74c3c"     # Rouge
        self.P2_COLOR = "#f1c40f"     # Jaune
        self.BG_COLOR = "#0a192f"     # Bleu foncé profond
        self.FRAME_COLOR = "#112240"  # Bleu encore plus profond
        self.GRID_COLOR = "#1a365d"   # Bleu profond pour la grille
        self.HIGHLIGHT_COLOR = "#64ffda"  # Vert menthe pour les éléments surlignés
        self.TEXT_COLOR = "#ccd6f6"   # Texte blanc bleuté
        self.BUTTON_COLOR = "#64ffda" # Boutons vert menthe
        self.ERROR_COLOR = "#ff5555"  # Rouge pour les erreurs
        self.ACCENT_COLOR = "#64ffda" # Couleur d'accent
        
        # Configuration graphique
        self.CELL_SIZE = 60  # Taille d'une cellule en pixels
        self.TOKEN_RADIUS = 25  # Rayon des jetons
        
        # Création de l'interface
        self.root = tk.Tk()
        self.root.title("Puissance 4")
        self.root.geometry("1000x700")
        self.root.configure(bg=self.BG_COLOR)
        self.root.resizable(False, False)
        
        # Essayer de définir l'icône de l'application
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass  # Ignorer si l'icône n'est pas trouvée
        
        # Chargement des polices
        try:
            # Polices modernes
            self.title_font = font.Font(family="Montserrat", size=24, weight="bold")
            self.subtitle_font = font.Font(family="Montserrat", size=16, weight="bold")
            self.text_font = font.Font(family="Roboto", size=12)
            self.button_font = font.Font(family="Roboto", size=12, weight="bold")
            self.chat_font = font.Font(family="Roboto", size=11)
        except:
            try:
                # Fallback sur Segoe UI
                self.title_font = font.Font(family="Segoe UI", size=22, weight="bold")
                self.subtitle_font = font.Font(family="Segoe UI", size=16, weight="bold")
                self.text_font = font.Font(family="Segoe UI", size=12)
                self.button_font = font.Font(family="Segoe UI", size=12, weight="bold")
                self.chat_font = font.Font(family="Segoe UI", size=11)
            except:
                # Fallback final sur Helvetica
                self.title_font = font.Font(family="Helvetica", size=20, weight="bold")
                self.subtitle_font = font.Font(family="Helvetica", size=14, weight="bold")
                self.text_font = font.Font(family="Helvetica", size=12)
                self.button_font = font.Font(family="Helvetica", size=12, weight="bold")
                self.chat_font = font.Font(family="Helvetica", size=11)
        
        # Frame principale avec ombre portée
        self.main_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Frame d'accueil (login) avec effet de profondeur
        self.login_frame = tk.Frame(self.main_frame, bg=self.FRAME_COLOR, bd=0)
        self.login_frame.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)
        
        # Crédit avec animation - REPOSITIONNÉ EN HAUT
        credit_frame = tk.Frame(self.login_frame, bg=self.FRAME_COLOR, height=30)
        credit_frame.pack(fill=tk.X, pady=(10, 20))
        
        # Conteneur pour centrer le texte de crédit
        credit_center = tk.Frame(credit_frame, bg=self.FRAME_COLOR)
        credit_center.pack(expand=True)
        
        # Texte de crédit
        tk.Label(
            credit_center,
            text="Développé avec ",
            bg=self.FRAME_COLOR,
            fg="#a8b2d1",
            font=("Montserrat", 12)
        ).pack(side=tk.LEFT)
        
        # Cœur animé
        self.heart_label = tk.Label(
            credit_center,
            text="♥",
            bg=self.FRAME_COLOR,
            fg="#ff6b6b",
            font=("Montserrat", 14, "bold")
        )
        self.heart_label.pack(side=tk.LEFT)
        
        def animate_heart():
            if not hasattr(self, 'heart_label') or not self.heart_label.winfo_exists():
                return
            current_size = int(self.heart_label.cget("font").split(" ")[1])
            if current_size == 14:
                self.heart_label.config(
                    font=("Montserrat", 16, "bold"),
                    fg="#ff4757"
                )
            else:
                self.heart_label.config(
                    font=("Montserrat", 14, "bold"),
                    fg="#ff6b6b"
                )
            self.root.after(600, animate_heart)
        
        # Démarrer l'animation du cœur
        self.root.after(1000, animate_heart)
        
        # Logo ou titre stylisé
        title_frame = tk.Frame(self.login_frame, bg=self.FRAME_COLOR)
        title_frame.pack(pady=(20, 30))
        
        main_title = tk.Label(
            title_frame, 
            text="PUISSANCE", 
            font=("Montserrat", 36, "bold"), 
            bg=self.FRAME_COLOR, 
            fg=self.TEXT_COLOR
        )
        main_title.pack()
        
        sub_title = tk.Label(
            title_frame, 
            text="4", 
            font=("Montserrat", 72, "bold"), 
            bg=self.FRAME_COLOR, 
            fg=self.ACCENT_COLOR
        )
        sub_title.pack()
        
        # Frame pour le pseudo avec style plus élégant
        self.username_frame = tk.Frame(self.login_frame, bg=self.FRAME_COLOR)
        self.username_frame.pack(pady=25)
        
        # Cadre pour l'entrée avec effet de brillance
        username_entry_frame = tk.Frame(
            self.username_frame, 
            bg=self.FRAME_COLOR, 
            bd=0, 
            highlightthickness=1, 
            highlightbackground=self.ACCENT_COLOR
        )
        username_entry_frame.pack(pady=10)
        
        self.username_entry = tk.Entry(
            username_entry_frame, 
            font=("Roboto", 14),
            width=20,
            bg=self.FRAME_COLOR,
            fg=self.TEXT_COLOR,
            insertbackground=self.ACCENT_COLOR,
            relief=tk.FLAT,
            bd=10,
            justify='center'
        )
        self.username_entry.pack()
        self.username_entry.insert(0, "Entrez votre pseudo")
        
        # Effet de focus sur l'entrée
        def on_entry_click(event):
            if self.username_entry.get() == "Entrez votre pseudo":
                self.username_entry.delete(0, tk.END)
                self.username_entry.config(fg=self.TEXT_COLOR)
                
        def on_focus_out(event):
            if self.username_entry.get() == "":
                self.username_entry.insert(0, "Entrez votre pseudo")
                self.username_entry.config(fg="#666666")
                
        self.username_entry.bind('<FocusIn>', on_entry_click)
        self.username_entry.bind('<FocusOut>', on_focus_out)
        self.username_entry.config(fg="#666666")
        
        # Option pour jouer contre l'IA avec style amélioré
        ai_frame = tk.Frame(self.login_frame, bg=self.FRAME_COLOR)
        ai_frame.pack(pady=15)
        
        self.ai_var = tk.BooleanVar(value=False)
        
        # Checkbox personnalisé moderne
        self.ai_check = tk.Checkbutton(
            ai_frame, 
            text="Mode IA si aucun joueur disponible", 
            variable=self.ai_var,
            bg=self.FRAME_COLOR,
            fg=self.TEXT_COLOR,
            selectcolor=self.FRAME_COLOR,
            activebackground=self.FRAME_COLOR,
            activeforeground=self.ACCENT_COLOR,
            font=("Roboto", 12),
            cursor="hand2"
        )
        self.ai_check.pack()
        
        # Conteneur pour le bouton avec effet de survol
        button_container = tk.Frame(self.login_frame, bg=self.FRAME_COLOR)
        button_container.pack(pady=30)
        
        # Bouton de connexion avec animation au survol
        self.join_button = tk.Button(
            button_container, 
            text="JOUER", 
            command=self.join_queue,
            bg=self.BUTTON_COLOR,
            fg=self.FRAME_COLOR,
            font=("Montserrat", 14, "bold"),
            padx=40,
            pady=12,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2"
        )
        self.join_button.pack()
        
        # Effet de survol amélioré
        def on_enter(e):
            self.join_button.config(bg=self.TEXT_COLOR)
            
        def on_leave(e):
            self.join_button.config(bg=self.BUTTON_COLOR)
            
        self.join_button.bind("<Enter>", on_enter)
        self.join_button.bind("<Leave>", on_leave)
        
        # Information sur le nombre de joueurs avec style moderne
        self.queue_info = tk.Label(
            self.login_frame, 
            text="0 joueur en attente", 
            bg=self.FRAME_COLOR,
            fg=self.TEXT_COLOR,
            font=("Roboto", 12)
        )
        self.queue_info.pack(pady=15)
        
        # Frame de jeu (initialement cachée)
        self.game_container = tk.Frame(self.main_frame, bg=self.BG_COLOR)
        # Elle sera affichée avec .pack() lorsque le joueur sera dans une partie
        
        # Frame gauche (jeu)
        self.game_frame = tk.Frame(self.game_container, bg=self.FRAME_COLOR, bd=0, relief=tk.FLAT)
        self.game_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Information sur la partie
        self.game_info_frame = tk.Frame(self.game_frame, bg=self.FRAME_COLOR)
        self.game_info_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Label pour les messages de statut
        self.status_label = tk.Label(
            self.game_info_frame, 
            text="En attente d'un adversaire...", 
            bg=self.FRAME_COLOR, 
            fg=self.TEXT_COLOR, 
            font=self.subtitle_font
        )
        self.status_label.pack(side=tk.LEFT, padx=15)
        
        # Bouton Rejouer avec style moderne
        self.replay_button = tk.Button(
            self.game_info_frame,
            text="REJOUER",
            command=self.new_game,
            bg=self.BUTTON_COLOR,
            fg=self.TEXT_COLOR,
            font=self.button_font,
            relief=tk.FLAT,
            padx=10,
            pady=5,
            bd=0,
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.replay_button.pack(side=tk.RIGHT, padx=5)
        
        # Bouton de reconnexion avec style moderne
        self.reconnect_button = tk.Button(
            self.game_info_frame, 
            text="RECONNECTER", 
            command=self.reconnect, 
            bg=self.ERROR_COLOR, 
            fg=self.TEXT_COLOR, 
            font=self.button_font,
            relief=tk.FLAT,
            padx=10,
            pady=5,
            bd=0,
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.reconnect_button.pack(side=tk.RIGHT, padx=15)
        
        # Plateau de jeu
        self.board_frame = tk.Frame(self.game_frame, bg=self.FRAME_COLOR)
        self.board_frame.pack(expand=True, fill=tk.BOTH, padx=15, pady=(0, 15))
        
        # Canvas pour dessiner le plateau
        self.board_canvas_width = self.COLS * self.CELL_SIZE + 40  # Marge supplémentaire
        self.board_canvas_height = (self.ROWS + 1) * self.CELL_SIZE + 40  # +1 pour la zone de sélection
        
        # Fond stylisé pour le canvas
        canvas_frame = tk.Frame(self.board_frame, bg=self.GRID_COLOR, bd=0, relief=tk.FLAT)
        canvas_frame.pack(expand=True)
        
        self.board_canvas = tk.Canvas(
            canvas_frame,
            width=self.board_canvas_width,
            height=self.board_canvas_height,
            bg=self.GRID_COLOR,
            highlightthickness=0
        )
        self.board_canvas.pack(padx=15, pady=15)
        
        # Événements pour le canvas du plateau
        self.board_canvas.bind("<Motion>", self.on_mouse_move)
        self.board_canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Variable pour stocker l'ID du jeton fantôme et ses composants
        self.ghost_token = None
        self.ghost_components = []
        self.current_col = -1
        
        # Frame droite (chat)
        self.chat_container = tk.Frame(self.game_container, bg=self.FRAME_COLOR, bd=0, relief=tk.FLAT, width=320)
        self.chat_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        self.chat_container.pack_propagate(False)  # Empêche le redimensionnement du conteneur
        
        # Titre du chat avec bordure inférieure
        self.chat_title_frame = tk.Frame(self.chat_container, bg=self.FRAME_COLOR)
        self.chat_title_frame.pack(fill=tk.X, pady=(15, 5))
        
        self.chat_title_label = tk.Label(
            self.chat_title_frame, 
            text="CONVERSATION", 
            bg=self.FRAME_COLOR, 
            fg=self.TEXT_COLOR, 
            font=self.subtitle_font
        )
        self.chat_title_label.pack(padx=15, pady=5)
        
        # Ligne de séparation
        separator = tk.Frame(self.chat_container, height=1, bg="#3a3a3a")
        separator.pack(fill=tk.X, padx=10)
        
        # Zone d'affichage des messages
        self.chat_frame = tk.Frame(self.chat_container, bg=self.FRAME_COLOR)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Créer un widget Text avec défilement pour les messages
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame, 
            wrap=tk.WORD, 
            bg="#0c1524", 
            fg=self.TEXT_COLOR, 
            font=self.chat_font,
            bd=0,
            padx=10,
            pady=10,
            height=15,
            relief=tk.FLAT,
            insertbackground=self.TEXT_COLOR
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)  # Lecture seule, pour éviter les modifications
        
        # Personnaliser la barre de défilement
        self.chat_display.config(
            selectbackground=self.BUTTON_COLOR,
            insertbackground=self.TEXT_COLOR
        )
        
        # Configurer les styles de texte pour les messages
        self.chat_display.tag_configure("bold", font=font.Font(family="Roboto", size=11, weight="bold"))
        self.chat_display.tag_configure("system", foreground="#3498db")  # Messages système en bleu
        self.chat_display.tag_configure("self", foreground="#2ecc71")    # Nos messages en vert
        self.chat_display.tag_configure("other", foreground="#e74c3c")   # Messages des autres en rouge
        self.chat_display.tag_configure("timestamp", foreground="#888888", font=font.Font(family="Roboto", size=9))
        
        # Zone de saisie des messages
        self.input_frame = tk.Frame(self.chat_container, bg=self.FRAME_COLOR, height=80)
        self.input_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Ligne de séparation au-dessus de l'entrée
        separator2 = tk.Frame(self.chat_container, height=1, bg="#3a3a3a")
        separator2.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Cadre pour le champ de saisie
        message_entry_frame = tk.Frame(self.input_frame, bg="#0c1524", bd=0, highlightthickness=0)
        message_entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Zone de texte pour la saisie des messages
        self.message_entry = tk.Entry(
            message_entry_frame, 
            font=self.text_font, 
            bg="#0c1524",
            fg=self.TEXT_COLOR,
            relief=tk.FLAT,
            bd=8,
            insertbackground=self.TEXT_COLOR
        )
        self.message_entry.pack(fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", lambda event: self.send_chat_message())
        
        # Bouton d'envoi plus stylisé
        self.send_button = tk.Button(
            self.input_frame, 
            text="ENVOYER", 
            command=self.send_chat_message,
            bg=self.BUTTON_COLOR,
            fg=self.TEXT_COLOR,
            font=self.button_font,
            relief=tk.FLAT,
            padx=15,
            pady=8,
            bd=0,
            activebackground=self.HIGHLIGHT_COLOR,
            activeforeground=self.TEXT_COLOR,
            cursor="hand2"
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Effet de survol sur le bouton d'envoi
        self.send_button.bind("<Enter>", lambda e: self.send_button.config(bg=self.HIGHLIGHT_COLOR))
        self.send_button.bind("<Leave>", lambda e: self.send_button.config(bg=self.BUTTON_COLOR))
        
        # Thread pour recevoir les messages du serveur
        self.receive_thread = None
        
    def connect(self):
        """Établit la connexion avec le serveur"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            self.socket.settimeout(60)  # Augmenter le délai d'attente à 60 secondes
            logging.info("Connecté au serveur")
            return True
        except Exception as e:
            logging.error(f"Erreur de connexion: {e}")
            messagebox.showerror("Erreur", "Impossible de se connecter au serveur")
            return False
            
    def join_queue(self):
        """Rejoint la file d'attente"""
        self.username = self.username_entry.get().strip()
        if not self.username:
            messagebox.showwarning("Attention", "Veuillez entrer un pseudo")
            return
            
        if not self.connect():
            return
            
        # Envoyer le message de connexion avec l'option IA
        message = create_join_queue_message(self.username)
        message["play_with_ai"] = self.ai_var.get()
        
        if not send_message(self.socket, message):
            messagebox.showerror("Erreur", "Impossible d'envoyer le message au serveur")
            return
        
        # Cacher l'écran de login et afficher l'écran de jeu
        self.login_frame.pack_forget()
        self.game_container.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Dessiner le plateau vide
        self.draw_board()
        
        # Activer le bouton de reconnexion
        self.reconnect_button.config(state=tk.NORMAL)
        self.status_label.config(text="En attente d'un adversaire...")
        
        # Ajouter un message système dans le chat
        self.add_chat_message("Système", "Connexion au serveur réussie. En attente d'un adversaire...", "system")
        
        # Démarrer le thread de réception
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
    def reconnect(self):
        """Reconnecte au serveur"""
        try:
            # Fermer l'ancienne connexion si elle existe
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            
            # Réinitialiser l'état du jeu
            self.game = None
            self.is_my_turn = False
            self.player = None
            
            # Désactiver le bouton rejouer
            self.replay_button.config(state=tk.DISABLED)
            
            if not self.connect():
                return
            
            # Envoyer le message de connexion avec l'option IA
            message = create_join_queue_message(self.username)
            message["play_with_ai"] = self.ai_var.get()
            
            if not send_message(self.socket, message):
                messagebox.showerror("Erreur", "Impossible d'envoyer le message au serveur")
                return
            
            # Mettre à jour l'interface
            self.status_label.config(text="Reconnecté. En attente d'un adversaire...")
            self.add_chat_message("Système", "Reconnexion au serveur réussie. En attente d'un adversaire...", "system")
            
            # Redessiner le plateau vide
            self.draw_board()
            
            # Démarrer le thread de réception
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
        except Exception as e:
            logging.error(f"Erreur lors de la reconnexion: {e}")
            messagebox.showerror("Erreur", "Une erreur est survenue lors de la reconnexion")
        
    def receive_messages(self):
        """Reçoit les messages du serveur"""
        try:
            while True:
                try:
                    message = receive_message(self.socket)
                    if not message:
                        logging.error("Connexion perdue avec le serveur")
                        self.root.after(0, lambda: messagebox.showerror("Erreur", "Connexion perdue avec le serveur"))
                        self.root.after(0, lambda: self.reconnect_button.config(state=tk.NORMAL))
                        break
                        
                    logging.info(f"Message reçu: {message}")  # Log de debug
                    self.handle_server_message(message)
                    
                except socket.error as e:
                    logging.error(f"Erreur de socket: {e}")
                    self.root.after(0, lambda: messagebox.showerror("Erreur", "Connexion perdue avec le serveur"))
                    self.root.after(0, lambda: self.reconnect_button.config(state=tk.NORMAL))
                    break
                    
                except Exception as e:
                    logging.error(f"Erreur de réception: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Erreur fatale: {e}")
        finally:
            try:
                self.socket.close()
            except:
                pass
            
    def handle_server_message(self, message: dict):
        """Traite les messages reçus du serveur"""
        try:
            msg_type = message.get("type")
            print(f">> Message reçu de type: {msg_type}")  # Log de debug
            logging.info(f"Message reçu du serveur: {message}")
            
            if msg_type == MessageType.QUEUE_UPDATE.value:
                # Mise à jour du nombre de joueurs en attente
                queue_size = message.get("queue_size", 0)
                plural = "s" if queue_size > 1 else ""
                self.queue_info.config(text=f"{queue_size} joueur{plural} en attente")
                
            elif msg_type == MessageType.START_MATCH.value:
                self.player = message.get("player")
                self.game = message.get("board")
                self.is_my_turn = self.player == 1
                opponent = message.get("opponent", "Adversaire")
                
                # Activer le bouton rejouer
                self.replay_button.config(state=tk.NORMAL)
                
                # Mettre à jour l'interface
                if self.is_my_turn:
                    self.status_label.config(text=f"Match contre {opponent} - À vous de jouer !", fg=self.HIGHLIGHT_COLOR)
                else:
                    self.status_label.config(text=f"Match contre {opponent} - Tour de l'adversaire", fg="white")
                
                # Effacer le chat au début d'une nouvelle partie
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.delete(1.0, tk.END)
                self.chat_display.config(state=tk.DISABLED)
                
                self.draw_board()
                self.add_chat_message("Système", f"Match commencé contre {opponent}", "system")
                logging.info(f"Match commencé contre {opponent} en tant que joueur {self.player}")
                
            elif msg_type == MessageType.GAME_UPDATE.value:
                self.game = message.get("board")
                current_player = message.get("current_player")
                self.is_my_turn = current_player == self.player
                
                # Mettre à jour l'interface
                if self.is_my_turn:
                    self.status_label.config(text="À vous de jouer !", fg=self.HIGHLIGHT_COLOR)
                else:
                    self.status_label.config(text="Tour de l'adversaire", fg="white")
                
                self.draw_board()
                
            elif msg_type == MessageType.END_GAME.value:
                winner = message.get("winner")
                if winner:
                    if winner == self.player:
                        result_text = "Vous avez gagné !"
                        self.status_label.config(text=result_text, fg=self.HIGHLIGHT_COLOR)
                    else:
                        result_text = "L'adversaire a gagné !"
                        self.status_label.config(text=result_text, fg=self.P1_COLOR)
                    
                    self.add_chat_message("Système", result_text, "system")
                else:
                    self.status_label.config(text="Match nul !", fg=self.P2_COLOR)
                    self.add_chat_message("Système", "Match nul !", "system")
                
                self.is_my_turn = False
                self.draw_board()
                
                # Proposer une nouvelle partie
                self.root.after(1000, lambda: messagebox.askyesno(
                    "Partie terminée", 
                    f"{result_text}\nVoulez-vous jouer à nouveau ?",
                    command=lambda response: self.new_game() if response else None
                ))
                
            elif msg_type == MessageType.CHAT_MESSAGE.value:
                sender = message.get("sender", "Inconnu")
                msg = message.get("message", "")
                
                if not sender or not msg:
                    logging.error(f"Message de chat incomplet reçu: {message}")
                    return
                    
                print(f">> Message de chat reçu: {sender}: {msg}")  # Log de debug
                logging.info(f"Message de chat reçu: {sender}: {msg}")
                
                # Traiter le message de chat sur le thread principal pour éviter les problèmes d'UI
                self.root.after(0, lambda: self.add_chat_message(sender, msg, "other"))
                
            elif msg_type == MessageType.ERROR.value:
                error_msg = message.get("message", "Erreur inconnue")
                logging.error(f"Message d'erreur reçu: {error_msg}")
                
                # Si l'adversaire s'est déconnecté, proposer de rejouer
                if "déconnecté" in error_msg.lower():
                    self.add_chat_message("Système", "L'adversaire s'est déconnecté", "system")
                    self.status_label.config(text="L'adversaire s'est déconnecté", fg=self.ERROR_COLOR)
                    # Proposer une nouvelle partie
                    self.root.after(1000, lambda: messagebox.askyesno(
                        "Adversaire déconnecté", 
                        "L'adversaire s'est déconnecté.\nVoulez-vous chercher une nouvelle partie ?",
                        command=lambda response: self.new_game() if response else None
                    ))
                else:
                    # Afficher l'erreur sur le thread principal
                    self.root.after(0, lambda: messagebox.showerror("Erreur", error_msg))
                    self.root.after(0, lambda: self.add_chat_message("Système", f"Erreur: {error_msg}", "system"))
                
        except Exception as e:
            print(f"Erreur dans handle_server_message: {e}")  # Log de debug
            logging.error(f"Erreur lors du traitement du message: {e}")
            self.root.after(0, lambda: messagebox.showerror("Erreur", "Une erreur est survenue lors du traitement du message"))
    
    def new_game(self):
        """Démarre une nouvelle partie"""
        try:
            # Fermer la connexion existante
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            
            # Réinitialiser l'état du jeu
            self.game = None
            self.is_my_turn = False
            self.player = None
            
            # Désactiver le bouton rejouer
            self.replay_button.config(state=tk.DISABLED)
            
            # Se reconnecter au serveur
            if not self.connect():
                return
                
            # Envoyer le message de connexion avec l'option IA
            message = create_join_queue_message(self.username)
            message["play_with_ai"] = self.ai_var.get()
            
            if not send_message(self.socket, message):
                messagebox.showerror("Erreur", "Impossible d'envoyer le message au serveur")
                return
            
            # Mettre à jour l'interface
            self.status_label.config(text="En attente d'un adversaire...")
            self.add_chat_message("Système", "En attente d'un adversaire...", "system")
            
            # Effacer le chat
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            
            # Redessiner le plateau vide
            self.draw_board()
            
            # Démarrer le thread de réception
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
        except Exception as e:
            logging.error(f"Erreur lors du redémarrage de la partie: {e}")
            messagebox.showerror("Erreur", "Une erreur est survenue lors du redémarrage de la partie")
            
    def add_chat_message(self, sender: str, message: str, tag="other"):
        """Ajoute un message dans la zone de chat avec un style moderne et élégant"""
        try:
            # Vérifier que les widgets existent
            if not hasattr(self, 'chat_display'):
                print("Erreur: chat_display n'existe pas")
                return
                
            self.chat_display.config(state=tk.NORMAL)
            
            # Ajouter l'horodatage
            current_time = time.strftime("%H:%M")
            
            # Insérer un peu d'espace vertical entre les messages
            self.chat_display.insert(tk.END, "\n", tag)
            
            # Différencier visuellement les types de messages
            if tag == "system":
                # Message système
                self.chat_display.insert(tk.END, f"[{current_time}] ", "timestamp")
                self.chat_display.insert(tk.END, f"SYSTÈME\n", ("bold", "system"))
                
                # Insérer le message avec une indentation
                self.chat_display.insert(tk.END, f"  {message}\n", "system")
                
                # Ajouter une ligne de séparation discrète
                self.chat_display.insert(tk.END, "─" * 30 + "\n", "timestamp")
                
            elif tag == "self":
                # Message de l'utilisateur
                self.chat_display.insert(tk.END, f"[{current_time}] ", "timestamp")
                self.chat_display.insert(tk.END, f"VOUS\n", ("bold", "self"))
                
                # Créer une bulle de message
                self.chat_display.insert(tk.END, f"  {message}\n", "self")
                
            else:
                # Message d'un autre joueur
                self.chat_display.insert(tk.END, f"[{current_time}] ", "timestamp")
                self.chat_display.insert(tk.END, f"{sender}\n", ("bold", "other"))
                
                # Créer une bulle de message
                self.chat_display.insert(tk.END, f"  {message}\n", "other")
            
            # Faire défiler jusqu'au dernier message
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"Erreur dans add_chat_message: {e}")
            
    def send_chat_message(self):
        """Envoie un message de chat avec une interface améliorée"""
        if not self.socket or not self.username:
            logging.error("Tentative d'envoi de message sans connexion ou sans nom d'utilisateur")
            return
            
        message = self.message_entry.get().strip()
        if not message:
            return
            
        try:
            logging.info(f"Envoi du message de chat: {message}")
            chat_msg = create_chat_message(self.username, message)
            
            # Essayer jusqu'à 3 fois d'envoyer le message
            max_retries = 3
            result = False
            
            for attempt in range(max_retries):
                result = send_message(self.socket, chat_msg)
                if result:
                    break
                time.sleep(0.1)  # Petite pause avant de réessayer
                
            if result:
                # Ajouter le message à notre propre chat
                self.add_chat_message(self.username, message, "self")
                # Vider la zone de saisie
                self.message_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Erreur", "Impossible d'envoyer le message")
                
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi du message: {e}")
            messagebox.showerror("Erreur", "Une erreur est survenue lors de l'envoi du message")
            
    def play_move(self, col: int):
        """Joue un coup dans la colonne sélectionnée"""
        if not self.is_my_turn or not self.game:
            return
            
        try:
            # Trouver la première position libre dans la colonne (de bas en haut)
            row = -1
            for r in range(self.ROWS - 1, -1, -1):
                if self.game[r][col] == 0:
                    row = r
                    break
                    
            if row == -1:
                # Colonne pleine
                return
            
            # Envoyer le message au serveur
            message = create_play_turn_message(row, col)
            if not send_message(self.socket, message):
                logging.error("Erreur lors de l'envoi du coup")
                messagebox.showerror("Erreur", "Impossible d'envoyer le coup au serveur")
                return
                
            # Désactiver temporairement le plateau pendant l'envoi
            self.is_my_turn = False
            
            # Animer la chute du jeton
            self.animate_token_drop(col, row)
            
        except Exception as e:
            logging.error(f"Erreur lors du coup: {e}")
            messagebox.showerror("Erreur", "Une erreur est survenue lors de l'envoi du coup")
            
    def update_board(self):
        """Met à jour l'affichage du plateau"""
        if not self.game:
            return
            
        self.draw_board()
                    
    def draw_counter(self, canvas, color):
        """Dessine un jeton sur le canvas"""
        canvas.config(bg=color)
                    
    def draw_board(self):
        """Dessine le plateau de jeu avec un style simplifié mais fonctionnel"""
        self.board_canvas.delete("all")  # Effacer tout
        
        # Dessiner le fond du plateau
        self.board_canvas.create_rectangle(
            15, 
            15 + self.CELL_SIZE,  # Laisser de l'espace pour la sélection
            15 + self.COLS * self.CELL_SIZE, 
            15 + (self.ROWS + 1) * self.CELL_SIZE,
            fill=self.GRID_COLOR,
            outline=self.GRID_COLOR,
            width=2
        )
        
        # Zone de sélection (partie supérieure)
        selection_zone = self.board_canvas.create_rectangle(
            15, 
            15,
            15 + self.COLS * self.CELL_SIZE, 
            15 + self.CELL_SIZE,
            fill=self.BG_COLOR,
            outline="",
        )
        
        # Dessiner les trous pour les jetons
        for row in range(self.ROWS):
            for col in range(self.COLS):
                # Calculer le centre du cercle
                x = 15 + col * self.CELL_SIZE + self.CELL_SIZE // 2
                y = 15 + (row + 1) * self.CELL_SIZE + self.CELL_SIZE // 2  # +1 pour l'espace de sélection
                
                # Dessiner le cercle (trou)
                self.board_canvas.create_oval(
                    x - self.TOKEN_RADIUS,
                    y - self.TOKEN_RADIUS,
                    x + self.TOKEN_RADIUS,
                    y + self.TOKEN_RADIUS,
                    fill=self.EMPTY_COLOR,
                    outline="",
                    width=0
                )
        
        # Dessiner les jetons si une partie est en cours
        if self.game:
            for row in range(self.ROWS):
                for col in range(self.COLS):
                    if self.game[row][col] != 0:
                        self.draw_token(row, col, self.game[row][col])
    
    def draw_token(self, row, col, player):
        """Dessine un jeton à la position spécifiée avec un style simple mais efficace"""
        # Calculer le centre du jeton
        x = 15 + col * self.CELL_SIZE + self.CELL_SIZE // 2
        y = 15 + (row + 1) * self.CELL_SIZE + self.CELL_SIZE // 2  # +1 pour l'espace de sélection
        
        # Couleur du jeton
        color = self.P1_COLOR if player == 1 else self.P2_COLOR
        
        # Créer des nuances pour l'effet 3D
        darker = self.darken_color(color, 0.7)
        
        # Dessiner le cercle principal
        token = self.board_canvas.create_oval(
            x - self.TOKEN_RADIUS,
            y - self.TOKEN_RADIUS,
            x + self.TOKEN_RADIUS,
            y + self.TOKEN_RADIUS,
            fill=color,
            outline=""
        )
        
        # Ajouter un reflet pour un effet 3D simple
        highlight_radius = self.TOKEN_RADIUS * 0.5
        highlight = self.board_canvas.create_oval(
            x - self.TOKEN_RADIUS * 0.6,
            y - self.TOKEN_RADIUS * 0.6,
            x - self.TOKEN_RADIUS * 0.6 + highlight_radius,
            y - self.TOKEN_RADIUS * 0.6 + highlight_radius,
            fill="white",
            outline="",
            stipple="gray50"  # Semi-transparent
        )
        
        return token
        
    def darken_color(self, hex_color, factor=0.7):
        """Assombrit une couleur hexadécimale"""
        # Enlever le # si présent
        hex_color = hex_color.lstrip("#")
        
        # Convertir en RGB
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Assombrir
        rgb_darkened = tuple(int(c * factor) for c in rgb)
        
        # Reconvertir en hex
        return f"#{rgb_darkened[0]:02x}{rgb_darkened[1]:02x}{rgb_darkened[2]:02x}"
        
    def lighten_color(self, hex_color, factor=0.5):
        """Éclaircit une couleur hexadécimale"""
        # Enlever le # si présent
        hex_color = hex_color.lstrip("#")
        
        # Convertir en RGB
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Éclaircir
        rgb_lightened = tuple(int(c + (255 - c) * factor) for c in rgb)
        
        # Reconvertir en hex
        return f"#{rgb_lightened[0]:02x}{rgb_lightened[1]:02x}{rgb_lightened[2]:02x}"
        
    def show_ghost_token(self, col):
        """Affiche un jeton fantôme simplifié au-dessus de la colonne où la souris se trouve"""
        if not self.is_my_turn or col == -1 or col >= self.COLS:
            return
        
        # Vérifier si la colonne est pleine
        is_full = True
        for row in range(self.ROWS):
            if self.game and self.game[row][col] == 0:
                is_full = False
                break
        
        if is_full:
            return
        
        # Supprimer l'ancien jeton fantôme et ses composants
        if self.ghost_token:
            self.board_canvas.delete(self.ghost_token)
            for item in self.ghost_components:
                self.board_canvas.delete(item)
            self.ghost_components = []
            
        # Calculer la position du jeton fantôme
        x = 15 + col * self.CELL_SIZE + self.CELL_SIZE // 2
        y = 15 + self.CELL_SIZE // 2  # Première ligne (zone de sélection)
        
        # Déterminer la couleur (celle du joueur actuel)
        color = self.P1_COLOR if self.player == 1 else self.P2_COLOR
        
        # Dessiner le jeton fantôme principal (semi-transparent)
        self.ghost_token = self.board_canvas.create_oval(
            x - self.TOKEN_RADIUS,
            y - self.TOKEN_RADIUS,
            x + self.TOKEN_RADIUS,
            y + self.TOKEN_RADIUS,
            fill=color,
            outline="",
            stipple="gray25"  # Rend le jeton semi-transparent
        )
        self.ghost_components.append(self.ghost_token)
        
        # Ajouter un reflet pour un effet 3D simple
        highlight_radius = self.TOKEN_RADIUS * 0.5
        ghost_highlight = self.board_canvas.create_oval(
            x - self.TOKEN_RADIUS * 0.6,
            y - self.TOKEN_RADIUS * 0.6,
            x - self.TOKEN_RADIUS * 0.6 + highlight_radius,
            y - self.TOKEN_RADIUS * 0.6 + highlight_radius,
            fill="white",
            outline="",
            stipple="gray12"  # Très transparent
        )
        self.ghost_components.append(ghost_highlight)
        
    def on_mouse_move(self, event):
        """Gère le mouvement de la souris sur le plateau de jeu"""
        if not self.is_my_turn or not self.game:
            return
            
        # Calculer la colonne où se trouve la souris
        col = (event.x - 10) // self.CELL_SIZE
        
        # Vérifier que la colonne est valide
        if 0 <= col < self.COLS:
            if col != self.current_col:
                self.current_col = col
                self.show_ghost_token(col)
        else:
            # Hors du plateau, supprimer le jeton fantôme
            if self.ghost_token:
                self.board_canvas.delete(self.ghost_token)
                self.ghost_token = None
            self.current_col = -1
    
    def on_canvas_click(self, event):
        """Gère le clic sur le plateau de jeu"""
        if not self.is_my_turn or not self.game:
            return
            
        # Calculer la colonne cliquée
        col = (event.x - 10) // self.CELL_SIZE
        
        # Vérifier que la colonne est valide
        if 0 <= col < self.COLS:
            self.play_move(col)
            
    def animate_token_drop(self, col, row):
        """Anime la chute d'un jeton simplifiée mais fonctionnelle"""
        if not self.game:
            return
            
        # Supprimer le jeton fantôme et ses composants
        if self.ghost_token:
            self.board_canvas.delete(self.ghost_token)
            for item in self.ghost_components:
                self.board_canvas.delete(item)
            self.ghost_components = []
            self.ghost_token = None
            
        # Position finale du jeton
        final_y = 15 + (row + 1) * self.CELL_SIZE + self.CELL_SIZE // 2
        
        # Position initiale (en haut de la colonne)
        initial_y = 15 + self.CELL_SIZE // 2
        
        # Créer le jeton à animer
        x = 15 + col * self.CELL_SIZE + self.CELL_SIZE // 2
        color = self.P1_COLOR if self.player == 1 else self.P2_COLOR
        
        # Dessiner le jeton principal
        token = self.board_canvas.create_oval(
            x - self.TOKEN_RADIUS,
            initial_y - self.TOKEN_RADIUS,
            x + self.TOKEN_RADIUS,
            initial_y + self.TOKEN_RADIUS,
            fill=color,
            outline=""
        )
        
        # Ajouter un reflet
        highlight_radius = self.TOKEN_RADIUS * 0.5
        highlight = self.board_canvas.create_oval(
            x - self.TOKEN_RADIUS * 0.6,
            initial_y - self.TOKEN_RADIUS * 0.6,
            x - self.TOKEN_RADIUS * 0.6 + highlight_radius,
            initial_y - self.TOKEN_RADIUS * 0.6 + highlight_radius,
            fill="white",
            outline="",
            stipple="gray50"
        )
        
        # Animer la chute avec un effet simple
        self.animate_drop(token, highlight, initial_y, final_y, 0)
        
    def animate_drop(self, token, highlight, current_y, final_y, velocity):
        """Anime la chute d'un jeton avec une animation simplifiée mais fonctionnelle"""
        # Paramètres physiques
        gravity = 0.8
        bounce_damping = 0.6  # Facteur d'amortissement des rebonds
        velocity += gravity  # Augmenter la vitesse avec la gravité
        
        # Calculer la nouvelle position
        new_y = current_y + velocity
        
        # Si le jeton a atteint ou dépassé sa position finale
        if new_y >= final_y:
            # Rebond
            new_y = final_y
            velocity = -velocity * bounce_damping
            
            # Si la vitesse est très faible, arrêter l'animation
            if abs(velocity) < 1:
                self.board_canvas.delete(token)
                self.board_canvas.delete(highlight)
                self.update_board()  # Mettre à jour le plateau pour afficher le jeton final
                return
                
        # Déplacer le jeton et son reflet
        dy = new_y - current_y
        self.board_canvas.move(token, 0, dy)
        self.board_canvas.move(highlight, 0, dy)
        
        # Continuer l'animation
        self.root.after(16, lambda: self.animate_drop(token, highlight, new_y, final_y, velocity))

    def run(self):
        """Lance l'interface"""
        self.root.mainloop()

if __name__ == "__main__":
    client = Puissance4Client()
    client.run() 