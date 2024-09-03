import paramiko
import tkinter as tk
from tkinter import messagebox
import json
import logging

# Configuration du logging dans un fichier
logging.basicConfig(filename='lolssh.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Chargement des credentials depuis le fichier JSON
def load_credentials():
    try:
        with open('credentials.json', 'r') as file:
            credentials = json.load(file)
        return credentials
    except Exception as e:
        logging.error(f"Erreur lors du chargement des credentials : {str(e)}")
        messagebox.showerror("Erreur", f"Erreur lors du chargement des credentials : {str(e)}")
        return None

# Connexion SSH avec confirmation de succès ou d'échec
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

# Exécution d'une commande SSH avec logging
def execute_command(client, command):
    logging.info(f"Commande exécutée : {command}")
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode('utf-8').splitlines()
    logging.info(f"Résultat : {''.join(output)}")
    return output

# Affichage du menu principal avec options dynamiques
def display_menu(root, client, command, is_main_menu=False):
    for widget in root.winfo_children():
        widget.destroy()  # On supprime les widgets existants pour un nouvel affichage

    # Affichage du nom "Megaburo" et du bouton "Menu Principal"
    tk.Label(root, text="Megaburo", font=("Arial", 20)).pack()

    if not is_main_menu:
        tk.Button(root, text="Menu Principal", command=lambda: display_menu(root, client, 'ls -1', True)).pack()

    # Récupération et affichage dynamique des options de menu
    data = execute_command(client, command)

    for item in data:
        button = tk.Button(root, text=item, command=lambda i=item: display_submenu(root, client, i))
        button.pack()

    # Option pour entrer une commande manuellement
    tk.Label(root, text="Entrer une commande SSH :").pack()
    user_command = tk.Entry(root)
    user_command.pack()

    tk.Button(root, text="Exécuter", command=lambda: display_submenu(root, client, user_command.get(), custom_command=True)).pack()

# Gestion des sous-menus et des commandes personnalisées
def display_submenu(root, client, choice, custom_command=False):
    # Commande à exécuter selon le choix
    new_command = choice if custom_command else f'ls -1 {choice}'  
    display_menu(root, client, new_command)

# Fenêtre principale de l'application
def main():
    credentials = load_credentials()

    if credentials:
        # Initialisation de l'interface Tkinter
        root = tk.Tk()
        root.title("SSH Menu Dynamique")

        # Connexion SSH
        client = ssh_connect(credentials)

        if client:
            # Affichage du menu principal
            display_menu(root, client, 'ls -1', True)

        root.mainloop()

# Exécution de l'application
if __name__ == "__main__":
    main()