import tkinter as tk
from tkinter import messagebox, scrolledtext
import socket
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessRequest, AccessAccept, AccessReject
import pyrad.packet
import logging

# Initialisation du logging pour les tentatives d'authentification
logging.basicConfig(filename="radius_auth.log", level=logging.INFO)

# Fonction pour valider une adresse IP/Hostname
def is_valid_ip_or_hostname(address):
    try:
        socket.getaddrinfo(address, None)
        return True
    except socket.gaierror:
        return False

# Fonction pour tester le serveur RADIUS avec gestion des erreurs
def test_radius_auth():
    username = entry_username.get()
    password = entry_password.get()
    radius_server = entry_server.get()
    radius_secret = entry_secret.get()
    radius_port = int(entry_port.get())
    timeout = int(entry_timeout.get())
    
    if not is_valid_ip_or_hostname(radius_server):
        messagebox.showerror("Erreur", "Adresse IP ou hostname invalide.")
        return
    
    try:
        # Résolution DNS pour afficher l'adresse IP
        resolved_ip = socket.gethostbyname(radius_server)
        text_logs.insert(tk.END, f"IP résolue pour le serveur {radius_server}: {resolved_ip}\n")

        # Configuration du client RADIUS avec gestion du timeout
        client = Client(server=radius_server, secret=bytes(radius_secret, 'utf-8'), dict=Dictionary("dictionary"))
        client.authport = radius_port
        client.timeout = timeout

        # Création de la requête d'authentification
        req = client.CreateAuthPacket(code=AccessRequest, User_Name=username)
        req["User-Password"] = req.PwCrypt(password)

        # Option de méthode d'authentification (PAP par défaut)
        auth_method = auth_method_var.get()
        if auth_method == "MS-CHAPv2":
            # Ajouter d'autres options de cryptage si nécessaire
            req["CHAP-Password"] = req.PwCrypt(password)

        # Envoi de la requête avec tentatives multiples
        attempts = int(entry_attempts.get())
        for attempt in range(1, attempts + 1):
            text_logs.insert(tk.END, f"Tentative {attempt}/{attempts}...\n")
            response = client.SendPacket(req)

            # Analyse de la réponse
            if response.code == AccessAccept:
                text_logs.insert(tk.END, "Authentification réussie !\n")
                messagebox.showinfo("Succès", "Authentification réussie !")
                logging.info(f"Authentification réussie pour {username} sur {radius_server}")
                return
            elif response.code == AccessReject:
                text_logs.insert(tk.END, "Authentification refusée.\n")
                messagebox.showerror("Erreur", "Authentification refusée.")
                logging.info(f"Authentification refusée pour {username} sur {radius_server}")
            else:
                text_logs.insert(tk.END, "Réponse inattendue du serveur RADIUS.\n")
                messagebox.showwarning("Avertissement", "Réponse inattendue du serveur RADIUS.")
        
    except Exception as e:
        if debug_mode.get():
            messagebox.showerror("Erreur", f"Une erreur s'est produite : {str(e)}")
        text_logs.insert(tk.END, f"Erreur : {str(e)}\n")
        logging.error(f"Erreur lors de l'authentification pour {username} : {str(e)}")

# Création de l'interface graphique
root = tk.Tk()
root.title("Test Authentification RADIUS")

# Champ pour le serveur RADIUS
tk.Label(root, text="Serveur RADIUS (IP/Hostname) :").grid(row=0, column=0)
entry_server = tk.Entry(root)
entry_server.grid(row=0, column=1)

# Champ pour le secret partagé du serveur RADIUS
tk.Label(root, text="Secret RADIUS :").grid(row=1, column=0)
entry_secret = tk.Entry(root, show='*')
entry_secret.grid(row=1, column=1)

# Champ pour le port du serveur RADIUS
tk.Label(root, text="Port RADIUS :").grid(row=2, column=0)
entry_port = tk.Entry(root)
entry_port.grid(row=2, column=1)

# Champ pour le nom d'utilisateur
tk.Label(root, text="Nom d'utilisateur :").grid(row=3, column=0)
entry_username = tk.Entry(root)
entry_username.grid(row=3, column=1)

# Champ pour le mot de passe
tk.Label(root, text="Mot de passe :").grid(row=4, column=0)
entry_password = tk.Entry(root, show='*')
entry_password.grid(row=4, column=1)

# Champ pour le timeout
tk.Label(root, text="Timeout (secondes) :").grid(row=5, column=0)
entry_timeout = tk.Entry(root)
entry_timeout.insert(0, "5")
entry_timeout.grid(row=5, column=1)

# Champ pour le nombre de tentatives
tk.Label(root, text="Nombre de tentatives :").grid(row=6, column=0)
entry_attempts = tk.Entry(root)
entry_attempts.insert(0, "1")
entry_attempts.grid(row=6, column=1)

# Méthode d'authentification
tk.Label(root, text="Méthode d'authentification :").grid(row=7, column=0)
auth_method_var = tk.StringVar(value="PAP")
tk.OptionMenu(root, auth_method_var, "PAP", "MS-CHAPv2").grid(row=7, column=1)

# Zone pour afficher les logs
tk.Label(root, text="Logs :").grid(row=8, column=0)
text_logs = scrolledtext.ScrolledText(root, width=40, height=10)
text_logs.grid(row=8, column=1)

# Mode débogage
debug_mode = tk.BooleanVar()
tk.Checkbutton(root, text="Activer le mode débogage", variable=debug_mode).grid(row=9, column=0)

# Bouton pour tester l'authentification
tk.Button(root, text="Tester", command=test_radius_auth).grid(row=10, column=1)

# Lancement de l'application GUI
root.mainloop()
