import json
import sqlite3
import tkinter as tk
from gettext import gettext as translate
from functools import partial
from tkinter import ttk, filedialog, messagebox, scrolledtext 
from tkcalendar import DateEntry


form_fields = None  
is_saved = True 
canvas = None


def load_json_file(file_path):
    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        return data
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
    except Exception as e:
        return None

def load_translations(language_file):
    translations = load_json_file(language_file)
    if not translations:
        print("Error: Translations not loaded successfully.")
    return translations

config_data = load_json_file('config.json')

if config_data:
    company_name = config_data.get("company_name", "Table Search")
    database_name = config_data.get("database_name", "default_database_name")
    database_path = config_data.get("database_path", "default_database_path")
    language_file = config_data.get("language", "default_language_file")
    translations = load_translations(language_file)
    if not translations:
        print("Error: Translations not loaded successfully.")
else:
    print("Error: Configuration data not loaded successfully.")

def execute_query(query, params=None, fetchall=False):
    result = None
    with sqlite3.connect(database_path + '/' + database_name) as connection:
        cursor = connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        if fetchall:
            result = cursor.fetchall()
        else:
            result = cursor.fetchone()
    return result

def fetch_foreign_keys(table_name):
    query = f"PRAGMA foreign_key_list({table_name})"
    return execute_query(query, fetchall=True)

def fetch_table_columns(table_name):
    query = f"PRAGMA table_info({table_name})"
    return execute_query(query, fetchall=True)

def fetch_linked_data(table_name, linked_column):
    query = f"SELECT * FROM {table_name}"
    return execute_query(query, fetchall=True)

def insert_data(table_name, data):
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    values = tuple(data.values())
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    execute_query(query, params=values)

def detect_required_fields(table_name):
    query = f"PRAGMA table_info({table_name})"
    columns_info = execute_query(query, fetchall=True)
    return [column[1] for column in columns_info if column[3] == 1]

def create_date_field(root):
    return DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)

def open_file_dialog(root, column_name, file_paths_entry):  
    file_paths = filedialog.askopenfilenames()
    if file_paths:
        file_paths_entry.delete(0, tk.END)
        file_paths_entry.insert(0, ', '.join(file_paths))

def create_dynamic_form(root, selected_table, columns_info, foreign_keys, new_number):
    edit_window = tk.Toplevel(root)
    edit_window.title("Save Record")
    
    scrollable_frame = tk.Frame(edit_window)
    scrollable_frame.pack(expand=True, fill="both", padx=10, pady=10)

    form_frame = tk.Frame(scrollable_frame)
    form_frame.pack(expand=True, fill="both", padx=0, pady=0)
    
    form_fields = {}
    combobox_columns = [fk[3] for fk in foreign_keys] 
    required_fields = detect_required_fields(selected_table)  
    
    for column_info in columns_info:
        column_name = column_info[1]
        translated_column_name = translations.get(column_name, column_name)
        if column_name != 'Number':  
            if column_name not in combobox_columns:  
                if not column_name.lower().endswith("id"):  
                    label_text = translated_column_name
                    if column_name in required_fields:  
                        label_text += " *"
                    label = tk.Label(form_frame, text=label_text)
                    label.grid(row=len(form_fields), column=0, padx=10, pady=5, sticky='w')
                    if 'DATE' in column_info[2].upper():
                        entry = create_date_field(form_frame)
                        entry.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
                    elif 'FILE_PATHS' in column_name.upper():  
                        file_paths_entry = tk.Entry(form_frame, width=50)
                        file_paths_entry.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
                        button = tk.Button(form_frame, text=translations.get("Select a file", "Select a file"), command=lambda col=column_name, entry=file_paths_entry: open_file_dialog(root, col, entry))
                        button.grid(row=len(form_fields), column=2, padx=10, pady=5, sticky='w')
                        entry = file_paths_entry
                    elif 'NOTES' in column_name.upper():  
                        text_field = scrolledtext.ScrolledText(form_frame, height=5, width=50)  
                        text_field.grid(row=len(form_fields), column=1, columnspan=2, padx=10, pady=5, sticky='w')
                        entry = text_field
                    else:
                        entry = ttk.Entry(form_frame)
                        entry.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
                    form_fields[column_name] = entry
            else:  # Column associated with a combobox
                linked_table = next((fk[2] for fk in foreign_keys if fk[3] == column_name), None)
                if linked_table:
                    label_text = translated_column_name
                    if column_name in required_fields:  
                        label_text += " *"
                    label = tk.Label(form_frame, text=label_text)
                    label.grid(row=len(form_fields), column=0, padx=10, pady=5, sticky='w')
                    combobox = ttk.Combobox(form_frame)
                    combobox.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
                    update_combobox_from_linked_table(combobox, linked_table, column_name)
                    form_fields[column_name] = combobox

    if any(column[1] == 'Number' for column in columns_info):
        label = tk.Label(form_frame, text=translations.get("Number", "Number"))
        label.grid(row=len(form_fields), column=0, padx=10, pady=5, sticky='w')
        number_entry = ttk.Entry(form_frame)
        number_entry.insert(0, str(new_number))  
        number_entry.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
        form_fields['Number'] = number_entry

    save_button = tk.Button(form_frame, text=translations.get("Save", "Save"), command=lambda: save_button_click(selected_table, required_fields, form_fields))
    save_button.grid(row=len(form_fields), column=3, padx=10, pady=5, sticky='e')

    return_button = tk.Button(form_frame, text="Main Menu", command=edit_window.destroy)
    return_button.grid(row=len(form_fields), column=2, padx=10, pady=5, sticky='e')

    # Configure row and column weights for automatic resizing
    for i in range(len(form_fields)):
        form_frame.grid_rowconfigure(i, weight=1)
    form_frame.grid_columnconfigure((0,1,2,3), weight=1)

    return form_fields


