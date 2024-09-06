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
        self.setWindowTitle("Convertisseur CSV Canon, Xerox et Sharp (FR/EN)")
        self.setGeometry(100, 100, 800, 500)

        layout = QVBoxLayout()

        self.label = QLabel("Sélectionnez un fichier CSV à convertir ou éditer :", self)
        layout.addWidget(self.label)

        self.btn_charger = QPushButton("Charger fichier CSV", self)
        self.btn_charger.clicked.connect(self.charger_fichier)
        layout.addWidget(self.btn_charger)

        self.label_format_source = QLabel("Format source détecté : Aucun", self)
        layout.addWidget(self.label_format_source)

        self.label_langue_source = QLabel("Langue détectée : Inconnue", self)
        layout.addWidget(self.label_langue_source)

        self.label_format_source_manuel = QLabel("Choisissez le format source (si nécessaire) :", self)
        layout.addWidget(self.label_format_source_manuel)
        self.combo_source = QComboBox(self)
        self.combo_source.addItems(["Canon", "Xerox", "Sharp"])
        layout.addWidget(self.combo_source)

        self.label_format_sortie = QLabel("Choisissez le format de sortie :", self)
        layout.addWidget(self.label_format_sortie)
        self.combo_sortie = QComboBox(self)
        self.combo_sortie.addItems(["Canon", "Xerox", "Sharp"])
        layout.addWidget(self.combo_sortie)

        self.table_widget = QTableWidget(self)
        layout.addWidget(self.table_widget)

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Rechercher dans les données...")
        self.search_bar.textChanged.connect(self.rechercher_donnees)
        layout.addWidget(self.search_bar)

        self.btn_ajouter_ligne = QPushButton("Ajouter une ligne", self)
        self.btn_ajouter_ligne.clicked.connect(self.ajouter_ligne)
        layout.addWidget(self.btn_ajouter_ligne)

        self.btn_ajouter_colonne = QPushButton("Ajouter une colonne", self)
        self.btn_ajouter_colonne.clicked.connect(self.ajouter_colonne)
        layout.addWidget(self.btn_ajouter_colonne)

        self.btn_supprimer_ligne = QPushButton("Supprimer les enregistrements sélectionnés", self)
        self.btn_supprimer_ligne.clicked.connect(self.supprimer_lignes)
        layout.addWidget(self.btn_supprimer_ligne)

        self.btn_convertir = QPushButton("Convertir et sauvegarder", self)
        self.btn_convertir.clicked.connect(self.sauvegarder_fichier)
        self.btn_convertir.setEnabled(False)
        layout.addWidget(self.btn_convertir)

        self.btn_previsualisation = QPushButton("Prévisualisation du fichier", self)
        self.btn_previsualisation.clicked.connect(self.preview_output)
        self.btn_previsualisation.setEnabled(False)
        layout.addWidget(self.btn_previsualisation)

        self.btn_exporter_pdf = QPushButton("Exporter en PDF", self)
        self.btn_exporter_pdf.clicked.connect(self.exporter_pdf)
        layout.addWidget(self.btn_exporter_pdf)

        self.btn_sauvegarder = QPushButton("Sauvegarder les modifications", self)
        self.btn_sauvegarder.clicked.connect(self.sauvegarder_modifications)
        self.btn_sauvegarder.setEnabled(False)
        layout.addWidget(self.btn_sauvegarder)

        self.setLayout(layout)

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
            # Ajoutez d'autres correspondances ici si nécessaire
        }

        ligne_convertie = {}
        for colonne_sortie in self.obtenir_colonnes(format_sortie, 'Anglais'):
            for colonne_source in correspondance.get(colonne_sortie.lower(), []):
                if colonne_source in ligne:
                    ligne_convertie[colonne_sortie] = ligne[colonne_source]
                    break
            else:
                ligne_convertie[colonne_sortie] = '""'  # Ajouter des guillemets
        return ligne_convertie

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

                with open(self.chemin_fichier_sortie, 'w', newline='', encoding='utf-8') as fichier_sortie:
                    ecrivain_csv = csv.DictWriter(fichier_sortie, fieldnames=colonnes_sortie, quoting=csv.QUOTE_ALL)
                    ecrivain_csv.writeheader()

                    for ligne in lecteur_csv:
                        ligne_convertie = self.convertir_ligne(ligne, self.format_source, format_sortie)
                        ecrivain_csv.writerow(ligne_convertie)

            QMessageBox.information(self, "Succès", f"Le fichier a été converti avec succès et sauvegardé à : {self.chemin_fichier_sortie}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la conversion : {str(e)}")

    def preview_output(self):
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

    def exporter_pdf(self):
        fichier_pdf, _ = QFileDialog.getSaveFileName(self, "Exporter en PDF", "", "Fichiers PDF (*.pdf)")
        if fichier_pdf:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Aperçu du fichier de sortie", ln=True, align="C")
            for row in self.donnees_csv[:6]:  # Exemple : prévisualisation des premières lignes
                row_convertie = self.convertir_ligne(row, self.format_source, self.combo_sortie.currentText())
                pdf.cell(200, 10, txt=", ".join(row_convertie.values()), ln=True)
            pdf.output(fichier_pdf)
            QMessageBox.information(self, "PDF Exporté", f"Le fichier PDF a été exporté avec succès à : {fichier_pdf}")

    def sauvegarder_modifications(self):
        fichier_sortie, _ = QFileDialog.getSaveFileName(self, "Sauvegarder fichier CSV", "", "Fichiers CSV (*.csv)")
        if fichier_sortie:
            try:
                with open(fichier_sortie, 'w', newline='', encoding='utf-8') as fichier:
                    ecrivain_csv = csv.writer(fichier)

                    en_tetes = [self.table_widget.horizontalHeaderItem(col).text() for col in range(1, self.table_widget.columnCount())]
                    ecrivain_csv.writerow(en_tetes)

                    for row in range(self.table_widget.rowCount()):
                        ligne = [self.table_widget.item(row, col).text() if self.table_widget.item(row, col) else '' for col in range(1, self.table_widget.columnCount())]
                        ecrivain_csv.writerow(ligne)

                QMessageBox.information(self, "Succès", f"Les modifications ont été sauvegardées dans le fichier : {fichier_sortie}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la sauvegarde : {str(e)}")

    def rechercher_donnees(self):
        texte_recherche = self.search_bar.text().lower()
        for row in range(self.table_widget.rowCount()):
            hide_row = True
            for col in range(1, self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item and texte_recherche in item.text().lower():
                    hide_row = False
                    break
            self.table_widget.setRowHidden(row, hide_row)

# Initialisation de l'application
def main():
    app = QApplication(sys.argv)
    fenetre = ConvertisseurCSV()
    fenetre.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()