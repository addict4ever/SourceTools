import paramiko
import tkinter as tk

def ssh_connect(hostname, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password)
    return client

def execute_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    return stdout.read().decode('utf-8').splitlines()

def display_menu(root, client, command, is_main_menu=False):
    for widget in root.winfo_children():
        widget.destroy()  # On supprime les widgets existants pour un nouvel affichage

    # Affichage du nom et du Menu Principal
    tk.Label(root, text="Megaburo", font=("Arial", 20)).pack()
    
    if not is_main_menu:
        tk.Button(root, text="Menu Principal", command=lambda: display_menu(root, client, 'ls -1', True)).pack()

    # Récupération et affichage dynamique des options de menu
    data = execute_command(client, command)
    
    for item in data:
        button = tk.Button(root, text=item, command=lambda i=item: display_submenu(root, client, i))
        button.pack()

def display_submenu(root, client, choice):
    # Par exemple, on suppose que choisir une option mène à un autre menu basé sur un répertoire
    new_command = f'ls -1 {choice}'  # Modifier la commande pour refléter la nouvelle navigation
    display_menu(root, client, new_command)

# Connexion SSH
client = ssh_connect('hostname', 'username', 'password')

# Interface Tkinter
root = tk.Tk()
root.title("SSH Menu Dynamique")

# Affichage du menu principal
display_menu(root, client, 'ls -1', True)

root.mainloop()