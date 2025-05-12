import subprocess
import time
import os
import sys
import tkinter as tk
from tkinter import messagebox
import threading

def check_python_version():
    """Vérifie que la version de Python est compatible"""
    if sys.version_info < (3, 6):
        messagebox.showerror("Erreur", "Python 3.6 ou supérieur est requis pour exécuter ce jeu.")
        return False
    return True

def is_module_installed(module_name):
    """Vérifie si un module est installé"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def install_required_modules():
    """Installe les modules nécessaires"""
    required_modules = ["pyinstaller"]
    for module in required_modules:
        if not is_module_installed(module):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module])
                print(f"Module {module} installé avec succès.")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Erreur", f"Impossible d'installer le module {module}. Erreur: {str(e)}")
                return False
    return True

def start_server():
    """Démarre le serveur en arrière-plan"""
    try:
        # Utiliser le chemin absolu pour le script du serveur
        server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server", "server.py")
        print(f"Démarrage du serveur à partir de: {server_path}")
        
        if not os.path.exists(server_path):
            print(f"ERREUR: Le fichier serveur n'existe pas à l'emplacement: {server_path}")
            messagebox.showerror("Erreur", f"Le fichier serveur n'existe pas: {server_path}")
            return None
        
        # Démarrer le serveur
        server_process = subprocess.Popen([sys.executable, server_path], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE)
        
        print(f"Processus serveur démarré avec PID: {server_process.pid}")
        
        # Attendre que le serveur soit prêt
        time.sleep(2)
        
        # Vérifier si le processus est toujours en cours d'exécution
        if server_process.poll() is not None:
            # Le processus s'est terminé prématurément
            stdout, stderr = server_process.communicate()
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Inconnu"
            print(f"ERREUR: Le serveur s'est arrêté prématurément: {error_msg}")
            messagebox.showerror("Erreur", f"Le serveur s'est arrêté: {error_msg}")
            return None
        
        return server_process
    except Exception as e:
        print(f"ERREUR lors du démarrage du serveur: {str(e)}")
        messagebox.showerror("Erreur", f"Impossible de démarrer le serveur: {str(e)}")
        return None

def start_client():
    """Démarre un client en arrière-plan"""
    try:
        # Utiliser le chemin absolu pour le script du client
        client_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client", "client.py")
        print(f"Démarrage du client à partir de: {client_path}")
        
        if not os.path.exists(client_path):
            print(f"ERREUR: Le fichier client n'existe pas à l'emplacement: {client_path}")
            messagebox.showerror("Erreur", f"Le fichier client n'existe pas: {client_path}")
            return None
        
        # Démarrer le client
        client_process = subprocess.Popen([sys.executable, client_path],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        
        print(f"Processus client démarré avec PID: {client_process.pid}")
        
        # Vérifier si le processus est toujours en cours d'exécution après un court délai
        time.sleep(0.5)
        if client_process.poll() is not None:
            # Le processus s'est terminé prématurément
            stdout, stderr = client_process.communicate()
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Inconnu"
            print(f"ERREUR: Le client s'est arrêté prématurément: {error_msg}")
            messagebox.showerror("Erreur", f"Le client s'est arrêté: {error_msg}")
            return None
        
        return client_process
    except Exception as e:
        print(f"ERREUR lors du démarrage du client: {str(e)}")
        messagebox.showerror("Erreur", f"Impossible de démarrer le client: {str(e)}")
        return None

def create_executable():
    """Crée un fichier exécutable pour le lanceur"""
    try:
        # Vérifier que PyInstaller est installé
        if not is_module_installed("PyInstaller"):
            messagebox.showerror("Erreur", "PyInstaller n'est pas installé.")
            return False
            
        # Construire le chemin absolu pour ce script
        script_path = os.path.abspath(__file__)
        
        # Créer l'exécutable
        result = subprocess.run(
            [
                sys.executable, 
                "-m", 
                "PyInstaller", 
                "--onefile", 
                "--windowed",
                "--name", 
                "Puissance4_Launcher", 
                script_path
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            messagebox.showinfo("Succès", "L'exécutable a été créé avec succès dans le dossier 'dist'.")
            return True
        else:
            messagebox.showerror("Erreur", f"Erreur lors de la création de l'exécutable: {result.stderr}")
            return False
            
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la création de l'exécutable: {str(e)}")
        return False

class LauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Puissance 4 - Lanceur")
        self.root.geometry("400x300")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)
        
        self.server_process = None
        self.client_processes = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Titre
        title_label = tk.Label(
            self.root, 
            text="PUISSANCE 4", 
            font=("Segoe UI", 24, "bold"),
            bg="#1a1a2e",
            fg="#ecf0f1"
        )
        title_label.pack(pady=(20, 10))
        
        # Sous-titre
        subtitle_label = tk.Label(
            self.root, 
            text="Lanceur de jeu", 
            font=("Segoe UI", 14),
            bg="#1a1a2e",
            fg="#ecf0f1"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Bouton pour démarrer le serveur et les clients
        start_button = tk.Button(
            self.root,
            text="DÉMARRER LE JEU",
            command=self.start_game,
            bg="#4361ee",
            fg="#ecf0f1",
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        start_button.pack(pady=10)
        
        # Bouton pour créer un exécutable
        create_exe_button = tk.Button(
            self.root,
            text="CRÉER UN EXÉCUTABLE",
            command=self.create_exe,
            bg="#0f3460",
            fg="#ecf0f1",
            font=("Segoe UI", 12),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        create_exe_button.pack(pady=10)
        
        # Bouton pour quitter
        quit_button = tk.Button(
            self.root,
            text="QUITTER",
            command=self.quit_app,
            bg="#e74c3c",
            fg="#ecf0f1",
            font=("Segoe UI", 12),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        quit_button.pack(pady=10)
        
        # Label d'état
        self.status_label = tk.Label(
            self.root,
            text="Prêt à démarrer",
            font=("Segoe UI", 10),
            bg="#1a1a2e",
            fg="#ecf0f1"
        )
        self.status_label.pack(pady=10)
        
    def start_game(self):
        """Démarre le serveur et deux clients"""
        if self.server_process:
            messagebox.showinfo("Info", "Le jeu est déjà en cours d'exécution.")
            return
            
        # Mettre à jour le statut
        self.status_label.config(text="Démarrage du serveur...")
        self.root.update()
        
        # Démarrer le serveur
        self.server_process = start_server()
        if not self.server_process:
            self.status_label.config(text="Échec du démarrage du serveur")
            return
            
        # Mettre à jour le statut
        self.status_label.config(text="Démarrage des clients...")
        self.root.update()
        
        # Démarrer deux clients
        for _ in range(2):
            client = start_client()
            if client:
                self.client_processes.append(client)
            time.sleep(1)  # Petite pause entre les démarrages
            
        # Mettre à jour le statut
        if len(self.client_processes) == 2:
            self.status_label.config(text="Jeu démarré avec succès !")
        else:
            self.status_label.config(text=f"Jeu démarré partiellement ({len(self.client_processes)} client(s))")
    
    def create_exe(self):
        """Crée un exécutable pour le lanceur"""
        # Vérifier les prérequis
        if not check_python_version():
            return
            
        if not install_required_modules():
            return
            
        # Mettre à jour le statut
        self.status_label.config(text="Création de l'exécutable en cours...")
        self.root.update()
        
        # Créer l'exécutable dans un thread séparé pour ne pas bloquer l'interface
        threading.Thread(target=self.create_exe_thread).start()
    
    def create_exe_thread(self):
        """Thread pour créer l'exécutable"""
        success = create_executable()
        
        # Mettre à jour le statut
        if success:
            self.root.after(0, lambda: self.status_label.config(text="Exécutable créé avec succès !"))
        else:
            self.root.after(0, lambda: self.status_label.config(text="Échec de la création de l'exécutable"))
    
    def quit_app(self):
        """Quitte l'application et termine tous les processus"""
        # Terminer les clients
        for client in self.client_processes:
            try:
                client.terminate()
            except:
                pass
                
        # Terminer le serveur
        if self.server_process:
            try:
                self.server_process.terminate()
            except:
                pass
                
        # Quitter l'application
        self.root.quit()

