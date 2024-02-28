import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import PhotoImage

def fetch_tables():
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    return [table[0] for table in tables]

def fetch_table_columns(table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return [column[1] for column in columns]

def fetch_table_data(table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    return data

def clear_table():
    for row in main_table.get_children():
        main_table.delete(row)

def update_main_table(columns, data):
    clear_table()
    display_columns = columns[:5]  # Sélectionnez les cinq premières colonnes à afficher
    main_table["columns"] = display_columns
    for col in display_columns:
        main_table.heading(col, text=col)
    max_columns = len(columns)  # Nombre maximal de colonnes disponibles
    for row in data:
        main_table.insert("", tk.END, values=row[:max_columns])  # Afficher toutes les colonnes disponibles

def display_table_data(event=None):  # Événement par défaut pour pouvoir l'appeler depuis le changement de sélection
    selected_table = tables_combobox.get()
    table_columns = fetch_table_columns(selected_table)
    table_data = fetch_table_data(selected_table)
    update_main_table(table_columns, table_data)

def display_details(event):
    selected_item = main_table.selection()[0]
    selected_row = main_table.item(selected_item, 'values')
    selected_table = tables_combobox.get()
    table_columns = fetch_table_columns(selected_table)
    show_details_window(selected_row, table_columns)



def show_details_window(selected_row, table_columns):
    details_window = tk.Toplevel(root)
    details_window.title("Détails de l'enregistrement")

    # Création d'une grille pour afficher les détails
    for i, (header, value) in enumerate(zip(table_columns, selected_row)):
        label_header = ttk.Label(details_window, text=header + ":", font=('Helvetica', 18, 'bold'))
        label_header.grid(row=i, column=0, sticky="e", padx=5, pady=2)

        label_value = ttk.Label(details_window, text=value, font=('Helvetica', 18))
        label_value.grid(row=i, column=1, sticky="w", padx=5, pady=2)

def search_data():
    keyword = search_entry.get().lower()
    selected_table = tables_combobox.get()
    table_columns = fetch_table_columns(selected_table)
    table_data = fetch_table_data(selected_table)
    
    # Filtrer les données en fonction du mot-clé
    filtered_data = [row for row in table_data if any(keyword in str(cell).lower() for cell in row)]
    
    # Mettre à jour le tableau principal avec les données filtrées
    update_main_table(table_columns, filtered_data)

def delete_record():
    selected_item = main_table.selection()[0]
    selected_row = main_table.item(selected_item, 'values')
    selected_table = tables_combobox.get()
    primary_key = selected_row[0]  # Supposons que la première colonne est la clé primaire
    cursor.execute(f"DELETE FROM {selected_table} WHERE {table_columns[0]}=?", (primary_key,))
    connection.commit()
    display_table_data()

def copy_to_clipboard(selected_row):
    record_text = "\t".join(map(str, selected_row))
    root.clipboard_clear()
    root.clipboard_append(record_text)
    print("Contenu copié avec succès dans le presse-papiers.")

connection = sqlite3.connect("data.db")
cursor = connection.cursor()

root = tk.Tk()
root.title("Affichage des Tables")

# Création du menu pour sélectionner la table
tables_label = tk.Label(root, text="Sélectionnez une table:")
tables_label.grid(row=0, column=0, padx=5, pady=5)
tables = fetch_tables()
selected_table = tk.StringVar(value=tables[0])  # Pré-sélectionner la première table
tables_combobox = ttk.Combobox(root, textvariable=selected_table, values=tables, state="readonly")
tables_combobox.grid(row=0, column=1, padx=5, pady=5)
tables_combobox.bind("<<ComboboxSelected>>", display_table_data)  # Lier la fonction à l'événement de sélection

# Champ de recherche
search_label = tk.Label(root, text="Recherche:")
search_label.grid(row=0, column=2, padx=5, pady=5)
search_entry = ttk.Entry(root)
search_entry.grid(row=0, column=3, padx=5, pady=5)

# Bouton de recherche
search_button = tk.Button(root, text="Rechercher", command=search_data)
search_button.grid(row=0, column=4, padx=5, pady=5)

# Bouton pour supprimer un enregistrement
delete_button = tk.Button(root, text="Supprimer l'enregistrement sélectionné", command=delete_record)
delete_button.grid(row=1, column=0, columnspan=5, padx=5, pady=5)

# Création du tableau pour afficher les données de la table principale
main_table = ttk.Treeview(root, show="headings", selectmode="browse")
main_table.grid(row=2, column=0, columnspan=5, padx=10, pady=10)
main_table.bind("<Double-1>", display_details)

root.mainloop()

connection.close()
