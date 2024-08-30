import paramiko
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, scrolledtext
import logging
import re
import json
import os
from paramiko import SCPClient

# Configuration du logger
logging.basicConfig(filename='session.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Chargement de la configuration depuis config.json
def load_config():
    try:
        with open("config.json", "r") as file:
            config = json.load(file)
            return config
    except FileNotFoundError:
        logging.error("Le fichier config.json est introuvable.")
        messagebox.showerror("Erreur", "Le fichier config.json est introuvable.")
        return None
    except json.JSONDecodeError:
        logging.error("Erreur de décodage JSON dans config.json.")
        messagebox.showerror("Erreur", "Le fichier config.json contient des erreurs de formatage.")
        return None

# Classe pour gérer l'historique de navigation
class NavigationHistory:
    def __init__(self):
        self.history = []
        self.current_index = -1

    def add_menu(self, menu_text):
        # Supprime tous les éléments après l'index actuel (cas d'une navigation en arrière)
        self.history = self.history[:self.current_index + 1]
        self.history.append(menu_text)
        self.current_index += 1

    def go_back(self):
        if self.current_index > 0:
            self.current_index -= 1
            return self.history[self.current_index]
        return None

    def go_forward(self):
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]
        return None

# Fonction pour se connecter au serveur SSH et récupérer les options de menu
def fetch_menu_options(shell):
    menu_options = ""
    while True:
        try:
            received_data = shell.recv(4096).decode('utf-8', errors='ignore')
            if not received_data:
                raise ValueError("Connexion fermée par le serveur.")
            logging.info("Reçu du serveur: %s", received_data.strip())
            menu_options += received_data
            # Détecter la fin d'un menu avec des indices comme "Entrer <RETOUR>"
            if "Entrer <RETOUR>" in menu_options or "Choisir avec les fleches" in menu_options:
                break
        except Exception as e:
            logging.error("Erreur lors de la réception des données: %s", e)
            messagebox.showerror("Erreur", f"Erreur de communication: {str(e)}")
            break
    return menu_options

# Fonction pour analyser le menu et en extraire les options
def parse_menu_options(menu_text):
    options = re.findall(r"(\d+)\.\s+(.+?)(?=\s+\d+\.\s|$)", menu_text, re.DOTALL)
    return options

# Fonction pour gérer la sélection d'une option dans le menu
def select_option(option, shell, root=None, history=None):
    try:
        logging.info("Envoi de la commande: %s", option)
        shell.send(option + "\n")
        submenu_options = fetch_menu_options(shell)
        if history:
            history.add_menu(submenu_options)
        if root:
            root.destroy()  # Fermer la fenêtre actuelle
        create_menu_gui(submenu_options, shell, history)
    except Exception as e:
        logging.error("Erreur lors de l'envoi de la commande: %s", e)
        messagebox.showerror("Erreur", f"Erreur lors de l'envoi de la commande: {str(e)}")

