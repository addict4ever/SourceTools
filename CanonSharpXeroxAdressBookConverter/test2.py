import sys
import csv
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QLineEdit
from PyQt5.QtCore import Qt

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

        # Bouton pour sauvegarder en JSON
        self.btn_exporter_json = QPushButton("Exporter en JSON", self)
        self.btn_exporter_json.clicked.connect(self.exporter_json)
        layout.addWidget(self.btn_exporter_json)

        # **Bouton pour sauvegarder les modifications manuelles**
        self.btn_sauvegarder = QPushButton("Sauvegarder les modifications", self)
        self.btn_sauvegarder.clicked.connect(self.sauvegarder_modifications)
        self.btn_sauvegarder.setEnabled(False)  # Désactivé jusqu'à ce qu'un fichier soit chargé
        layout.addWidget(self.btn_sauvegarder)

        # Définir le layout pour la fenêtre
        self.setLayout(layout)

        # Variables de fichier
        self.chemin_fichier_entrée = None
        self.chemin_fichier_sortie = None
        self.format_source = None
        self.langue_source = None
        self.donnees_csv = []

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
                self.combo_source.setCurrentText(self.format_source)  # Mise à jour de la ComboBox
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
            
            self.charger_donnees_csv(fichier_entrée)

    def detecter_format_et_langue(self, fichier_csv):
        # Lire les en-têtes du fichier CSV pour détecter le format et la langue (insensible à la casse)
        with open(fichier_csv, 'r', newline='', encoding='utf-8') as fichier:
            lecteur_csv = csv.reader(fichier)
            en_tetes = [col.lower() for col in next(lecteur_csv)]  # Convertir toutes les colonnes en minuscules

            # Détection des colonnes selon le format et la langue
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
        # Charger les données du fichier CSV dans le tableau
        with open(fichier_csv, 'r', newline='', encoding='utf-8') as fichier:
            lecteur_csv = csv.reader(fichier)
            self.donnees_csv = list(lecteur_csv)

        # Configuration du tableau
        if self.donnees_csv:
            en_tetes = self.donnees_csv[0]
            self.table_widget.setColumnCount(len(en_tetes) + 1)  # Une colonne supplémentaire pour les checkbox
            self.table_widget.setRowCount(len(self.donnees_csv) - 1)
            self.table_widget.setHorizontalHeaderLabels(["Sélectionner"] + en_tetes)
            # Remplir le tableau avec les données et ajouter des checkbox pour chaque ligne
            for i, ligne in enumerate(self.donnees_csv[1:]):
                # Ajouter la checkbox de sélection
                checkbox = QCheckBox()
                self.table_widget.setCellWidget(i, 0, checkbox)
                
                # Ajouter les valeurs des colonnes
                for j, valeur in enumerate(ligne):
                    item = QTableWidgetItem(valeur)
                    self.table_widget.setItem(i, j + 1, item)  # Décalage d'une colonne pour laisser la place au checkbox

            # Activer le bouton de sauvegarde
            self.btn_sauvegarder.setEnabled(True)
            self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def ajouter_ligne(self):
        # Ajouter une ligne vide dans le tableau
        row_count = self.table_widget.rowCount()
        self.table_widget.insertRow(row_count)

        # Ajouter une checkbox dans la nouvelle ligne
        checkbox = QCheckBox()
        self.table_widget.setCellWidget(row_count, 0, checkbox)

    def ajouter_colonne(self):
        # Ajouter une colonne vide dans le tableau
        col_count = self.table_widget.columnCount()
        self.table_widget.insertColumn(col_count)
        self.table_widget.setHorizontalHeaderItem(col_count, QTableWidgetItem(f"Colonne {col_count}"))

    def supprimer_lignes(self):
        # Supprimer les lignes sélectionnées via les checkbox
        rows_to_delete = []
        for i in range(self.table_widget.rowCount()):
            checkbox = self.table_widget.cellWidget(i, 0)  # Récupérer la checkbox
            if checkbox.isChecked():  # Si la ligne est sélectionnée
                rows_to_delete.append(i)

        # Supprimer les lignes de la fin vers le début pour éviter les décalages d'index
        for row in sorted(rows_to_delete, reverse=True):
            self.table_widget.removeRow(row)

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

                # Vérifier si les colonnes du fichier source sont correctes (insensible à la casse)
                if not all(col.lower() in [c.lower() for c in lecteur_csv.fieldnames] for col in colonnes_source):
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
                return ['Nom', 'Email', 'Téléphone', 'Adresse', 'Entreprise', 'Fax', 'Catégorie', 'Localisation', 'Notes', 'Titre', 'Département']
            else:
                return ['Name', 'Email', 'Phone', 'Address', 'Company', 'Fax', 'Category', 'Location', 'Notes', 'Job Title', 'Department']
        elif format_type == "Xerox":
            if langue == 'Français':
                return ['Nom', 'Adresse e-mail', 'Numéro de téléphone', 'Adresse', 'Entreprise', 'Numéro de fax', 'Département', 'Titre', 'Notes', 'Localisation']
            else:
                return ['Display Name', 'Email Address', 'Phone Number', 'Address', 'Company', 'Fax Number', 'Department', 'Title', 'Notes', 'Location']
        elif format_type == "Sharp":
            # Colonnes spécifiques au format Sharp, selon le fichier fourni
            return ['address', 'search-id', 'name', 'search-string', 'category-id', 'frequently-used',
                    'mail-address', 'fax-number', 'ifax-address', 'ftp-host', 'ftp-directory', 'ftp-username',
                    'ftp-username/@encodingMethod', 'ftp-password', 'ftp-password/@encodingMethod', 
                    'smb-directory', 'smb-username', 'smb-username/@encodingMethod', 'smb-password', 
                    'smb-password/@encodingMethod', 'desktop-host', 'desktop-port', 'desktop-directory', 
                    'desktop-username', 'desktop-username/@encodingMethod', 'desktop-password', 
                    'desktop-password/@encodingMethod']

    def convertir_ligne(self, ligne, format_source, format_sortie):
        # Adapter les noms de colonnes selon le format source et cible
        correspondance = {
            'Name': ['display name', 'nom', 'name'],  # Nom dans Xerox et Canon
            'Email': ['email address', 'mail-address'],  # E-mail dans Xerox et Canon
            'Phone': ['phone number'],  # Téléphone dans Xerox
            'Address': ['address'],  # Adresse dans Xerox
            'Company': ['company'],  # Entreprise dans Xerox
            'Fax': ['fax number', 'ifax-address'],  # Numéro de fax
            'Category': ['category-id'],  # Catégorie (existe dans certains systèmes)
            'Location': ['location'],  # Localisation (présent dans certains systèmes)
            'Notes': ['notes'],  # Notes supplémentaires
            'Job Title': ['title'],  # Titre professionnel
            'Department': ['department']  # Département
        }

        ligne_convertie = {}
        for colonne_sortie in self.obtenir_colonnes(format_sortie, 'Anglais'):  # Sortie en anglais par défaut
            for colonne_source in correspondance.get(colonne_sortie.lower(), []):  # Gérer la casse ici aussi
                if colonne_source in ligne:
                    ligne_convertie[colonne_sortie] = ligne[colonne_source]
                    break
            else:
                # Si aucune correspondance trouvée, remplir avec une valeur vide
                ligne_convertie[colonne_sortie] = ''

        return ligne_convertie

    def sauvegarder_modifications(self):
        # Ouvrir la boîte de dialogue pour choisir où sauvegarder le fichier modifié
        fichier_sortie, _ = QFileDialog.getSaveFileName(self, "Sauvegarder fichier CSV", "", "Fichiers CSV (*.csv)")
        if fichier_sortie:
            try:
                # Sauvegarder les données éditées dans le fichier CSV
                with open(fichier_sortie, 'w', newline='', encoding='utf-8') as fichier:
                    ecrivain_csv = csv.writer(fichier)

                    # Sauvegarder les en-têtes
                    en_tetes = [self.table_widget.horizontalHeaderItem(col).text() for col in range(1, self.table_widget.columnCount())]  # Ignorer la colonne des checkbox
                    ecrivain_csv.writerow(en_tetes)

                    # Sauvegarder chaque ligne éditée
                    for row in range(self.table_widget.rowCount()):
                        ligne = [self.table_widget.item(row, col).text() if self.table_widget.item(row, col) else '' for col in range(1, self.table_widget.columnCount())]
                        ecrivain_csv.writerow(ligne)

                QMessageBox.information(self, "Succès", f"Les modifications ont été sauvegardées dans le fichier : {fichier_sortie}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la sauvegarde : {str(e)}")

    def exporter_json(self):
        # Exporter les données en JSON
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

# Initialisation de l'application
def main():
    app = QApplication(sys.argv)
    fenetre = ConvertisseurCSV()
    fenetre.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

