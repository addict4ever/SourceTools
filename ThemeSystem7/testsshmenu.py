import paramiko
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading

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

# Menus prédéfinis
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

menu_client = """
{
    "options": [
        {"text": "1. Fichier des clients", "command": "1"},
        {"text": "2. Journal des ventes", "command": "2"},
        {"text": "3. Journal caisse-recettes", "command": "3"},
        {"text": "4. Modification d'un code client", "command": "4"},
        {"text": "5. Fusion d'un code client", "command": "5"},
        {"text": "6. Table des escomptes", "command": "6"},
        {"text": "7. Exceptions", "command": "7"},
        {"text": "8. Tables des territoires", "command": "8"},
        {"text": "9. Visionnement Journal des ventes", "command": "9"},
        {"text": "10. TRANSFERT DES VENTES DATE AU J/G", "command": "10"},
        {"text": "11. TRANSFERT DES RECETTES AU J/G", "command": "11"},
        {"text": "12. Fichier des clients importation", "command": "12"},
        {"text": "13. COMMANDES DE VENTES", "command": "13"},
        {"text": "14. FACTURATION", "command": "14"},
        {"text": "15. IMPRESSION DES LISTES DE CLIENTS", "command": "15"},
        {"text": "16. IMPRESSION DES JOURNAUX", "command": "16"},
        {"text": "17. IMPRESSION DE L'AGE DES COMPTes", "command": "17"},
        {"text": "18. IMPRESSION DES ETATS DE COMPTES", "command": "18"},
        {"text": "19. IMPRESSION DES ETIQUETTES", "command": "19"},
        {"text": "20. X- IMPRESSION FAX COVER SHEET", "command": "20"},
        {"text": "21. Table des types de clients", "command": "21"},
        {"text": "22. Verification factures comptant", "command": "22"},
        {"text": "23. Gestion des groupes de clients", "command": "23"},
        {"text": "24. Fichier client ancien", "command": "24"},
        {"text": "25. Gestion des types de clients", "command": "25"},
        {"text": "26. -", "command": "26"},
        {"text": "27. FRAIS D'ADMINISTRATION", "command": "27"},
        {"text": "28. ANALYSES DES VENTES", "command": "28"}
    ]
}
"""

# Fonction pour lire en continu les logs du SSH
def read_logs(ssh_channel):
    while True:
        if ssh_channel.recv_ready():
            log = ssh_channel.recv(1024).decode('utf-8')
            log_textbox.insert(tk.END, log)
            log_textbox.see(tk.END)  # Scrolle vers le bas pour afficher le dernier log

# Interface graphique pour les menus
def send_command(command):
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode()
    if command == "2":  # Simuler le passage au menu client
        parse_and_display_menu(menu_client)
    elif output:
        parse_and_display_menu(output)
    else:
        messagebox.showinfo("Info", "Aucun menu reçu après l'exécution de la commande.")

def parse_and_display_menu(menu_data):
    try:
        menu = json.loads(menu_data)
        for widget in root.winfo_children():
            widget.destroy()  # Effacer les anciens widgets

        tk.Label(root, text="Menu SSH", font=("Arial", 16)).pack(pady=10)
        
        for option in menu["options"]:
            button = tk.Button(root, text=option["text"], command=lambda cmd=option["command"]: send_command(cmd))
            button.pack(pady=5, fill="x")
    except json.JSONDecodeError:
        messagebox.showerror("Erreur", "Erreur lors de l'analyse du menu JSON.")
        
def initial_menu():
    parse_and_display_menu(menu_principal)

# Fenêtre principale pour les menus
root = tk.Tk()
root.title("Menu SSH")

# Fenêtre pour les logs SSH
log_window = tk.Toplevel(root)
log_window.title("Logs SSH")

log_textbox = scrolledtext.ScrolledText(log_window, width=80, height=20)
log_textbox.pack()

# Démarrage du menu initial
initial_menu()

# Démarrage de la lecture des logs dans un thread séparé
channel = client.invoke_shell()
log_thread = threading.Thread(target=read_logs, args=(channel,))
log_thread.daemon = True
log_thread.start()

root.mainloop()

# Fermer la connexion SSH à la fin
client.close()