# Fonction pour créer une GUI en fonction des options de menu
def create_menu_gui(menu_text, shell, history=None):
    options = parse_menu_options(menu_text)

    if options:
        root = tk.Tk()
        root.title("Menu Dynamique")
        root.configure(bg="#282c34")

        # Ajouter des boutons pour la navigation dans l'historique
        if history:
            nav_frame = tk.Frame(root, bg="#282c34")
            nav_frame.pack(fill=tk.X, pady=5)

            back_button = tk.Button(nav_frame, text="◀ Retour", command=lambda: go_back(history, shell, root))
            back_button.pack(side=tk.LEFT, padx=5)

            forward_button = tk.Button(nav_frame, text="Suivant ▶", command=lambda: go_forward(history, shell, root))
            forward_button.pack(side=tk.LEFT, padx=5)

        # Créer un champ de recherche pour filtrer les options
        search_var = tk.StringVar()
        search_var.trace("w", lambda name, index, mode, sv=search_var: filter_options(sv, options, button_frame, shell, root))
        search_entry = tk.Entry(root, textvariable=search_var, font=("Helvetica", 12))
        search_entry.pack(padx=10, pady=5, fill=tk.X)

        # Conteneur pour les boutons d'options
        button_frame = tk.Frame(root, bg="#282c34")
        button_frame.pack(fill=tk.BOTH, expand=True)

        # Créer un bouton pour chaque option
        for number, description in options:
            description = description.strip().replace("\n", " ")
            button = tk.Button(button_frame, text=f"{number}. {description}",
                               command=lambda opt=number: select_option(opt, shell, root, history),
                               bg="#61afef", fg="white", font=("Helvetica", 12, "bold"))
            button.pack(padx=10, pady=5, fill=tk.X)

        # Bouton de retour stylé
        button_back = tk.Button(root, text="Retour", command=lambda: select_option('e', shell, root, history),
                                bg="#98c379", fg="white", font=("Helvetica", 12, "bold"))
        button_back.pack(padx=10, pady=5, fill=tk.X)

        # Bouton pour afficher les logs
        button_logs = tk.Button(root, text="Afficher les Logs", command=show_logs, bg="#e06c75", fg="white", font=("Helvetica", 12, "bold"))
        button_logs.pack(padx=10, pady=5, fill=tk.X)

        # Bouton pour l'édition offline des menus
        button_edit_offline = tk.Button(root, text="Édition Offline", command=edit_menu_offline, bg="#c678dd", fg="white", font=("Helvetica", 12, "bold"))
        button_edit_offline.pack(padx=10, pady=5, fill=tk.X)

        # Bouton pour télécharger un fichier via SCP
        button_scp_download = tk.Button(root, text="Télécharger Fichier", command=lambda: scp_download(shell), bg="#56b6c2", fg="white", font=("Helvetica", 12, "bold"))
        button_scp_download.pack(padx=10, pady=5, fill=tk.X)

        # Bouton pour uploader un fichier via SCP
        button_scp_upload = tk.Button(root, text="Uploader Fichier", command=lambda: scp_upload(shell), bg="#56b6c2", fg="white", font=("Helvetica", 12, "bold"))
        button_scp_upload.pack(padx=10, pady=5, fill=tk.X)

        root.mainloop()

def filter_options(search_var, options, button_frame, shell, root):
    search_term = search_var.get().lower()
    for widget in button_frame.winfo_children():
        widget.destroy()  # Clear previous buttons

    for number, description in options:
        if search_term in description.lower():
            button = tk.Button(button_frame, text=f"{number}. {description}",
                               command=lambda opt=number: select_option(opt, shell, root),
                               bg="#61afef", fg="white", font=("Helvetica", 12, "bold"))
            button.pack(padx=10, pady=5, fill=tk.X)

def go_back(history, shell, root):
    previous_menu = history.go_back()
    if previous_menu:
        root.destroy()
        create_menu_gui(previous_menu, shell, history)

def go_forward(history, shell, root):
    next_menu = history.go_forward()
    if next_menu:
        root.destroy()
        create_menu_gui(next_menu, shell, history)

def show_logs():
    log_window = tk.Toplevel()
    log_window.title("Logs")
    log_text = scrolledtext.ScrolledText(log_window, width=100, height=30)
    log_text.pack()

    try:
        with open("session.log", "r") as log_file:
            logs = log_file.read()
        log_text.insert(tk.END, logs)
    except Exception as e:
        logging.error(f"Erreur lors du chargement des logs: {e}")
        log_text.insert(tk.END, "Erreur lors du chargement des logs.")