if __name__ == "__main__":
    try:
        print("Démarrage du lanceur Puissance 4...")
        print(f"Chemin d'exécution: {os.path.abspath(__file__)}")
        print(f"Répertoire courant: {os.getcwd()}")
        print(f"Répertoire du script: {os.path.dirname(os.path.abspath(__file__))}")
        
        # Vérifier que les dossiers et fichiers requis existent
        server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server", "server.py")
        client_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client", "client.py")
        
        print(f"Vérification du serveur à: {server_path}")
        print(f"Vérification du client à: {client_path}")
        
        if not os.path.exists(server_path):
            print(f"ERREUR: Le fichier serveur n'existe pas à l'emplacement: {server_path}")
        
        if not os.path.exists(client_path):
            print(f"ERREUR: Le fichier client n'existe pas à l'emplacement: {client_path}")
            
        # Vérifier les prérequis si on est en mode exécution directe (pas en création d'exe)
        if getattr(sys, 'frozen', False):
            # On est dans un exécutable
            print("Exécution depuis un fichier exécutable")
            root = tk.Tk()
            app = LauncherGUI(root)
            root.mainloop()
        else:
            # On est en mode script
            print("Exécution depuis le script Python")
            if check_python_version():
                print("Version de Python compatible")
                root = tk.Tk()
                app = LauncherGUI(root)
                root.mainloop() 
    except Exception as e:
        print(f"ERREUR CRITIQUE LORS DU DÉMARRAGE: {str(e)}")
        # Essayer d'afficher une boîte de dialogue en dernier recours
        try:
            tk.Tk().withdraw()
            messagebox.showerror("Erreur critique", f"Erreur lors du démarrage du lanceur: {str(e)}")
        except:
            pass 