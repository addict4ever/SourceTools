import sys
import csv
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QLineEdit
from PyQt5.QtCore import Qt
from fpdf import FPDF
from datetime import datetime

class ConvertisseurCSV(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Configuration de la fenêtre principale
        self.setWindowTitle("Convertisseur CSV Canon, Xerox et Sharp (FR/EN)")
        self.setGeometry(100, 100, 800, 500)

        # Disposition verticale
        layout = QVBoxLayout()

        # Label d'instructions pour choisir un fichier CSV
        self.label = QLabel("Sélectionnez un fichier CSV à convertir ou éditer :", self)
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

        # Tableau pour éditer les données CSV
        self.table_widget = QTableWidget(self)
        layout.addWidget(self.table_widget)

        # Barre de recherche
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Rechercher dans les données...")
        self.search_bar.textChanged.connect(self.rechercher_donnees)
        layout.addWidget(self.search_bar)

        # Bouton pour ajouter une ligne ou une colonne
        self.btn_ajouter_ligne = QPushButton("Ajouter une ligne", self)
        self.btn_ajouter_ligne.clicked.connect(self.ajouter_ligne)
        layout.addWidget(self.btn_ajouter_ligne)

        self.btn_ajouter_colonne = QPushButton("Ajouter une colonne", self)
        self.btn_ajouter_colonne.clicked.connect(self.ajouter_colonne)
        layout.addWidget(self.btn_ajouter_colonne)

        # Bouton pour supprimer les enregistrements sélectionnés
        self.btn_supprimer_ligne = QPushButton("Supprimer les enregistrements sélectionnés", self)
        self.btn_supprimer_ligne.clicked.connect(self.supprimer_lignes)
        layout.addWidget(self.btn_supprimer_ligne)

        # Bouton pour convertir et sauvegarder
        self.btn_convertir = QPushButton("Convertir et sauvegarder", self)
        self.btn_convertir.clicked.connect(self.sauvegarder_fichier)
        self.btn_convertir.setEnabled(False)
        layout.addWidget(self.btn_convertir)

        # Bouton pour prévisualiser la sortie
        self.btn_previsualisation = QPushButton("Prévisualisation du fichier", self)
        self.btn_previsualisation.clicked.connect(self.preview_output)
        self.btn_previsualisation.setEnabled(False)
        layout.addWidget(self.btn_previsualisation)

        self.setLayout(layout)

        # Variables de fichier
        self.chemin_fichier_entrée = None
        self.chemin_fichier_sortie = None
        self.format_source = None
        self.langue_source = None
        self.donnees_csv = []

    def charger_fichier(self):
        fichier_entrée, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier CSV", "", "Fichiers CSV (*.csv)")
        if fichier_entrée:
            self.chemin_fichier_entrée = fichier_entrée
            self.label.setText(f"Fichier chargé : {fichier_entrée}")
            self.format_source, self.langue_source = self.detecter_format_et_langue(fichier_entrée)

            if self.format_source:
                self.label_format_source.setText(f"Format source détecté : {self.format_source}")
                self.label_langue_source.setText(f"Langue détectée : {self.langue_source}")
                self.combo_source.setCurrentText(self.format_source)
                self.btn_convertir.setEnabled(True)
                self.btn_previsualisation.setEnabled(True)
            else:
                reponse = QMessageBox.question(self, "Format non détecté", "Le format du fichier n'a pas pu être détecté automatiquement. Voulez-vous confirmer manuellement le format?", QMessageBox.Yes | QMessageBox.No)
                if reponse == QMessageBox.Yes:
                    self.format_source = self.combo_source.currentText()
                    self.langue_source = "Manuel"
                    self.label_format_source.setText(f"Format source sélectionné : {self.format_source}")
                    self.label_langue_source.setText(f"Langue : Inconnue (Manuel)")
                    self.btn_convertir.setEnabled(True)
                    self.btn_previsualisation.setEnabled(True)
                else:
                    QMessageBox.warning(self, "Annulé", "Opération annulée. Veuillez sélectionner un autre fichier.")
            self.charger_donnees_csv(fichier_entrée)

    def detecter_format_et_langue(self, fichier_csv):
        with open(fichier_csv, 'r', newline='', encoding='utf-8') as fichier:
            lecteur_csv = csv.reader(fichier)
            en_tetes = [col.lower() for col in next(lecteur_csv)]
            if 'display name' in en_tetes or 'nom' in en_tetes:
                langue = 'Anglais' if 'display name' in en_tetes else 'Français'
                format_source = "Xerox"
            elif 'nom' in en_tetes and 'email' in en_tetes:
                langue = 'Anglais' if 'nom' == 'name' else 'Français'
                format_source = "Canon"
            elif 'name' in en_tetes or 'mail-address' in en_tetes:
                langue = 'Français' if 'nom' in en_tetes else 'Anglais'
                format_source = "Sharp"
            else:
                format_source = None
                langue = None
            return format_source, langue

    def charger_donnees_csv(self, fichier_csv):
        with open(fichier_csv, 'r', newline='', encoding='utf-8') as fichier:
            lecteur_csv = csv.reader(fichier)
            self.donnees_csv = list(lecteur_csv)

        # Charger les données dans le tableau
        if self.donnees_csv:
            en_tetes = self.donnees_csv[0]
            self.table_widget.setColumnCount(len(en_tetes) + 1)  # Une colonne supplémentaire pour les checkbox
            self.table_widget.setRowCount(len(self.donnees_csv) - 1)
            self.table_widget.setHorizontalHeaderLabels(["Sélectionner"] + en_tetes)
            for i, ligne in enumerate(self.donnees_csv[1:]):
                checkbox = QCheckBox()
                self.table_widget.setCellWidget(i, 0, checkbox)
                for j, valeur in enumerate(ligne):
                    item = QTableWidgetItem(valeur)
                    self.table_widget.setItem(i, j + 1, item)
            self.btn_sauvegarder.setEnabled(True)
            self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def sauvegarder_fichier(self):
        fichier_sortie, _ = QFileDialog.getSaveFileName(self, "Sauvegarder fichier CSV", "", "Fichiers CSV (*.csv)")
        if fichier_sortie:
            self.chemin_fichier_sortie = fichier_sortie
            self.convertir_fichier()
        else:
            QMessageBox.warning(self, "Avertissement", "Aucun fichier de sortie sélectionné.")

    def convertir_fichier(self):
        try:
            if not self.chemin_fichier_entrée or not self.chemin_fichier_sortie:
                raise ValueError("Chemin de fichier non défini.")
            format_sortie = self.combo_sortie.currentText()

            with open(self.chemin_fichier_entrée, 'r', newline='', encoding='utf-8') as fichier_entrée:
                lecteur_csv = csv.DictReader(fichier_entrée)
                colonnes_source = self.obtenir_colonnes(self.format_source, self.langue_source)
                colonnes_sortie = self.obtenir_colonnes(format_sortie, 'Anglais')

                if not all(col.lower() in [c.lower() for c in lecteur_csv.fieldnames] for col in colonnes_source):
                    raise ValueError(f"Les colonnes du fichier {self.format_source} ne correspondent pas.")

                # Sauvegarder avec toutes les colonnes entourées de guillemets
                with open(self.chemin_fichier_sortie, 'w', newline='', encoding='utf-8') as fichier_sortie:
                    ecrivain_csv = csv.DictWriter(fichier_sortie, fieldnames=colonnes_sortie, quoting=csv.QUOTE_ALL)
                    ecrivain_csv.writeheader()

                    for ligne in lecteur_csv:
                        ligne_convertie = self.convertir_ligne(ligne, self.format_source, format_sortie)
                        ecrivain_csv.writerow(ligne_convertie)

            QMessageBox.information(self, "Succès", f"Le fichier a été converti avec succès et sauvegardé à : {self.chemin_fichier_sortie}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la conversion : {str(e)}")

    def obtenir_colonnes(self, format_type, langue):
        if format_type == "Canon":
            return [
                'objectclass', 'cn', 'cnread', 'cnshort', 'subdbid', 'mailaddress', 'dialdata', 'uri', 'url', 'path',
                'protocol', 'username', 'pwd', 'member', 'indxid', 'enablepartial', 'sub', 'faxprotocol', 'ecm',
                'txstartspeed', 'commode', 'lineselect', 'uricommode', 'uriflag', 'pwdinputflag', 'ifaxmode',
                'transsvcstr1', 'transsvcstr2', 'ifaxdirectmode', 'documenttype', 'bwpapersize', 'bwcompressiontype',
                'bwpixeltype', 'bwbitsperpixel', 'bwresolution', 'clpapersize', 'clcompressiontype', 'clpixeltype',
                'clbitsperpixel', 'clresolution', 'accesscode', 'uuid', 'cnreadlang', 'enablesfp', 'memberobjectuuid',
                'loginusername', 'logindomainname', 'usergroupname', 'personalid', 'folderidflag'
            ]
        elif format_type == "Xerox":
            return ['Display Name', 'Email Address', 'Phone Number', 'Address', 'Company', 'Fax Number', 'Department', 'Title', 'Notes', 'Location']
        elif format_type == "Sharp":
            return ['address', 'search-id', 'name', 'search-string', 'category-id', 'frequently-used',
                    'mail-address', 'fax-number', 'ifax-address', 'ftp-host', 'ftp-directory', 'ftp-username',
                    'ftp-username/@encodingMethod', 'ftp-password', 'ftp-password/@encodingMethod', 
                    'smb-directory', 'smb-username', 'smb-username/@encodingMethod', 'smb-password', 
                    'smb-password/@encodingMethod', 'desktop-host', 'desktop-port', 'desktop-directory', 
                    'desktop-username', 'desktop-username/@encodingMethod', 'desktop-password', 
                    'desktop-password/@encodingMethod']

    def convertir_ligne(self, ligne, format_source, format_sortie):
        correspondance = {
            'objectclass': ['objectclass'],
            'cn': ['name', 'display name', 'nom'],
            'mailaddress': ['email', 'mail-address'],
            'dialdata': ['phone number'],
            'username': ['ftp-username', 'smb-username', 'desktop-username'],
            'pwd': ['ftp-password', 'smb-password', 'desktop-password']
        }
        ligne_convertie = {}
        for colonne_sortie in self.obtenir_colonnes(format_sortie, 'Anglais'):
            for colonne_source in correspondance.get(colonne_sortie.lower(), []):
                if colonne_source in ligne:
                    ligne_convertie[colonne_sortie] = ligne[colonne_source]
                    break
            else:
                ligne_convertie[colonne_sortie] = ''
        return ligne_convertie

    def preview_output(self):
        # Afficher un aperçu du fichier de sortie
        try:
            format_sortie = self.combo_sortie.currentText()
            colonnes_sortie = self.obtenir_colonnes(format_sortie, 'Anglais')
            preview_text = "Aperçu du fichier de sortie:\n"
            preview_text += ", ".join(colonnes_sortie) + "\n"
            for row in self.donnees_csv[1:6]:  # Prévisualisation des 5 premières lignes
                row_convertie = self.convertir_ligne(row, self.format_source, format_sortie)
                preview_text += ", ".join(row_convertie.values()) + "\n"
            QMessageBox.information(self, "Aperçu", preview_text)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'afficher l'aperçu : {str(e)}")



def convertir_fichier(self):
    try:
        if not self.chemin_fichier_entrée or not self.chemin_fichier_sortie:
            raise ValueError("Chemin de fichier non défini.")
        format_sortie = self.combo_sortie.currentText()

        with open(self.chemin_fichier_entrée, 'r', newline='', encoding='utf-8') as fichier_entrée:
            lecteur_csv = csv.DictReader(fichier_entrée)
            colonnes_source = self.obtenir_colonnes(self.format_source, self.langue_source)
            colonnes_sortie = self.obtenir_colonnes(format_sortie, 'Anglais')

            if not all(col.lower() in [c.lower() for c in lecteur_csv.fieldnames] for col in colonnes_source):
                raise ValueError(f"Les colonnes du fichier {self.format_source} ne correspondent pas.")

            with open(self.chemin_fichier_sortie, 'w', newline='', encoding='utf-8') as fichier_sortie:
                ecrivain_csv = csv.DictWriter(fichier_sortie, fieldnames=colonnes_sortie, quoting=csv.QUOTE_MINIMAL)
                ecrivain_csv.writeheader()  # Ecrire les en-têtes sans guillemets

                # Écrire chaque ligne avec les données entre guillemets
                for ligne in lecteur_csv:
                    ligne_convertie = self.convertir_ligne(ligne, self.format_source, format_sortie)

                    # Mettre les valeurs entre guillemets
                    ligne_convertie_avec_guillemets = {k: f'"{v}"' if v else '' for k, v in ligne_convertie.items()}

                    ecrivain_csv.writerow(ligne_convertie_avec_guillemets)

        QMessageBox.information(self, "Succès", f"Le fichier a été converti avec succès et sauvegardé à : {self.chemin_fichier_sortie}")

    except Exception as e:
        QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la conversion : {str(e)}")




def convertir_ligne(self, ligne, format_source, format_sortie):
    correspondance = {
        'objectclass': ['objectclass'],
        'cn': ['name', 'display name', 'nom'],
        'mailaddress': ['email', 'mail-address'],
        'dialdata': ['phone number'],
        'username': ['ftp-username', 'smb-username', 'desktop-username'],
        'pwd': ['ftp-password', 'smb-password', 'desktop-password']
    }
    
    # Initialiser la ligne convertie avec "email" au début
    ligne_convertie = {"email": ligne.get('mailaddress', '')}
    
    # Ajouter le numéro (ici, je vais ajouter un numéro d'ordre par exemple)
    ligne_convertie["number"] = 1  # Vous pouvez implémenter un compteur ou autre logique ici

    # Ajouter les colonnes selon le format source
    for colonne_sortie in self.obtenir_colonnes(format_sortie, 'Anglais'):
        # Ignorer certaines colonnes inutiles ou vides, par exemple celles qui contiennent "xS4FiNvCE4i8EqfPNhjWg=="
        if ligne.get(colonne_sortie) == "+xS4FiNvCE4i8EqfPNhjWg==" or not ligne.get(colonne_sortie):
            continue
        for colonne_source in correspondance.get(colonne_sortie.lower(), []):
            if colonne_source in ligne:
                ligne_convertie[colonne_sortie] = ligne[colonne_source]
                break
        else:
            ligne_convertie[colonne_sortie] = ''  # Mettre une valeur vide si aucune correspondance trouvée

    return ligne_convertie

def convertir_fichier(self):
    try:
        if not self.chemin_fichier_entrée or not self.chemin_fichier_sortie:
            raise ValueError("Chemin de fichier non défini.")
        format_sortie = self.combo_sortie.currentText()

        with open(self.chemin_fichier_entrée, 'r', newline='', encoding='utf-8') as fichier_entrée:
            lecteur_csv = csv.DictReader(fichier_entrée)
            colonnes_source = self.obtenir_colonnes(self.format_source, self.langue_source)
            colonnes_sortie = self.obtenir_colonnes(format_sortie, 'Anglais')

            # Ajout manuel des nouveaux champs dans les colonnes de sortie
            colonnes_sortie.insert(0, 'number')  # Ajouter 'number' au début
            colonnes_sortie.insert(1, 'email')  # Ajouter 'email' en deuxième position

            if not all(col.lower() in [c.lower() for c in lecteur_csv.fieldnames] for col in colonnes_source):
                raise ValueError(f"Les colonnes du fichier {self.format_source} ne correspondent pas.")

            with open(self.chemin_fichier_sortie, 'w', newline='', encoding='utf-8') as fichier_sortie:
                ecrivain_csv = csv.DictWriter(fichier_sortie, fieldnames=colonnes_sortie, quoting=csv.QUOTE_MINIMAL)
                ecrivain_csv.writeheader()

                # Générer un numéro pour chaque ligne
                numero = 1

                # Écrire chaque ligne avec les données
                for ligne in lecteur_csv:
                    ligne_convertie = self.convertir_ligne(ligne, self.format_source, format_sortie)

                    # Si la colonne "number" n'existe pas ou est vide, ajouter un numéro
                    if not ligne_convertie.get('number'):
                        ligne_convertie['number'] = numero
                        numero += 1  # Incrémenter le numéro pour la prochaine ligne

                    # Ajouter un email si manquant
                    if not ligne_convertie.get('email'):
                        ligne_convertie['email'] = 'dummy@example.com'

                    ecrivain_csv.writerow(ligne_convertie)

        QMessageBox.information(self, "Succès", f"Le fichier a été converti avec succès et sauvegardé à : {self.chemin_fichier_sortie}")

    except Exception as e:
        QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la conversion : {str(e)}")


def convertir_ligne(self, ligne, format_source, format_sortie):
    correspondance = {
        'objectclass': ['objectclass'],
        'cn': ['name', 'display name', 'nom'],
        'mailaddress': ['email', 'mail-address'],
        'dialdata': ['phone number'],
        'username': ['ftp-username', 'smb-username', 'desktop-username'],
        'pwd': ['ftp-password', 'smb-password', 'desktop-password']
    }

    # Initialiser la ligne convertie avec un email et un numéro
    ligne_convertie = {
        'number': ligne.get('number', ''),  # Si le numéro existe déjà, le récupérer sinon vide
        'email': ligne.get('mailaddress', '')  # Récupérer l'email sinon vide
    }

    # Ajouter les colonnes selon le format source
    for colonne_sortie in self.obtenir_colonnes(format_sortie, 'Anglais'):
        if ligne.get(colonne_sortie) == "+xS4FiNvCE4i8EqfPNhjWg==" or not ligne.get(colonne_sortie):
            continue  # Ignorer les valeurs inutiles ou vides
        for colonne_source in correspondance.get(colonne_sortie.lower(), []):
            if colonne_source in ligne:
                ligne_convertie[colonne_sortie] = ligne[colonne_source]
                break
        else:
            ligne_convertie[colonne_sortie] = ''  # Ajouter une valeur vide si aucune correspondance trouvée

    return ligne_convertie