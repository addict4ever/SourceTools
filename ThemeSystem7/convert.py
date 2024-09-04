import sys
import csv
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox

class ConvertisseurCSV(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Configuration de la fenêtre principale
        self.setWindowTitle("Convertisseur CSV Xerox vers Sharp")
        self.setGeometry(100, 100, 400, 200)
        
        # Disposition verticale
        layout = QVBoxLayout()

        # Label d'instructions
        self.label = QLabel("Sélectionnez un fichier CSV Xerox à convertir :", self)
        layout.addWidget(self.label)

        # Bouton pour charger le fichier d'entrée
        self.btn_charger = QPushButton("Charger fichier CSV Xerox", self)
        self.btn_charger.clicked.connect(self.charger_fichier)
        layout.addWidget(self.btn_charger)

        # Bouton pour choisir l'emplacement du fichier de sortie
        self.btn_convertir = QPushButton("Convertir et sauvegarder au format Sharp", self)
        self.btn_convertir.clicked.connect(self.sauvegarder_fichier)
        self.btn_convertir.setEnabled(False)  # Désactivé jusqu'à ce qu'un fichier soit chargé
        layout.addWidget(self.btn_convertir)

        # Définir le layout pour la fenêtre
        self.setLayout(layout)

        # Variables de fichier
        self.chemin_fichier_entrée = None
        self.chemin_fichier_sortie = None

    def charger_fichier(self):
        # Ouvrir la boîte de dialogue pour choisir le fichier CSV Xerox
        fichier_entrée, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier CSV", "", "Fichiers CSV (*.csv)")
        if fichier_entrée:
            self.chemin_fichier_entrée = fichier_entrée
            self.label.setText(f"Fichier chargé : {fichier_entrée}")
            self.btn_convertir.setEnabled(True)

    def sauvegarder_fichier(self):
        # Ouvrir la boîte de dialogue pour choisir où sauvegarder le fichier converti
        fichier_sortie, _ = QFileDialog.getSaveFileName(self, "Sauvegarder fichier CSV Sharp", "", "Fichiers CSV (*.csv)")
        if fichier_sortie:
            self.chemin_fichier_sortie = fichier_sortie
            self.convertir_fichier()

    def convertir_fichier(self):
        try:
            # Vérifier si les chemins des fichiers sont définis
            if not self.chemin_fichier_entrée or not self.chemin_fichier_sortie:
                raise ValueError("Chemin de fichier non défini.")

            # Lire le fichier CSV Xerox
            with open(self.chemin_fichier_entrée, 'r', newline='', encoding='utf-8') as fichier_xerox:
                lecteur_csv = csv.DictReader(fichier_xerox)

                # Colonnes pour le fichier Sharp
                colonnes_sharp = ['Nom', 'Email', 'Numéro de téléphone', 'Adresse', 'Entreprise']

                # Écrire le fichier CSV Sharp
                with open(self.chemin_fichier_sortie, 'w', newline='', encoding='utf-8') as fichier_sharp:
                    ecrivain_csv = csv.DictWriter(fichier_sharp, fieldnames=colonnes_sharp)
                    ecrivain_csv.writeheader()

                    # Conversion des données
                    for ligne in lecteur_csv:
                        ligne_sharp = {
                            'Nom': ligne.get('Display Name', ''),
                            'Email': ligne.get('Email Address', ''),
                            'Numéro de téléphone': ligne.get('Phone Number', ''),
                            'Adresse': ligne.get('Address', ''),
                            'Entreprise': ligne.get('Company', '')
                        }
                        ecrivain_csv.writerow(ligne_sharp)

            # Message de succès
            QMessageBox.information(self, "Succès", f"Le fichier a été converti avec succès et sauvegardé à : {self.chemin_fichier_sortie}")

        except Exception as e:
            # Gestion des erreurs
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la conversion : {str(e)}")

# Initialisation de l'application
def main():
    app = QApplication(sys.argv)
    fenetre = ConvertisseurCSV()
    fenetre.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()