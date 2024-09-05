import sys
import csv
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView

class ConvertisseurCSV(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Configuration de la fenêtre principale
        self.setWindowTitle("Convertisseur CSV Canon, Xerox et Sharp (FR/EN)")
        self.setGeometry(100, 100, 600, 400)

        # Disposition verticale
        layout = QVBoxLayout()

        # Label d'instructions pour choisir un fichier CSV
        self.label = QLabel("Sélectionnez un fichier CSV à convertir ou éditer :", self)
        layout.addWidget(self.label)

        # Bouton pour charger le fichier d'entrée
        self.btn_charger = QPushButton("Charger fichier CSV", self)
        self.btn_charger.clicked.connect(self.charger_fichier)
        layout.addWidget(self.btn_charger)

        # Tableau pour éditer les données CSV
        self.table_widget = QTableWidget(self)
        layout.addWidget(self.table_widget)
        
        # Bouton pour ajouter une ligne ou une colonne
        self.btn_ajouter_ligne = QPushButton("Ajouter une ligne", self)
        self.btn_ajouter_ligne.clicked.connect(self.ajouter_ligne)
        layout.addWidget(self.btn_ajouter_ligne)

        self.btn_ajouter_colonne = QPushButton("Ajouter une colonne", self)
        self.btn_ajouter_colonne.clicked.connect(self.ajouter_colonne)
        layout.addWidget(self.btn_ajouter_colonne)

        # Bouton pour sauvegarder les modifications
        self.btn_sauvegarder = QPushButton("Sauvegarder les modifications", self)
        self.btn_sauvegarder.clicked.connect(self.sauvegarder_modifications)
        self.btn_sauvegarder.setEnabled(False)
        layout.addWidget(self.btn_sauvegarder)

        # Définir le layout pour la fenêtre
        self.setLayout(layout)

        # Variables de fichier
        self.chemin_fichier_entrée = None
        self.chemin_fichier_sortie = None
        self.donnees_csv = []

    def charger_fichier(self):
        # Ouvrir la boîte de dialogue pour choisir le fichier CSV
        fichier_entrée, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier CSV", "", "Fichiers CSV (*.csv)")
        if fichier_entrée:
            self.chemin_fichier_entrée = fichier_entrée
            self.label.setText(f"Fichier chargé : {fichier_entrée}")
            self.charger_donnees_csv(fichier_entrée)

    def charger_donnees_csv(self, fichier_csv):
        # Charger les données du fichier CSV dans le tableau
        with open(fichier_csv, 'r', newline='', encoding='utf-8') as fichier:
            lecteur_csv = csv.reader(fichier)
            self.donnees_csv = list(lecteur_csv)

        # Configuration du tableau
        if self.donnees_csv:
            en_tetes = self.donnees_csv[0]
            self.table_widget.setColumnCount(len(en_tetes))
            self.table_widget.setRowCount(len(self.donnees_csv) - 1)
            self.table_widget.setHorizontalHeaderLabels(en_tetes)
            
            for i, ligne in enumerate(self.donnees_csv[1:]):
                for j, valeur in enumerate(ligne):
                    item = QTableWidgetItem(valeur)
                    self.table_widget.setItem(i, j, item)

            # Activer le bouton pour sauvegarder les modifications
            self.btn_sauvegarder.setEnabled(True)
            self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def ajouter_ligne(self):
        # Ajouter une ligne vide dans le tableau
        self.table_widget.insertRow(self.table_widget.rowCount())

    def ajouter_colonne(self):
        # Ajouter une colonne vide dans le tableau
        col_count = self.table_widget.columnCount()
        self.table_widget.insertColumn(col_count)
        self.table_widget.setHorizontalHeaderItem(col_count, QTableWidgetItem(f"Colonne {col_count + 1}"))

    def sauvegarder_modifications(self):
        # Ouvrir la boîte de dialogue pour choisir où sauvegarder le fichier modifié
        fichier_sortie, _ = QFileDialog.getSaveFileName(self, "Sauvegarder fichier CSV", "", "Fichiers CSV (*.csv)")
        if fichier_sortie:
            self.chemin_fichier_sortie = fichier_sortie
            self.exporter_donnees_csv(fichier_sortie)

    def exporter_donnees_csv(self, fichier_sortie):
        try:
            # Sauvegarder les données éditées dans le fichier CSV
            with open(fichier_sortie, 'w', newline='', encoding='utf-8') as fichier:
                ecrivain_csv = csv.writer(fichier)
                
                # Sauvegarder les en-têtes
                en_tetes = [self.table_widget.horizontalHeaderItem(col).text() for col in range(self.table_widget.columnCount())]
                ecrivain_csv.writerow(en_tetes)

                # Sauvegarder chaque ligne éditée
                for row in range(self.table_widget.rowCount()):
                    ligne = [self.table_widget.item(row, col).text() if self.table_widget.item(row, col) else '' for col in range(self.table_widget.columnCount())]
                    ecrivain_csv.writerow(ligne)

            QMessageBox.information(self, "Succès", f"Les modifications ont été sauvegardées dans le fichier : {fichier_sortie}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la sauvegarde : {str(e)}")

# Initialisation de l'application
def main():
    app = QApplication(sys.argv)
    fenetre = ConvertisseurCSV()
    fenetre.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
