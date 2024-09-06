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

        # Bouton pour exporter en PDF
        self.btn_exporter_pdf = QPushButton("Exporter en PDF", self)
        self.btn_exporter_pdf.clicked.connect(self.exporter_pdf)
        layout.addWidget(self.btn_exporter_pdf)

        # Bouton pour importer plusieurs fichiers
        self.btn_importer_multiples = QPushButton("Importer plusieurs fichiers CSV", self)
        self.btn_importer_multiples.clicked.connect(self.importer_fichiers_multiples)
        layout.addWidget(self.btn_importer_multiples)

        # Bouton pour sauvegarde automatique avec versionnage
        self.btn_sauvegarde_auto = QPushButton("Sauvegarde automatique avec versionnage", self)
        self.btn_sauvegarde_auto.clicked.connect(self.sauvegarde_automatique)
        layout.addWidget(self.btn_sauvegarde_auto)

        # Bouton pour nettoyer les données
        self.btn_nettoyer_donnees = QPushButton("Nettoyer les données", self)
        self.btn_nettoyer_donnees.clicked.connect(self.nettoyer_donnees)
        layout.addWidget(self.btn_nettoyer_donnees)

        # Bouton pour sauvegarder en JSON
        self.btn_exporter_json = QPushButton("Exporter en JSON", self)
        self.btn_exporter_json.clicked.connect(self.exporter_json)
        layout.addWidget(self.btn_exporter_json)

        # **Bouton pour sauvegarder les modifications manuelles**
        self.btn_sauvegarder = QPushButton("Sauvegarder les modifications", self)
        self.btn_sauvegarder.clicked.connect(self.sauvegarder_modifications)
        self.btn_sauvegarder.setEnabled(False)
        layout.addWidget(self.btn_sauvegarder)

        # Initialiser historique des modifications
        self.historique_modifications = []
        self.btn_annuler = QPushButton("Annuler dernière modification", self)
        self.btn_annuler.clicked.connect(self.annuler_modification)
        layout.addWidget(self.btn_annuler)

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

    def ajouter_ligne(self):
        row_count = self.table_widget.rowCount()
        self.table_widget.insertRow(row_count)
        checkbox = QCheckBox()
        self.table_widget.setCellWidget(row_count, 0, checkbox)

    def ajouter_colonne(self):
        col_count = self.table_widget.columnCount()
        self.table_widget.insertColumn(col_count)
        self.table_widget.setHorizontalHeaderItem(col_count, QTableWidgetItem(f"Colonne {col_count}"))

    def supprimer_lignes(self):
        rows_to_delete = []
        for i in range(self.table_widget.rowCount()):
            checkbox = self.table_widget.cellWidget(i, 0)
            if checkbox.isChecked():
                rows_to_delete.append(i)
        for row in sorted(rows_to_delete, reverse=True):
            self.table_widget.removeRow(row)

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
                    ecrivain_csv = csv.DictWriter(fichier_sortie, fieldnames=colonnes_sortie)
                    ecrivain_csv.writeheader()
                    for ligne in lecteur_csv:
                        ligne_convertie = self.convertir_ligne(ligne, self.format_source, format_sortie)
                        ecrivain_csv.writerow(ligne_convertie)
            QMessageBox.information(self, "Succès", f"Le fichier a été converti avec succès et sauvegardé à : {self.chemin_fichier_sortie}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la conversion : {str(e)}")

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
                ligne_convertie[colonne_sortie] = ''
        return ligne_convertie

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

    def importer_fichiers_multiples(self):
        fichiers, _ = QFileDialog.getOpenFileNames(self, "Sélectionner plusieurs fichiers CSV", "", "Fichiers CSV (*.csv)")
        if fichiers:
            self.donnees_csv = []
            for fichier in fichiers:
                with open(fichier, 'r', newline='', encoding='utf-8') as f:
                    lecteur_csv = csv.reader(f)
                    self.donnees_csv.extend(list(lecteur_csv))
            QMessageBox.information(self, "Importé", "Les fichiers ont été importés avec succès")

    def sauvegarde_automatique(self):
        version = datetime.now().strftime("%Y%m%d%H%M%S")
        fichier_sortie = f"backup_version_{version}.csv"
        self.chemin_fichier_sortie = fichier_sortie
        self.convertir_fichier()

    def nettoyer_donnees(self):
        for row in range(self.table_widget.rowCount()):
            for col in range(1, self.table_widget.columnCount()):  # Ignorer la colonne des checkbox
                item = self.table_widget.item(row, col)
                if item and item.text():
                    # Nettoyage de texte : Suppression des espaces en trop
                    cleaned_text = item.text().strip()
                    self.table_widget.setItem(row, col, QTableWidgetItem(cleaned_text))
        QMessageBox.information(self, "Nettoyage des données", "Les données ont été nettoyées avec succès.")

    def sauvegarder_modifications(self):
        fichier_sortie, _ = QFileDialog.getSaveFileName(self, "Sauvegarder fichier CSV", "", "Fichiers CSV (*.csv)")
        if fichier_sortie:
            try:
                # Sauvegarder les modifications dans l'historique pour permettre annulation
                self.historique_modifications.append(self.donnees_csv.copy())
                
                # Sauvegarder les données éditées dans le fichier CSV
                with open(fichier_sortie, 'w', newline='', encoding='utf-8') as fichier:
                    ecrivain_csv = csv.writer(fichier)
                    en_tetes = [self.table_widget.horizontalHeaderItem(col).text() for col in range(1, self.table_widget.columnCount())]  # Ignorer la colonne des checkbox
                    ecrivain_csv.writerow(en_tetes)
                    for row in range(self.table_widget.rowCount()):
                        ligne = [self.table_widget.item(row, col).text() if self.table_widget.item(row, col) else '' for col in range(1, self.table_widget.columnCount())]
                        ecrivain_csv.writerow(ligne)

                QMessageBox.information(self, "Succès", f"Les modifications ont été sauvegardées dans le fichier : {fichier_sortie}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la sauvegarde : {str(e)}")

    def annuler_modification(self):
        if self.historique_modifications:
            # Restaurer la dernière modification enregistrée
            self.donnees_csv = self.historique_modifications.pop()
            self.charger_donnees_csv_from_list(self.donnees_csv)
            QMessageBox.information(self, "Annulation", "La dernière modification a été annulée.")
        else:
            QMessageBox.warning(self, "Avertissement", "Aucune modification à annuler.")

    def charger_donnees_csv_from_list(self, data_list):
        # Méthode pour recharger les données CSV dans le tableau à partir d'une liste
        if data_list:
            en_tetes = data_list[0]
            self.table_widget.setColumnCount(len(en_tetes) + 1)  # Une colonne supplémentaire pour les checkbox
            self.table_widget.setRowCount(len(data_list) - 1)
            self.table_widget.setHorizontalHeaderLabels(["Sélectionner"] + en_tetes)
            for i, ligne in enumerate(data_list[1:]):
                checkbox = QCheckBox()
                self.table_widget.setCellWidget(i, 0, checkbox)
                for j, valeur in enumerate(ligne):
                    item = QTableWidgetItem(valeur)
                    self.table_widget.setItem(i, j + 1, item)
            self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def exporter_json(self):
        fichier_json, _ = QFileDialog.getSaveFileName(self, "Sauvegarder fichier JSON", "", "Fichiers JSON (*.json)")
        if fichier_json:
            try:
                donnees_json = []
                en_tetes = [self.table_widget.horizontalHeaderItem(col).text() for col in range(1, self.table_widget.columnCount())]
                for row in range(self.table_widget.rowCount()):
                    ligne = {en_tetes[col - 1]: self.table_widget.item(row, col).text() if self.table_widget.item(row, col) else '' for col in range(1, self.table_widget.columnCount())}
                    donnees_json.append(ligne)

                with open(fichier_json, 'w', encoding='utf-8') as fichier:
                    json.dump(donnees_json, fichier, ensure_ascii=False, indent=4)

                QMessageBox.information(self, "Succès", f"Les données ont été exportées en JSON avec succès.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de l'exportation en JSON : {str(e)}")

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