# Fonction pour éditer les menus offline
def edit_menu_offline():
    edit_window = tk.Toplevel()
    edit_window.title("Édition Offline")
    edit_frame = tk.Frame(edit_window)
    edit_frame.pack(fill=tk.BOTH, expand=True)

    # Sélectionner un menu JSON existant
    def load_menu_json():
        menu_file = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if menu_file:
            with open(menu_file, "r") as file:
                menu_data = json.load(file)
                display_menu_editor(menu_data, menu_file)

    # Afficher l'éditeur de menus
    def display_menu_editor(menu_data, menu_file):
        for widget in edit_frame.winfo_children():
            widget.destroy()  # Clear previous widgets

        # Afficher les options actuelles
        for i, option in enumerate(menu_data.get("options", [])):
            option_frame = tk.Frame(edit_frame)
            option_frame.pack(fill=tk.X, pady=5)

            tk.Label(option_frame, text=f"Option {i + 1}:").pack(side=tk.LEFT)
            text_entry = tk.Entry(option_frame)
            text_entry.insert(0, option.get("text", ""))
            text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            command_entry = tk.Entry(option_frame)
            command_entry.insert(0, option.get("command", ""))
            command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            save_button = tk.Button(option_frame, text="Save", command=lambda idx=i, t=text_entry, c=command_entry: save_option(menu_data, idx, t, c, menu_file))
            save_button.pack(side=tk.RIGHT, padx=5)

    def save_option(menu_data, index, text_entry, command_entry, menu_file):
        menu_data["options"][index]["text"] = text_entry.get()
        menu_data["options"][index]["command"] = command_entry.get()

        with open(menu_file, "w") as file:
            json.dump(menu_data, file, indent=4)

        logging.info(f"Option {index + 1} mise à jour dans {menu_file}")
        messagebox.showinfo("Sauvegarde", f"Option {index + 1} mise à jour avec succès.")

    load_button = tk.Button(edit_window, text="Charger Menu JSON", command=load_menu_json)
    load_button.pack(pady=10)

# Fonction de téléchargement de fichier via SCP
def scp_download(shell):
    try:
        scp = SCPClient(shell.get_transport())
        remote_file = simpledialog.askstring("Téléchargement SCP", "Entrez le chemin complet du fichier à télécharger depuis le serveur :")
        local_path = filedialog.askdirectory(title="Sélectionnez un dossier pour enregistrer le fichier téléchargé")

        if remote_file and local_path:
            scp.get(remote_file, local_path)
            logging.info(f"Fichier téléchargé : {remote_file} vers {local_path}")
            messagebox.showinfo("Téléchargement SCP", f"Fichier téléchargé : {remote_file} vers {local_path}")
        scp.close()
    except Exception as e:
        logging.error(f"Erreur lors du téléchargement SCP : {e}")
        messagebox.showerror("Erreur", f"Erreur lors du téléchargement SCP : {str(e)}")

# Fonction d'upload de fichier via SCP
def scp_upload(shell):
    try:
        scp = SCPClient(shell.get_transport())
        local_file = filedialog.askopenfilename(title="Sélectionnez un fichier à uploader vers le serveur")
        remote_path = simpledialog.askstring("Upload SCP", "Entrez le chemin complet où le fichier doit être uploadé sur le serveur :")

        if local_file and remote_path:
            scp.put(local_file, remote_path)
            logging.info(f"Fichier uploadé : {local_file} vers {remote_path}")
            messagebox.showinfo("Upload SCP", f"Fichier uploadé : {local_file} vers {remote_path}")
        scp.close()
    except Exception as e:
        logging.error(f"Erreur lors de l'upload SCP : {e}")
        messagebox.showerror("Erreur", f"Erreur lors de l'upload SCP : {str(e)}")

# Fonction principale pour se connecter et démarrer l'interface
def main():
    config = load_config()
    if not config:
        return

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=config["hostname"],
            username=config["username"],
            password=config["password"],
            port=config["port"]
        )

        shell = ssh.invoke_shell()
        shell.send("\n")  # Réveiller le terminal
        logging.info("Connexion SSH établie avec le serveur %s", config["hostname"])

        history = NavigationHistory()

        # Récupérer et afficher le menu principal
        menu_principal = fetch_menu_options(shell)
        history.add_menu(menu_principal)
        create_menu_gui(menu_principal, shell, history)

    except Exception as e:
        logging.error("Erreur de connexion: %s", e)
        messagebox.showerror("Erreur de connexion", f"Impossible de se connecter au serveur : {str(e)}")

# Exécuter le programme
if __name__ == "__main__":
    main()
