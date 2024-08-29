import paramiko
import tkinter as tk
from tkinter import messagebox
import logging
import re

# Configuration du logger
logging.basicConfig(filename='session.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Informations de connexion par défaut
DEFAULT_USERNAME = "lol"
DEFAULT_PASSWORD = "lol"
DEFAULT_IP = "12.12.12.151"
DEFAULT_PORT = 22

# Fonction pour se connecter au serveur SSH et récupérer les options de menu
def fetch_menu_options(shell):
    menu_options = ""
    while True:
        try:
            received_data = shell.recv(1024).decode('utf-8')
            if not received_data:
                raise ValueError("Connexion fermée par le serveur.")
            logging.info("Reçu du serveur: %s", received_data.strip())
            menu_options += received_data
            if re.search(r"\d+\.\s+", menu_options):  # Détecte la présence d'options numérotées
                break
        except Exception as e:
            logging.error("Erreur lors de la réception des données: %s", e)
            messagebox.showerror("Erreur", f"Erreur de communication: {str(e)}")
            break
    return menu_options

# Fonction pour analyser le menu et en extraire les options
def parse_menu_options(menu_text):
    options = re.findall(r"(\d+)\.\s+(.+?)(?=\s+\d+\.|\s*$)", menu_text, re.DOTALL)
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

# Fonction pour créer une GUI en fonction des options de menu
def create_menu_gui(menu_text, shell):
    options = parse_menu_options(menu_text)
    
    if options:
        root = tk.Tk()
        root.title("Menu Dynamique")
        root.configure(bg="#282c34")

        # Créer un bouton pour chaque option
        for number, description in options:
            button = tk.Button(root, text=f"{number}. {description.strip()}",
                               command=lambda opt=number: select_option(opt, shell, root),
                               bg="#61afef", fg="white", font=("Helvetica", 12, "bold"))
            button.pack(padx=10, pady=5, fill=tk.X)

        # Bouton de retour stylé
        button_back = tk.Button(root, text="Retour", command=lambda: select_option('e', shell, root),
                                bg="#98c379", fg="white", font=("Helvetica", 12, "bold"))
        button_back.pack(padx=10, pady=5, fill=tk.X)

        root.mainloop()

# Fonction principale pour se connecter et démarrer l'interface
def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=DEFAULT_IP, username=DEFAULT_USERNAME, password=DEFAULT_PASSWORD, port=DEFAULT_PORT)
        
        shell = ssh.invoke_shell()
        shell.send("\n")  # Réveiller le terminal
        
        # Récupérer et afficher le menu principal
        menu_principal = fetch_menu_options(shell)
        create_menu_gui(menu_principal, shell)
        
    except Exception as e:
        messagebox.showerror("Erreur de connexion", f"Impossible de se connecter au serveur : {str(e)}")

# Exécuter le programme
if __name__ == "__main__":
    main()