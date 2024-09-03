import paramiko
import tkinter as tk
from tkinter import messagebox
import re
import json
import threading
import logging

# Configuration du logging dans des fichiers
logging.basicConfig(filename='lolssh.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

menu_logger = logging.getLogger('menu_logger')
menu_handler = logging.FileHandler('logmenu.log')
menu_formatter = logging.Formatter('%(asctime)s - %(message)s')
menu_handler.setFormatter(menu_formatter)
menu_logger.addHandler(menu_handler)
menu_logger.setLevel(logging.INFO)

# Charger les credentials depuis un fichier JSON
def load_credentials():
    try:
        with open('config.json', 'r') as file:
            credentials = json.load(file)
        return credentials
    except Exception as e:
        logging.error(f"Erreur lors du chargement des credentials : {str(e)}")
        messagebox.showerror("Erreur", f"Erreur lors du chargement des credentials : {str(e)}")
        return None

# Connexion SSH
def ssh_connect(credentials):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(credentials['hostname'], username=credentials['username'], password=credentials['password'])
        logging.info("Connexion SSH réussie!")
        return client
    except Exception as e:
        logging.error(f"Connexion SSH échouée : {str(e)}")
        messagebox.showerror("Erreur", f"Connexion SSH échouée : {str(e)}")
        return None

# Lire le flux SSH de manière continue
def read_ssh_channel(channel, callback):
    output = ""
    while True:
        if channel.recv_ready():
            received_data = channel.recv(1024).decode('utf-8')
            logging.info(f"Reçu du serveur : {received_data}")
            output += received_data
            callback(output)
            output = ""  # Réinitialiser la sortie après chaque traitement
        else:
            continue

# Fonction pour nettoyer les séquences d'échappement ANSI et autres caractères de contrôle
def clean_output(output):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    clean_text = ansi_escape.sub('', output)
    return clean_text.strip()

# Fonction pour analyser les menus envoyés par le terminal serveur
def parse_menu_output(output):
    clean_text = clean_output(output)
    
    # Rechercher les options de menu sous la forme de numéros suivis de texte.
    # Le regex suivant cherche les numéros suivis d'un texte, même si les options sont collées.
    menu_pattern = r"(\d+)\.\s+([^\d]+)"
    menu_options = re.findall(menu_pattern, clean_text)
    
    # Log menu options
    if menu_options:
        menu_logger.info("Menu détecté:")
        for num, text in menu_options:
            menu_logger.info(f"Option {num}: {text.strip()}")
    
    return {int(num): text.strip() for num, text in menu_options}

# Fonction pour détecter le début du menu après le message d'accueil
def detect_menu_start(output):
    # Supposons que le menu commence après "MENU PRINCIPAL" ou similaire
    start_pattern = r"MENU PRINCIPAL"
    match = re.search(start_pattern, output, re.IGNORECASE)
    if match:
        # Tout ce qui vient après ce point est considéré comme le menu
        menu_output = output[match.end():]
        return menu_output
    return None

# Générer les boutons de menu dynamiquement
def display_menu(root, menu_output):
    # Effacer les widgets existants
    for widget in root.winfo_children():
        widget.destroy()

    # Titre et sous-titre du menu
    tk.Label(root, text="Megaburo Inc.", font=("Arial", 20)).pack(pady=10)
    tk.Label(root, text="Menu Principal", font=("Arial", 16)).pack(pady=5)

    # Analyser les options de menu
    menu_options = parse_menu_output(menu_output)

    # Générer un bouton pour chaque option détectée
    if not menu_options:
        tk.Label(root, text="Aucune option de menu trouvée.", font=("Arial", 14)).pack(pady=5)
    else:
        for num, option in menu_options.items():
            # Créer un bouton pour chaque option de menu
            button = tk.Button(root, text=f"{num}. {option}", command=lambda n=num: send_command_to_server(n))
            button.pack(fill=tk.X, padx=10, pady=5)

    # Bouton pour quitter l'application
    tk.Button(root, text="Quitter", command=root.quit).pack(fill=tk.X, padx=10, pady=5)

# Envoyer la commande sélectionnée au serveur
def send_command_to_server(option_number):
    command = str(option_number) + '\n'  # Envoyer le numéro de l'option sélectionnée
    logging.info(f"Envoyé au serveur : {command}")
    channel.send(command)

# Fonction de rappel pour mettre à jour le GUI avec les nouvelles options de menu
def menu_callback(output):
    menu_output = detect_menu_start(output)
    if menu_output:
        display_menu(root, menu_output)
    else:
        # Mise à jour pour gérer les nouvelles options de menu
        display_menu(root, output)

# Fenêtre principale de l'application
def main():
    global root, channel

    credentials = load_credentials()

    if credentials:
        root = tk.Tk()
        root.title("SSH Menu Dynamique")

        client = ssh_connect(credentials)

        if client:
            channel = client.invoke_shell()

            # Lancer un thread pour lire le flux SSH en continu
            thread = threading.Thread(target=read_ssh_channel, args=(channel, menu_callback))
            thread.daemon = True  # Permettre la fermeture propre du programme
            thread.start()

            root.mainloop()

if __name__ == "__main__":
    main()