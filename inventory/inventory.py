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
global search_entry_global

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
def open_file_dialog(form_window, column_name, file_paths_entry):
    file_paths = filedialog.askopenfilenames(parent=form_window)
    if file_paths:
        form_window.focus_set()  # Mettre le formulaire en premier plan
        file_paths_entry.delete(0, tk.END)
        file_paths_entry.insert(0, ', '.join(file_paths))

def create_or_edit_record_form(root, selected_table, columns_info, foreign_keys, new_number=None, record_details=None, form_fields=None):
    edit_window = tk.Toplevel(root)
    if record_details:
        edit_window.title("Edit Record")
    else:
        edit_window.title("Save Record")
    
    scrollable_frame = tk.Frame(edit_window)
    scrollable_frame.pack(expand=True, fill="both", padx=10, pady=10)

    form_frame = tk.Frame(scrollable_frame)
    form_frame.pack(expand=True, fill="both", padx=0, pady=0)
    
    form_fields = {}
    combobox_columns = [fk[3] for fk in foreign_keys] 
    required_fields = detect_required_fields(selected_table)  
    
    if record_details:
        record_dict = {column_info[1]: value for column_info, value in zip(columns_info, record_details)}
    
    entry = None  # Initialisation de la variable entry
    
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

                    default_value = ''
                    if record_details:
                        default_value = record_dict.get(column_name, '')
                    
                    if 'DATE' in column_info[2].upper():
                        entry = create_date_field(form_frame)
                        if default_value:
                            entry.set_date(default_value)
                        entry.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
                    elif 'FILE_PATHS' in column_name.upper():  
                        file_paths_entry = tk.Entry(form_frame, width=50)
                        file_paths_entry.insert(0, default_value)
                        file_paths_entry.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
                        button = tk.Button(form_frame, text=translations.get("Select a file", "Select a file"), command=lambda col=column_name, entry=file_paths_entry: open_file_dialog(edit_window, col, entry))
                        button.grid(row=len(form_fields), column=2, padx=10, pady=5, sticky='w')
                        entry = file_paths_entry
                    elif 'NOTES' in column_name.upper():  
                        text_field = scrolledtext.ScrolledText(form_frame, height=5, width=50)  
                        text_field.grid(row=len(form_fields), column=1, columnspan=2, padx=10, pady=5, sticky='w')
                        if record_details:
                            default_value = record_dict.get(column_name, '')  
                            text_field.insert(tk.END, default_value)
                        entry = text_field

                    else:
                        entry = ttk.Entry(form_frame)
                        entry.insert(0, default_value)
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
                    combobox = ttk.Combobox(form_frame, state="readonly")
                    combobox.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
                    update_combobox_from_linked_table(combobox, linked_table, column_name)
                    if record_details:
                        combobox.set(record_dict.get(column_name, ''))
                    else:
                        if len(combobox['values']) > 0: 
                            combobox.set(combobox['values'][0])  
                    form_fields[column_name] = combobox

    if any(column[1] == 'Number' for column in columns_info):
        label = tk.Label(form_frame, text=translations.get("Number", "Number"))
        label.grid(row=len(form_fields), column=0, padx=10, pady=5, sticky='w')
        number_entry = ttk.Entry(form_frame)
        number_entry.insert(0, str(new_number))  
        number_entry.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='w')
        form_fields['Number'] = number_entry

    save_button_text = translations.get("Save", "Save") if record_details else translations.get("Save", "Save")
    save_button_command = get_save_button_command(selected_table, required_fields, form_fields, record_details)
    save_button = tk.Button(form_frame, text=save_button_text, command=save_button_command)
    save_button.grid(row=len(form_fields) + 1, column=0, padx=10, pady=5, sticky='e')

    return_button = tk.Button(form_frame, text="Main Menu", command=edit_window.destroy)
    return_button.grid(row=len(form_fields) + 1, column=1, padx=10, pady=5, sticky='e')

    for i in range(len(form_fields)):
        form_frame.grid_rowconfigure(i, weight=1)
    form_frame.grid_columnconfigure((0,1), weight=1)

    edit_window.mainloop()