def edit_record_form(record_details, selected_table, columns_info, foreign_keys, new_number):
    edit_window = tk.Toplevel(root)
    edit_window.title("Edit Record")

    form_fields = {}
    combobox_columns = [fk[3] for fk in foreign_keys]
    required_fields = detect_required_fields(selected_table)

    form_frame = tk.Frame(edit_window)
    form_frame.pack(expand=True, fill="both", padx=10, pady=10)

    # Vérifier si le champ 'Number' est présent dans les détails de l'enregistrement
    number_index = next((i for i, col_info in enumerate(columns_info) if col_info[1] == 'Number'), None)
    if number_index is not None:
        record_number = record_details[number_index]
        label_number = tk.Label(form_frame, text="Number:")
        label_number.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        entry_number = tk.Entry(form_frame)
        entry_number.insert(0, record_number)  # Afficher le numéro de l'enregistrement
        entry_number.grid(row=0, column=1, padx=10, pady=5, sticky='w')
        form_fields["Number"] = entry_number  # Ajouter le champ de saisie au dictionnaire form_fields

    # Convertir record_details en un dictionnaire avec les noms de colonnes comme clés
    record_dict = {column_info[1]: value for column_info, value in zip(columns_info, record_details)}

    for column_info in columns_info:
        column_name = column_info[1]
        translated_column_name = translations.get(column_name, column_name)
        if column_name != 'Number':
            if column_name not in combobox_columns:
                if not column_name.lower().endswith("id"):
                    label_text = translated_column_name
                    if column_name in required_fields:
                        label_text += " *"
                    label = tk.Label(form_frame, text=label_text)
                    label.grid(row=len(form_fields), column=0, padx=10, pady=5, sticky='w')

                    # Si le champ est un champ de date
                    if 'DATE' in column_info[2].upper():
                        entry = DateEntry(form_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
                        entry.set_date(record_dict.get(column_name, ''))  # Définir la date existante
                        entry.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
                        form_fields[column_name] = entry
                    elif 'FILE_PATHS' in column_name.upper():
                        file_paths_entry = tk.Entry(form_frame, width=50)
                        file_paths_entry.insert(0, record_dict.get(column_name, ''))  # Insérez la valeur existante
                        file_paths_entry.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
                        button = tk.Button(form_frame, text="Select a file", command=lambda col=column_name, entry=file_paths_entry: open_file_dialog(root, col, entry))
                        button.grid(row=len(form_fields), column=2, padx=10, pady=5, sticky='w')
                        entry = file_paths_entry
                    elif 'NOTES' in column_name.upper():
                        text_field = scrolledtext.ScrolledText(form_frame, height=5, width=50)
                        text_field.insert(tk.END, record_dict.get(column_name, ''))  # Insérez la valeur existante
                        text_field.grid(row=len(form_fields), column=1, columnspan=2, padx=10, pady=5, sticky='w')
                        entry = text_field
                    else:
                        entry = tk.Entry(form_frame)
                        entry.insert(0, record_dict.get(column_name, ''))  # Insérez la valeur existante
                        entry.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
                    form_fields[column_name] = entry
            else:
                linked_table = next((fk[2] for fk in foreign_keys if fk[3] == column_name), None)
                if linked_table:
                    label_text = translated_column_name
                    if column_name in required_fields:
                        label_text += " *"
                    label = tk.Label(form_frame, text=label_text)
                    label.grid(row=len(form_fields), column=0, padx=10, pady=5, sticky='w')
                    combobox = ttk.Combobox(form_frame)
                    combobox.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
                    update_combobox_from_linked_table(combobox, linked_table, column_name)
                    combobox.set(record_dict.get(column_name, ''))  # Sélectionnez la valeur existante dans le combobox
                    form_fields[column_name] = combobox

    # Bouton de sauvegarde
    save_button = tk.Button(form_frame, text="Save", command=lambda: save_button_click(selected_table, required_fields, form_fields, is_editing=True))
    save_button.grid(row=len(form_fields) + 1, column=1, padx=10, pady=5, sticky='e')

    # Bouton de retour
    return_button = tk.Button(form_frame, text="Main Menu", command=edit_window.destroy)
    return_button.grid(row=len(form_fields) + 1, column=0, padx=10, pady=5, sticky='e')

    # Ajustez les poids des lignes et des colonnes pour le redimensionnement automatique
    for i in range(len(form_fields)):
        form_frame.grid_rowconfigure(i, weight=1)
    form_frame.grid_columnconfigure(1, weight=1)

    edit_window.mainloop()


def update_combobox_from_linked_table(combobox, table_name, linked_column):
    data = fetch_linked_data(table_name, linked_column)
    values = [item[1] for item in data]
    combobox['values'] = values

def validate_data(form_values, columns_info):
    errors = []

    # Récupérer les noms des champs avec NOT NULL
    required_fields = [column[1] for column in columns_info if column[3] == '1']

    # Vérifier si chaque champ requis est présent dans form_values
    for field_name in required_fields:
        if not form_values.get(field_name):  
            errors.append(f"{field_name} is required.")

    # Renvoyer les erreurs sous forme d'une seule chaîne de texte
    return "\n".join(errors)

def save_button_click(table_name, required_fields, form_fields, is_editing=False):
    global is_saved
    form_values = {}
    missing_required_fields = []  # Liste pour stocker les champs requis manquants

    for column_name, field in form_fields.items():
        if isinstance(field, tk.Text):
            form_values[column_name] = field.get("1.0", tk.END)
        else:
            form_values[column_name] = field.get()

    # Vérification des champs requis
    for field_name in required_fields:
        if not form_values.get(field_name):
            missing_required_fields.append(field_name)

    # Si des champs requis sont manquants, afficher un message d'erreur
    if missing_required_fields:
        error_message = translate("The following required fields are missing:") + "\n" + "\n".join(missing_required_fields)
        messagebox.showerror(translate("Missing Required Fields"), error_message)
        return  # Sortir de la fonction sans enregistrer les données

    # Le reste de la fonction continue comme avant
    # Supposons que la modification est réussie si la requête de mise à jour est exécutée sans erreur
    if is_editing:
        try:
            update_data(table_name, form_values)  # Implémentez la fonction update_data pour mettre à jour les données existantes
            messagebox.showinfo(translate("Success"), translate("Data modified successfully."))
            return_to_main_menu()
            is_saved = True
        except Exception as e:
            messagebox.showerror(translate("Error"), translate("Failed to modify data."))
            is_saved = False
    else:
        if successfully_saved_data():
            is_saved = True
            return_to_main_menu()
        else:
            messagebox.showerror(translate("Error"), translate("Failed to save data."))
            is_saved = False

        try:
            insert_data(table_name, form_values)
            messagebox.showinfo(translate("Success"), translate("Data saved successfully."))
            return_to_main_menu()
        except sqlite3.IntegrityError as e:
            messagebox.showerror(translate("Insertion Error"), str(e))
            return_to_main_menu()


def update_data(table_name, new_values):
    set_clause = ", ".join([f"{column} = ?" for column in new_values.keys()])
    query = f"UPDATE {table_name} SET {set_clause} WHERE Number = ?"  # Assuming 'Number' is the primary key
    values = list(new_values.values()) + [new_values['Number']]  # Include the primary key value in the query
    execute_query(query, params=tuple(values))


def fetch_tables():
    query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    tables = execute_query(query, fetchall=True)
    return [table[0] for table in tables]

def table_menu_select(selected_table, root):
    global cellulars_columns
    cellulars_columns = fetch_table_columns(selected_table)  
    foreign_keys = fetch_foreign_keys(selected_table)
    columns_info = fetch_table_columns(selected_table)
    
    has_number_column = any(column[1] == "Number" for column in cellulars_columns)
    
    if has_number_column:
        last_number_query = f"SELECT MAX(Number) FROM {selected_table}"
        last_number_result = execute_query(last_number_query)
        last_number = last_number_result[0] if last_number_result[0] is not None else 0
        new_number = last_number + 1
    else:
        count_query = f"SELECT COUNT(*) FROM {selected_table}"
        count_result = execute_query(count_query)
        new_number = count_result[0] + 1

    
    
    form_fields = create_dynamic_form(root, selected_table, columns_info, foreign_keys, new_number)

def search_data(table_name, search_term):
    query = f"SELECT * FROM {table_name} WHERE "
    columns = fetch_table_columns(table_name)

    # Construire une clause WHERE en recherchant des occurrences partielles du terme de recherche dans chaque colonne
    where_conditions = []
    params = []
    for column in columns:
        where_conditions.append(f"{column[1]} LIKE ?")
        params.append(f"%{search_term}%")  # Recherche vague du terme dans les colonnes
    where_clause = " OR ".join(where_conditions)
    query += where_clause

    table_results = execute_query(query, params=params, fetchall=True)
    return table_results



def display_search_results(results, search_results_listbox):
    search_results_listbox.delete(0, tk.END)
    for row in results:
        search_results_listbox.insert(tk.END, row)

    # Bind double click event to the listbox
    search_results_listbox.bind("<Double-Button-1>", lambda event: on_double_click(event, search_results_listbox))

def on_double_click(event, search_results_listbox):
    selected_item = search_results_listbox.curselection()
    if selected_item:
        index = int(selected_item[0])
        record_details = search_results_listbox.get(index)
        selected_table = record_details[0]  # Le nom de la table est généralement le premier élément dans les détails de l'enregistrement
        columns_info = fetch_table_columns(selected_table)
        foreign_keys = fetch_foreign_keys(selected_table)
        new_number = record_details[0]  # Récupérer le numéro de l'enregistrement
        edit_record_form(record_details[1:], selected_table, columns_info, foreign_keys, new_number)  # Passer le nouveau numéro à la fonction edit_record_form


    
def successfully_saved_data():
    return True  

def main_menu(root):
    for widget in root.winfo_children():
        widget.destroy()

    available_tables = fetch_tables()  
    default_table = available_tables[0] if available_tables else None

    menu_label = tk.Label(root, text=translations.get("Main Menu", "Main Menu"), font=("Arial", 18))
    menu_label.pack(pady=(20, 10))

    search_frame = tk.Frame(root)
    search_frame.pack(pady=10)

    search_label = ttk.Label(search_frame, text=translations.get("Search Term", "Search Term") + ":")
    search_label.grid(row=0, column=0, padx=(0, 5))

    search_entry = ttk.Entry(search_frame)
    search_entry.grid(row=0, column=1, padx=(0, 5))

    search_button = ttk.Button(search_frame, text=translations.get("Search", "Search"), command=lambda: search_button_click(search_entry.get(), search_results_listbox))
    search_button.grid(row=0, column=2)

    # Create the listbox for displaying search results
    search_results_listbox = tk.Listbox(root)
    search_results_listbox.pack(fill="both", expand=True)

    table_frame = tk.Frame(root)
    table_frame.pack(pady=10)

    table_label = ttk.Label(table_frame, text=translations.get("Select a table to edit", "Select a table to edit") + ":")
    table_label.grid(row=0, column=0, padx=(0, 5))

    table_menu = ttk.Combobox(table_frame, values=available_tables)
    table_menu.set(default_table)  # Sélectionnez la première table par défaut
    table_menu.grid(row=0, column=1, padx=(0, 5))

    select_button = ttk.Button(table_frame, text=translations.get("Select", "Select"), command=lambda: table_menu_select(table_menu.get(), root))
    select_button.grid(row=0, column=2)

    quit_button = ttk.Button(root, text=translations.get("Quit", "Quit"), command=root.quit)
    quit_button.pack(pady=(10, 20), side="bottom")

    # Bind resizing event to adjust widget layout
    root.bind("<Configure>", lambda event: on_window_resize(root, search_results_listbox))

    # Limit maximum window size
    root.maxsize(1920, 1080)


def on_window_resize(root, search_results_listbox):
    # Update the scrollbar of the listbox if needed
    search_results_listbox.yview()



    


def return_to_main_menu():
    if not is_saved:
        if messagebox.askyesno(translate("Unsaved Changes"), translate("You have unsaved changes. Are you sure you want to continue?")):
            main_menu(root)  # Rechargez simplement le menu
    else:
        main_menu(root)  # Rechargez simplement le menu

def search_button_click(search_term, search_results_listbox):
    if search_term:
        results = search_all_tables(search_term)
        display_search_results(results, search_results_listbox)  # Pass search_results_listbox as an argument
    else:
        messagebox.showwarning(translate("Empty Search Term"), translate("Please enter a search term."))




def search_all_tables(search_term):
    results = []
    for table_name in available_tables:
        table_results = search_data(table_name, search_term)
        prefixed_results = [(table_name, *row) for row in table_results]
        results.extend(prefixed_results)
    return results


if __name__ == "__main__":
    print("Available tables:")
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    available_tables = fetch_tables()
    print(available_tables)

    root = tk.Tk()
    root.title(config.get("company_name", "Table Search"))

    main_menu(root) 
     

    root.mainloop()
