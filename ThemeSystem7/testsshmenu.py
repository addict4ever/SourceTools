import paramiko
import json
import tkinter as tk
from tkinter import messagebox

# Charger la configuration depuis config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

ip_address = config.get('ip_address')
username = config.get('username')
password = config.get('password')
port = config.get('port', 22)  # Le port 22 est utilisé par défaut si non spécifié

# Connexion SSH
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(ip_address, port=port, username=username, password=password)

# Interface graphique
root = tk.Tk()
root.title("Menu SSH")

def send_command(command):
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode()
    if output:
        parse_and_display_menu(output)
    else:
        messagebox.showinfo("Info", "Aucun menu reçu après l'exécution de la commande.")

def parse_and_display_menu(menu_data):
    try:
        menu = json.loads(menu_data)
        for widget in root.winfo_children():
            widget.destroy()  # Effacer les anciens widgets

        tk.Label(root, text="Menu Principal", font=("Arial", 16)).pack(pady=10)
        
        for option in menu["options"]:
            button = tk.Button(root, text=option["text"], command=lambda cmd=option["command"]: send_command(cmd))
            button.pack(pady=5, fill="x")
    except json.JSONDecodeError:
        messagebox.showerror("Erreur", "Erreur lors de l'analyse du menu JSON.")
        
def initial_menu():
    # Simuler la réception du menu principal initial
    menu_principal = """
    {
        "options": [
            {"text": "1. LE GRAND LIVRE", "command": "1"},
            {"text": "2. LES CLIENTS", "command": "2"},
            {"text": "3. LES FOURNISSEURS", "command": "3"},
            {"text": "4. LES STOCKS", "command": "4"},
            {"text": "5. LES SALAIRES", "command": "5"},
            {"text": "6. LE SYSTEME", "command": "6"},
            {"text": "7. LES UTILITAIRES", "command": "7"},
            {"text": "8. MESSAGERIE", "command": "8"},
            {"text": "9. LE SERVICE", "command": "9"},
            {"text": "10. CENTRE DE CONTACTS", "command": "10"},
            {"text": "11. MENU SPECIAL", "command": "11"},
            {"text": "12. -", "command": "12"},
            {"text": "13. -", "command": "13"},
            {"text": "14. Verification des LOCK", "command": "14"}
        ]
    }
    """
    parse_and_display_menu(menu_principal)

# Afficher le menu principal initial
initial_menu()

root.mainloop()

# Fermer la connexion SSH à la fin
client.close()