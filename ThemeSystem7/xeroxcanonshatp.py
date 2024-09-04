import sys
import csv
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, QMessageBox

class ConvertisseurCSV(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Configuration de la fenêtre principale
        self.setWindowTitle("Convertisseur CSV Canon, Xerox et Sharp (FR/EN)")
        self.setGeometry(100, 100, 400, 250)

        # Disposition verticale
        layout = QVBoxLayout()

        # Label d'instructions pour choisir un fichier CSV
        self.label = QLabel("Sélectionnez un fichier CSV à convertir :", self)
        layout.addWidget(self.label)

        # Bouton pour charger le fichier d'entrée
        self.btn_charger = QPushButton("Charger fichier CSV", self)
        self.btn_charger.clicked.connect(self.charger_fichier)
        layout.addWidget(self.btn_charger)

        # Label pour montrer le format détecté et la langue détectée
        self.label_format_source = QLabel("Format source détecté : Aucun", self)
        layout.addWidget(self.label_format_source)

        self.label_langue_source = QLabel("Langue détectée : Inconnue", self)
        layout.addWidget(self.label_langue_source)

        # ComboBox pour choisir manuellement le format source si nécessaire
        self.label_format_source_manuel = QLabel("Choisissez le format source (si nécessaire) :", self)
        layout.addWidget(self.label_format_source_manuel)
        self.combo_source = QComboBox(self)
        self.combo_source.addItems(["Canon", "Xerox", "Sharp"])
        layout.addWidget(self.combo_source)

        # ComboBox pour choisir le format de sortie
        self.label_format_sortie = QLabel("Choisissez le format de sortie :", self)
        layout.addWidget(self.label_format_sortie)
        self.combo_sortie = QComboBox(self)
        self.combo_sortie.addItems(["Canon", "Xerox", "Sharp"])
        layout.addWidget(self.combo_sortie)

        # Bouton pour convertir et sauvegarder
        self.btn_convertir = QPushButton("Convertir et sauvegarder", self)
        self.btn_convertir.clicked.connect(self.sauvegarder_fichier)
        self.btn_convertir.setEnabled(False)
        layout.addWidget(self.btn_convertir)

        # Définir le layout pour la fenêtre
        self.setLayout(layout)

        # Variables de fichier
        self.chemin_fichier_entrée = None
        self.chemin_fichier_sortie = None
        self.format_source = None
        self.langue_source = None

    def charger_fichier(self):
        # Ouvrir la boîte de dialogue pour choisir le fichier CSV
        fichier_entrée, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier CSV", "", "Fichiers CSV (*.csv)")
        if fichier_entrée:
            self.chemin_fichier_entrée = fichier_entrée
            self.label.setText(f"Fichier chargé : {fichier_entrée}")
            self.format_source, self.langue_source = self.detecter_format_et_langue(fichier_entrée)

            if self.format_source:
                self.label_format_source.setText(f"Format source détecté : {self.format_source}")
                self.label_langue_source.setText(f"Langue détectée : {self.langue_source}")
                self.btn_convertir.setEnabled(True)
            else:
                # Demander à l'utilisateur de confirmer le format source si non détecté
                reponse = QMessageBox.question(self, "Format non détecté",
                                               "Le format du fichier n'a pas pu être détecté automatiquement. Voulez-vous confirmer manuellement le format?",
                                               QMessageBox.Yes | QMessageBox.No)
                if reponse == QMessageBox.Yes:
                    # Utiliser le format sélectionné dans la combo_box comme format source
                    self.format_source = self.combo_source.currentText()
                    self.langue_source = "Manuel"
                    self.label_format_source.setText(f"Format source sélectionné : {self.format_source}")
                    self.label_langue_source.setText(f"Langue : Inconnue (Manuel)")
                    self.btn_convertir.setEnabled(True)
                else:
                    QMessageBox.warning(self, "Annulé", "Opération annulée. Veuillez sélectionner un autre fichier.")

    def detecter_format_et_langue(self, fichier_csv):
        # Lire les en-têtes du fichier CSV pour détecter le format et la langue
        with open(fichier_csv, 'r', newline='', encoding='utf-8') as fichier:
            lecteur_csv = csv.reader(fichier)
            en_tetes = next(lecteur_csv)  # Lire la première ligne pour obtenir les en-têtes

            # Détection des colonnes selon le format et la langue
            if 'Display Name' in en_tetes or 'Nom' in en_tetes:
                langue = 'Anglais' if 'Display Name' in en_tetes else 'Français'
                format_source = "Xerox"
            elif 'Nom' in en_tetes and 'Email' in en_tetes:
                langue = 'Anglais' if 'Nom' == 'Name' else 'Français'
                format_source = "Canon"
            elif 'name' in en_tetes or 'mail-address' in en_tetes:
                langue = 'Français' if 'Nom' in en_tetes else 'Anglais'
                format_source = "Sharp"
            else:
                format_source = None
                langue = None

            return format_source, langue

    def sauvegarder_fichier(self):
        # Ouvrir la boîte de dialogue pour choisir où sauvegarder le fichier converti
        fichier_sortie, _ = QFileDialog.getSaveFileName(self, "Sauvegarder fichier CSV", "", "Fichiers CSV (*.csv)")
        if fichier_sortie:
            self.chemin_fichier_sortie = fichier_sortie
            self.convertir_fichier()
        else:
            # Si l'utilisateur n'a pas sélectionné de fichier, afficher un avertissement
            QMessageBox.warning(self, "Avertissement", "Aucun fichier de sortie sélectionné.")

    def convertir_fichier(self):
        try:
            # Vérifier si les chemins des fichiers sont définis
            if not self.chemin_fichier_entrée or not self.chemin_fichier_sortie:
                raise ValueError("Chemin de fichier non défini.")

            format_sortie = self.combo_sortie.currentText()

            # Lire le fichier CSV selon le format source détecté ou confirmé manuellement
            with open(self.chemin_fichier_entrée, 'r', newline='', encoding='utf-8') as fichier_entrée:
                lecteur_csv = csv.DictReader(fichier_entrée)

                colonnes_source = self.obtenir_colonnes(self.format_source, self.langue_source)
                colonnes_sortie = self.obtenir_colonnes(format_sortie, 'Anglais')  # Sortie en anglais par défaut

                # Vérifier si les colonnes du fichier source sont correctes
                if not all(col in lecteur_csv.fieldnames for col in colonnes_source):
                    raise ValueError(f"Les colonnes du fichier {self.format_source} ne correspondent pas.")

                # Écrire le fichier CSV converti
                with open(self.chemin_fichier_sortie, 'w', newline='', encoding='utf-8') as fichier_sortie:
                    ecrivain_csv = csv.DictWriter(fichier_sortie, fieldnames=colonnes_sortie)
                    ecrivain_csv.writeheader()

                    # Conversion des données
                    for ligne in lecteur_csv:
                        ligne_convertie = self.convertir_ligne(ligne, self.format_source, format_sortie)
                        ecrivain_csv.writerow(ligne_convertie)

            # Message de succès
            QMessageBox.information(self, "Succès", f"Le fichier a été converti avec succès et sauvegardé à : {self.chemin_fichier_sortie}")

        except Exception as e:
            # Gestion des erreurs
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la conversion : {str(e)}")

    def obtenir_colonnes(self, format_type, langue):
        # Définir les colonnes pour chaque format et langue
        if format_type == "Canon":
            if langue == 'Français':
                return ['Nom', 'Email', 'Téléphone', 'Adresse', 'Entreprise']
            else:
                return ['Name', 'Email', 'Phone', 'Address', 'Company']
        elif format_type == "Xerox":
            if langue == 'Français':
                return ['Nom', 'Adresse e-mail', 'Numéro de téléphone', 'Adresse', 'Entreprise']
            else:
                return ['Display Name', 'Email Address', 'Phone Number', 'Address', 'Company']
        elif format_type == "Sharp":
            # Colonnes spécifiques au format Sharp, selon le fichier fourni
            return ['address', 'search-id', 'name', 'search-string', 'category-id', 'frequently-used',
                    'mail-address', 'fax-number', 'ifax-address', 'ftp-host', 'ftp-directory', 'ftp-username',
                    'ftp-username/@encodingMethod', 'ftp-password', 'ftp-password/@encodingMethod', 
                    'smb-directory','smb-username', 'smb-username/@encodingMethod', 'smb-password', 
                    'smb-password/@encodingMethod', 'desktop-host', 'desktop-port', 
                    'desktop-directory', 'desktop-username', 'desktop-username/@encodingMethod', 
                    'desktop-password', 'desktop-password/@encodingMethod']

    def convertir_ligne(self, ligne, format_source, format_sortie):
        # Adapter les noms de colonnes selon le format source et cible
        correspondance = {
            'Nom': ['Nom', 'Display Name', 'Name'],
            'Email': ['Email', 'Email Address', 'mail-address', 'Adresse e-mail'],
            'Téléphone': ['Phone Number', 'Numéro de téléphone'],
            'Adresse': ['Adresse', 'Address', 'smb-directory'],
            'Entreprise': ['Entreprise', 'Company'],
            'FTP Username': ['ftp-username', 'ftp-username/@encodingMethod'],
            'FTP Password': ['ftp-password', 'ftp-password/@encodingMethod'],
            'SMB Username': ['smb-username', 'smb-username/@encodingMethod'],
            'SMB Password': ['smb-password', 'smb-password/@encodingMethod']
        }

        ligne_convertie = {}
        for colonne_sortie in self.obtenir_colonnes(format_sortie, 'Anglais'):  # Sortie en anglais par défaut
            for colonne_source in correspondance.get(colonne_sortie, []):
                if colonne_source in ligne:
                    ligne_convertie[colonne_sortie] = ligne[colonne_source]
                    break
            else:
                ligne_convertie[colonne_sortie] = ''

        return ligne_convertie

# Initialisation de l'application
def main():
    app = QApplication(sys.argv)
    fenetre = ConvertisseurCSV()
    fenetre.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()