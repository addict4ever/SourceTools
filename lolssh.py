import paramiko
import tkinter as tk
from tkinter import messagebox

# Informations de connexion par défaut
DEFAULT_USERNAME = "lol"
DEFAULT_PASSWORD = "lol"
DEFAULT_IP = "12.12.12.151"
DEFAULT_PORT = 22

# Fonction pour se connecter au serveur SSH et récupérer les options de menu
def fetch_menu_options(shell):
    menu_options = ""
    while True:
        received_data = shell.recv(1024).decode('utf-8')
        menu_options += received_data
        if "MENU PRINCIPAL" in menu_options.upper():  # Vérification du menu principal
            break
    return menu_options

# Fonction pour gérer la sélection d'une option dans le menu principal
def select_main_option(option, shell):
    shell.send(option + "\n")  # Envoyer l'option sélectionnée au serveur
    submenu_options = fetch_menu_options(shell)
    create_menu_gui(submenu_options, shell)

# Fonction pour créer une GUI en fonction des options de menu
def create_menu_gui(menu_options, shell):
    if menu_options:
        root = tk.Tk()
        root.title("Menu Dynamique")

        # Analyser les options de menu
        options = menu_options.splitlines()
        for option in options:
            if option.strip():  # Ignorer les lignes vides
                # Afficher chaque option comme un bouton dans la GUI
                button = tk.Button(root, text=option, command=lambda opt=option: select_option(opt, shell))
                button.pack(padx=10, pady=5, fill=tk.X)

        root.mainloop()

# Fonction pour gérer la sélection d'une option dans un sous-menu
def select_option(option, shell):
    messagebox.showinfo("Option sélectionnée", f"Vous avez sélectionné : {option}")
    shell.send(option + "\n")  # Envoyer l'option sélectionnée au serveur
    # Ici, vous pouvez ajouter du code pour traiter les sous-menus ou les commandes finales

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
        if "MENU PRINCIPAL" in menu_principal.upper():
            messagebox.showinfo("Connexion réussie", "Le menu principal a été détecté.")
            create_menu_gui(menu_principal, shell)
        else:
            messagebox.showerror("Erreur", "Menu principal non détecté")
            ssh.close()
        
    except Exception as e:
        messagebox.showerror("Erreur de connexion", f"Impossible de se connecter au serveur : {str(e)}")

# Exécuter le programme
if __name__ == "__main__":
    main()