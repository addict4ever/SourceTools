import paramiko
import tkinter as tk
from tkinter import scrolledtext, messagebox
import json

# Chargement des credentials depuis le fichier JSON
def load_credentials():
    try:
        with open('credentials.json', 'r') as file:
            credentials = json.load(file)
        return credentials
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors du chargement des credentials : {str(e)}")
        return None

# Connexion SSH avec confirmation de succès ou d'échec
def ssh_connect(credentials, log_window):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(credentials['hostname'], username=credentials['username'], password=credentials['password'])
        log_window.insert(tk.END, "Connexion SSH réussie!\n")
        log_window.yview(tk.END)
        return client
    except Exception as e:
        log_window.insert(tk.END, f"Connexion SSH échouée : {str(e)}\n")
        log_window.yview(tk.END)
        return None

# Exécution d'une commande SSH avec logging
def execute_command(client, command, log_window):
    log_window.insert(tk.END, f"Commande exécutée : {command}\n")
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode('utf-8').splitlines()
    log_window.insert(tk.END, f"Résultat :\n{''.join(output)}\n")
    log_window.yview(tk.END)
    return output

# Affichage du menu principal avec options dynamiques
def display_menu(root, client, command, log_window, is_main_menu=False):
    for widget in root.winfo_children():
        widget.destroy()  # On supprime les widgets existants pour un nouvel affichage

    # Affichage du nom "Megaburo" et du bouton "Menu Principal"
    tk.Label(root, text="Megaburo", font=("Arial", 20)).pack()

    if not is_main_menu:
        tk.Button(root, text="Menu Principal", command=lambda: display_menu(root, client, 'ls -1', log_window, True)).pack()

    # Récupération et affichage dynamique des options de menu
    data = execute_command(client, command, log_window)

    for item in data:
        button = tk.Button(root, text=item, command=lambda i=item: display_submenu(root, client, i, log_window))
        button.pack()

    # Option pour entrer une commande manuellement
    tk.Label(root, text="Entrer une commande SSH :").pack()
    user_command = tk.Entry(root)
    user_command.pack()

    tk.Button(root, text="Exécuter", command=lambda: display_submenu(root, client, user_command.get(), log_window, custom_command=True)).pack()

# Gestion des sous-menus et des commandes personnalisées
def display_submenu(root, client, choice, log_window, custom_command=False):
    # Commande à exécuter selon le choix
    new_command = choice if custom_command else f'ls -1 {choice}'  
    display_menu(root, client, new_command, log_window)

# Fenêtre principale de l'application
def main():
    credentials = load_credentials()

    if credentials:
        # Initialisation de l'interface Tkinter
        root = tk.Tk()
        root.title("SSH Menu Dynamique avec Log")

        # Fenêtre de log
        log_window = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10)
        log_window.pack(fill=tk.BOTH, expand=True)

        # Connexion SSH
        client = ssh_connect(credentials, log_window)

        if client:
            # Affichage du menu principal
            display_menu(root, client, 'ls -1', log_window, True)

        root.mainloop()

# Exécution de l'application
if __name__ == "__main__":
    main()