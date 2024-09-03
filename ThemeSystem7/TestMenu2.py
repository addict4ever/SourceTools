import paramiko
import tkinter as tk
from tkinter import messagebox
import re
import json
import logging

# Configuration du logging dans un fichier
logging.basicConfig(filename='lolssh.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Charger les credentials depuis un fichier JSON
def load_credentials():
    try:
        with open('credentials.json', 'r') as file:
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

# Exécuter une commande SSH et capturer la sortie
def execute_command(client, command):
    channel = client.invoke_shell()
    channel.send(command + '\n')
    
    output = ''
    while not channel.recv_ready():
        pass
    
    while channel.recv_ready():
        output += channel.recv(1024).decode('utf-8')
    
    logging.info(f"Commande exécutée : {command}\nRésultat : {output}")
    return output

# Fonction pour analyser les menus envoyés par le terminal serveur
def parse_menu_output(output):
    # Rechercher les options de menu sous la forme de numéros suivis de texte
    menu_pattern = r"^\s*(\d+)\.\s+(.*)$"
    menu_options = re.findall(menu_pattern, output, re.MULTILINE)
    return {int(num): text for num, text in menu_options}

# Générer les boutons de menu dynamiquement
def display_menu(root, client, output):
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text="Megaburo Inc.", font=("Arial", 20)).pack()
    tk.Label(root, text="Menu Principal", font=("Arial", 16)).pack()

    menu_options = parse_menu_output(output)

    if not menu_options:
        tk.Label(root, text="Aucune option de menu trouvée.", font=("Arial", 14)).pack()
    else:
        for num, option in menu_options.items():
            button = tk.Button(root, text=option, command=lambda n=num: select_menu_option(root, client, n))
            button.pack(fill=tk.X)

    tk.Button(root, text="Quitter", command=root.quit).pack(fill=tk.X)

# Sélectionner une option de menu
def select_menu_option(root, client, option_number):
    command = str(option_number) + '\n'  # Envoyer le numéro de l'option sélectionnée
    output = execute_command(client, command)
    display_menu(root, client, output)  # Afficher le nouveau menu reçu

# Fenêtre principale de l'application
def main():
    credentials = load_credentials()

    if credentials:
        root = tk.Tk()
        root.title("SSH Menu Dynamique")

        client = ssh_connect(credentials)

        if client:
            # Capturer le flux en temps réel pour récupérer les menus après connexion
            output = execute_command(client, '')  # Capturer le premier menu après connexion
            display_menu(root, client, output)

        root.mainloop()

if __name__ == "__main__":
    main()