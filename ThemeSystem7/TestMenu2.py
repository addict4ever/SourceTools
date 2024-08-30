import paramiko
import tkinter as tk
from tkinter import messagebox
import logging
import re
import os

# Configuration du logger pour le fichier 'lol.log'
logging.basicConfig(filename='lol.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Informations de connexion par défaut
DEFAULT_USERNAME = "lol"
DEFAULT_PASSWORD = "lol"
DEFAULT_IP = "16.16.16.16"
DEFAULT_PORT = 22
SAVE_MENU_PATH = "saved_menus"

# Fonction pour se connecter au serveur SSH et récupérer les options de menu
def fetch_menu_options(shell):
    menu_options = ""
    while True:
        try:
            # Accumuler les données pour éviter les coupures de texte
            received_data = shell.recv(4096).decode('utf-8', errors='ignore')
            if not received_data:
                raise ValueError("Connexion fermée par le serveur.")
            logging.info("Reçu du serveur: %s", repr(received_data))
            menu_options += received_data
            
            # Analyser les données accumulées pour vérifier si le menu est complet
            if "MENU PRINCIPAL" in menu_options or "Entrer <RETOUR>" in menu_options:
                break
        except Exception as e:
            logging.error("Erreur lors de la réception des données: %s", e)
            messagebox.showerror("Erreur", f"Erreur de communication: {str(e)}")
            break
    return menu_options

# Fonction pour analyser le menu et en extraire les options
def parse_menu_options(menu_text):
    # Nettoyage du texte pour une meilleure analyse
    menu_text = re.sub(r'\s+', ' ', menu_text).strip()  # Remplacer les multiples espaces par un seul et enlever les espaces en trop
    logging.info("Texte du menu après nettoyage: %s", menu_text)
    
    # Utiliser une regex améliorée pour capturer les options de menu
    options = re.findall(r"(\d+|e)\.\s+(.+?)(?=\s+\d+\.|\s+e\.|$)", menu_text, re.DOTALL)
    logging.info("Options détectées: %s", options)
    
    return options

# Fonction pour gérer la sélection d'une option dans le menu
def select_option(option, shell, root=None):
    try:
        logging.info("Envoi de la commande: %s", option)
        shell.send(option + "\n")
        submenu_options = fetch_menu_options(shell)
        
        if root:
            root.destroy()  # Fermer la fenêtre actuelle
        create_menu_gui(submenu_options, shell)
    except Exception as e:
        logging.error("Erreur lors de l'envoi de la commande: %s", e)
        messagebox.showerror("Erreur", f"Erreur lors de l'envoi de la commande: {str(e)}")

# Fonction pour sauvegarder un menu dans un fichier texte
def save_menu_to_file(menu_text):
    if not os.path.exists(SAVE_MENU_PATH):
        os.makedirs(SAVE_MENU_PATH)
    filename = os.path.join(SAVE_MENU_PATH, f"menu_{len(os.listdir(SAVE_MENU_PATH)) + 1}.txt")
    with open(filename, "w") as f:
        f.write(menu_text)
    logging.info(f"Menu sauvegardé dans {filename}")

# Fonction pour créer une GUI en fonction des options de menu
def create_menu_gui(menu_text, shell):
    options = parse_menu_options(menu_text)
    
    if options:
        root = tk.Tk()
        root.title("Menu Dynamique")
        root.configure(bg="#282c34")

        # Créer une liste pour les boutons afin de permettre la navigation au clavier
        buttons = []

        # Créer un bouton pour chaque option (verticalement)
        for number, description in options:
            description = description.strip().replace("\n", " ")  # Nettoyer la description
            
            # Déterminer la couleur du bouton
            if number == "e":  # Bouton de retour
                button_color = "#ff6347"  # Rouge pour le bouton de retour
            else:
                button_color = "#61afef"  # Bleu pour les autres options

            button = tk.Button(root, text=f"{number}. {description}",
                               command=lambda opt=number: select_option(opt, shell, root),
                               bg=button_color, fg="white", font=("Helvetica", 12, "bold"))
            button.pack(padx=10, pady=5, fill=tk.X)
            buttons.append(button)

        # Focus sur le premier bouton et gestion de la navigation au clavier
        buttons[0].focus_set()

        def on_key(event):
            current = root.focus_get()
            index = buttons.index(current)
            if event.keysym == "Up" and index > 0:
                buttons[index - 1].focus_set()
            elif event.keysym == "Down" and index < len(buttons) - 1:
                buttons[index + 1].focus_set()

        root.bind("<Up>", on_key)
        root.bind("<Down>", on_key)

        # Sauvegarder automatiquement le menu dans un fichier texte
        save_menu_to_file(menu_text)

        root.mainloop()

# Fonction principale pour se connecter et démarrer l'interface
def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=DEFAULT_IP, username=DEFAULT_USERNAME, password=DEFAULT_PASSWORD, port=DEFAULT_PORT)
        
        shell = ssh.invoke_shell()
        shell.send("\n")  # Réveiller le terminal
        logging.info("Connexion SSH établie avec le serveur %s", DEFAULT_IP)
        
        # Récupérer et afficher le menu principal
        menu_principal = fetch_menu_options(shell)
        save_menu_to_file(menu_principal)  # Sauvegarder le menu principal
        create_menu_gui(menu_principal, shell)
        
    except Exception as e:
        logging.error("Erreur de connexion: %s", e)
        messagebox.showerror("Erreur de connexion", f"Impossible de se connecter au serveur : {str(e)}")

# Exécuter le programme
if __name__ == "__main__":
    main()

