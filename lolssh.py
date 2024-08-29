import tkinter as tk
from tkinter import messagebox, simpledialog
import paramiko

# Informations par défaut
DEFAULT_USERNAME = "lol"
DEFAULT_PASSWORD = "lol"
DEFAULT_IP = "12.12.12.151"
DEFAULT_PORT = 22

# Fonction pour la connexion SSH (pour plus tard)
def connect_ssh(host=DEFAULT_IP, port=DEFAULT_PORT, username=DEFAULT_USERNAME, password=DEFAULT_PASSWORD):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, username=username, password=password, port=port)
        messagebox.showinfo("Connexion", f"Connecté à {host}")
        ssh.close()
    except Exception as e:
        messagebox.showerror("Connexion échouée", f"Échec de la connexion à {host}\n{str(e)}")

# Fonction pour vérifier l'authentification
def check_login():
    username = entry_username.get()
    password = entry_password.get()

    if username == DEFAULT_USERNAME and password == DEFAULT_PASSWORD:
        messagebox.showinfo("Connexion réussie", "Bienvenue dans le système")
        login_window.destroy()  # Fermer la fenêtre de connexion
        open_main_menu()  # Ouvrir le menu principal
    else:
        messagebox.showerror("Erreur de connexion", "Nom d'utilisateur ou mot de passe incorrect")

# Menu principal après authentification
def open_main_menu():
    root = tk.Tk()
    root.title("Menu Principal")

    # Liste des options du menu
    menu_options = [
        ("Grand Livre", lambda: messagebox.showinfo("Grand Livre", "Ouverture du Grand Livre")),
        ("Clients", lambda: messagebox.showinfo("Clients", "Ouverture du menu Clients")),
        ("Fournisseurs", lambda: messagebox.showinfo("Fournisseurs", "Ouverture du menu Fournisseurs")),
        ("Stocks", lambda: messagebox.showinfo("Stocks", "Ouverture du menu Stocks")),
        ("Salaires", lambda: messagebox.showinfo("Salaires", "Ouverture du menu Salaires")),
        ("Système", lambda: messagebox.showinfo("Système", "Ouverture du menu Système")),
        ("Utilitaires", lambda: messagebox.showinfo("Utilitaires", "Ouverture du menu Utilitaires")),
        ("Messagerie", lambda: messagebox.showinfo("Messagerie", "Ouverture du menu Messagerie")),
        ("Service", lambda: messagebox.showinfo("Service", "Ouverture du menu Service")),
        ("Centre de Contacts", lambda: messagebox.showinfo("Centre de Contacts", "Ouverture du Centre de Contacts")),
        ("Menu Spécial", lambda: messagebox.showinfo("Menu Spécial", "Ouverture du Menu Spécial"))
    ]

    # Création des boutons pour chaque option
    for option_text, option_command in menu_options:
        button = tk.Button(root, text=option_text, command=option_command, width=30)
        button.pack(pady=5)

    root.mainloop()

# Fenêtre d'authentification
login_window = tk.Tk()
login_window.title("Authentification")

# Étiquette et champ pour le nom d'utilisateur
label_username = tk.Label(login_window, text="Nom d'utilisateur:")
label_username.pack(pady=5)
entry_username = tk.Entry(login_window, width=30)
entry_username.pack(pady=5)
entry_username.insert(0, DEFAULT_USERNAME)  # Valeur par défaut

# Étiquette et champ pour le mot de passe
label_password = tk.Label(login_window, text="Mot de passe:")
label_password.pack(pady=5)
entry_password = tk.Entry(login_window, show="*", width=30)
entry_password.pack(pady=5)
entry_password.insert(0, DEFAULT_PASSWORD)  # Valeur par défaut

# Bouton de connexion
button_login = tk.Button(login_window, text="Se connecter", command=check_login)
button_login.pack(pady=20)

login_window.mainloop()