def get_save_button_command(selected_table, required_fields, form_fields, record_details=None):
    if record_details is None:
        return lambda: save_button_click(selected_table, required_fields, form_fields,is_editing=False)
    else:
        return lambda: save_button_click(selected_table, required_fields, form_fields,is_editing=True)
        
def update_combobox_from_linked_table(combobox, table_name, linked_column):
    data = fetch_linked_data(table_name, linked_column)
    values = [item[1] for item in data]
    combobox['values'] = values

def validate_data(form_values, columns_info):
    print ("lol")
    errors = []
    required_fields = [column[1] for column in columns_info if column[3] == '1']
    for field_name in required_fields:
        if not form_values.get(field_name):
            errors.append(f"{field_name} is required.")
    return "\n".join(errors)

def show_error_message(message):
    error_window = tk.Toplevel()
    error_window.title("Error")
    error_label = tk.Label(error_window, text=message, padx=20, pady=10)
    error_label.pack()
    error_button = tk.Button(error_window, text="OK", command=error_window.destroy)
    error_button.pack()
    
def save_button_click(table_name, required_fields, form_fields, is_editing=False):
    global is_saved
    print("Save button clicked")  
    form_values = {}
    for column_name, field in form_fields.items():
        if isinstance(field, tk.Text):
            form_values[column_name] = field.get("1.0", tk.END)
        else:
            form_values[column_name] = field.get()
    
    print("Form values:", form_values)  

    if is_editing:
        try:
            update_data(table_name, form_values)
            print(form_values)
            messagebox.showinfo("Success", "Data modified successfully.")
            return_to_main_menu()
            is_saved = True
        except sqlite3.Error as e:
            show_error_message(f"SQLite error: {str(e)}")
            is_saved = False
        except Exception as e:
            show_error_message(f"An unexpected error occurred: {str(e)}")
            is_saved = False
    else:
        if any(form_values.get(field_name) for field_name in required_fields):
            errors = validate_data(form_values, fetch_table_columns(table_name))
            if errors:
                show_error_message(errors)
                return
            else:
                try:
                    insert_data(table_name, form_values)
                    messagebox.showinfo("Success", "Data saved successfully.")
                   
                    main_menu(root)
                except sqlite3.IntegrityError as e:
                    show_error_message(str(e))
                except sqlite3.Error as e:
                    show_error_message(f"SQLite error: {str(e)}")
                    is_saved = False
                except Exception as e:
                    show_error_message(f"An unexpected error occurred: {str(e)}")
                    is_saved = False
        else:
            show_error_message("At least one required field must be filled.")

def show_info_message(message):
    info_window = tk.Toplevel()
    info_window.title("Success")
    info_label = tk.Label(info_window, text=message, padx=20, pady=10)
    info_label.pack()
    info_button = tk.Button(info_window, text="OK", command=info_window.destroy)
    info_button.pack()
    
def update_data(table_name, new_values):
    required_fields = detect_required_fields(table_name) 
    set_clauses = [f"{column} = ?" for column in new_values.keys() if column != 'Number']  
    set_clause = ", ".join(set_clauses)
    query = f"UPDATE {table_name} SET {set_clause} WHERE Number = ?"


    missing_required_fields = [field for field in required_fields if field not in new_values.keys()]
    if missing_required_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_required_fields)}")

    # Construire la liste des valeurs pour la requête SQL
    values = [new_values[column] for column in new_values.keys() if column != 'Number'] + [new_values['Number']]

    # Exécuter la requête SQL
    execute_query(query, params=tuple(values))



def detect_unique_column(table_name):
    query = f"PRAGMA table_info({table_name})"
    columns_info = execute_query(query, fetchall=True)
    for column_info in columns_info:
        if column_info[5] == 1:  
            return column_info[1]  
    return None  
    
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
    
    form_fields = create_or_edit_record_form(root, selected_table, columns_info, foreign_keys, new_number)

def search_all_tables(search_term):
    results = []
    available_tables = fetch_tables()
    for table_name in available_tables:
        table_results = search_data(table_name, search_term)
        prefixed_results = [(table_name, *row) for row in table_results]
        results.extend(prefixed_results)
    return results
    
