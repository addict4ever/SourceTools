import paramiko
import tkinter as tk
from tkinter import messagebox
import logging

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
            if any(keyword in menu_options.upper() for keyword in ["MENU PRINCIPAL", "LES CLIENTS", "COMMANDES DE VENTES"]):
                break
        except Exception as e:
            logging.error("Erreur lors de la réception des données: %s", e)
            messagebox.showerror("Erreur", f"Erreur de communication: {str(e)}")
            break
    return menu_options

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

# Classe pour afficher des tooltips
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="yellow", relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

# Fonction pour créer une GUI en fonction des options de menu
def create_menu_gui(menu_options, shell):
    if menu_options:
        root = tk.Tk()
        root.title("Menu Dynamique")
        root.configure(bg="#282c34")

        # Analyser les options de menu
        options = menu_options.splitlines()
        for option in options:
            option = option.strip()
            if option and (option[0].isdigit() or option[0].isalpha()):
                # Créer un bouton pour chaque option
                button = tk.Button(root, text=option, command=lambda opt=option.split()[0]: select_option(opt, shell, root),
                                   bg="#61afef", fg="white", font=("Helvetica", 12, "bold"))
                button.pack(padx=10, pady=5, fill=tk.X)
                # Ajouter un tooltip avec des détails supplémentaires
                ToolTip(button, f"Description de l'option {option}")

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
        if "MENU PRINCIPAL" in menu_principal.upper():
            create_menu_gui(menu_principal, shell)
        else:
            messagebox.showerror("Erreur", "Menu principal non détecté")
            ssh.close()
        
    except Exception as e:
        messagebox.showerror("Erreur de connexion", f"Impossible de se connecter au serveur : {str(e)}")

# Exécuter le programme
if __name__ == "__main__":
    main()