def search_data(table_name, search_term):
    query = f"SELECT * FROM {table_name} WHERE "
    columns = fetch_table_columns(table_name)

    where_conditions = []
    params = []
    for column in columns:
        where_conditions.append(f"{column[1]} LIKE ?")
        params.append(f"%{search_term}%")
    where_clause = " OR ".join(where_conditions)
    query += where_clause

    table_results = execute_query(query, params=params, fetchall=True)
    return table_results

def display_search_results(results, search_results_listbox):
    search_results_listbox.delete(0, tk.END)
    for row in results:
        search_results_listbox.insert(tk.END, row)

    search_results_listbox.bind("<Double-Button-1>", lambda event: on_double_click(event, search_results_listbox))

def on_double_click(event, search_results_listbox):
    selected_item = search_results_listbox.curselection()
    if selected_item:
        index = int(selected_item[0])
        record_details = search_results_listbox.get(index)
        selected_table = record_details[0]
        columns_info = fetch_table_columns(selected_table)
        foreign_keys = fetch_foreign_keys(selected_table)
        new_number = record_details[1]  
        create_or_edit_record_form(root, selected_table, columns_info, foreign_keys, new_number, record_details[1:])  


def fetch_record_details(table_name, record_id):
    query = f"SELECT * FROM {table_name} WHERE ID = ?"
    record_details = execute_query(query, params=(record_id,))
    return record_details
    
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

    search_entry_global = ttk.Entry(search_frame)
    search_entry_global.grid(row=0, column=1, padx=(0, 5))

    search_button = ttk.Button(search_frame, text=translations.get("Search", "Search"), command=lambda: search_button_click(search_entry_global.get(), search_results_listbox, search_entry_global.get()))
    search_button.grid(row=0, column=2)

    search_results_listbox = tk.Listbox(root)
    search_results_listbox.pack(fill="both", expand=True)

    table_frame = tk.Frame(root)
    table_frame.pack(pady=10)

    table_label = ttk.Label(table_frame, text=translations.get("Select a table to edit", "Select a table to edit") + ":")
    table_label.grid(row=0, column=0, padx=(0, 5))

    table_menu = ttk.Combobox(table_frame, values=available_tables)
    table_menu.set(default_table) 
    table_menu.grid(row=0, column=1, padx=(0, 5))

    new_button = ttk.Button(root, text=translations.get("New", "New"), command=lambda: table_menu_select(table_menu.get(), root))
    new_button.pack(pady=10, side="top")

    delete_button = ttk.Button(root, text=translations.get("Delete", "Delete"), command=lambda: delete_selected(search_results_listbox, search_entry_global))
    delete_button.pack(pady=10, side="top")
    
    quit_button = ttk.Button(root, text="Quit", command=root.quit)
    quit_button.pack(pady=10, side="top")

def delete_selected(search_results_listbox, search_entry):
    selected_item = search_results_listbox.curselection()
    if selected_item:
        index = int(selected_item[0])
        record_details = search_results_listbox.get(index)
        selected_table = record_details[0]
        record_id = record_details[1]
        if messagebox.askokcancel("Delete", f"Do you want to delete this record from {selected_table}?"):
            delete_record(selected_table, record_id)
            search_button_click(search_entry.get(), search_results_listbox, search_entry.get())

def delete_record(table_name, record_id):
    query = f"DELETE FROM {table_name} WHERE ID = ?"
    execute_query(query, params=(record_id,))


def search_button_click(search_term, search_results_listbox, selected_table):
    if not search_term and selected_table:
        results = execute_query(f"SELECT * FROM {selected_table}", fetchall=True)
        display_search_results([(selected_table, *row) for row in results], search_results_listbox)
    else:
        results = search_all_tables(search_term)
        display_search_results(results, search_results_listbox)
        
def return_to_main_menu():
    global root
    main_menu(root)

def open_root():
    global root
    root = tk.Tk()
    root.title(company_name)
    main_menu(root)
    root.mainloop()

if __name__ == "__main__":
    open_root()
