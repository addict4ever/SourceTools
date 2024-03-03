import json
import sqlite3
import tkinter as tk
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
    global form_fields
    form_fields = {}
    combobox_columns = [fk[3] for fk in foreign_keys] 
    required_fields = detect_required_fields(selected_table)  
    
    scrollable_frame = tk.Frame(root)
    scrollable_frame.pack(expand=True, fill="both", padx=10, pady=10)

    form_frame = tk.Frame(scrollable_frame)
    form_frame.pack(expand=True, fill="both", padx=0, pady=0)

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

    save_button = tk.Button(form_frame, text=translations.get("Save", "Save"), command=lambda: save_button_click(selected_table, required_fields))
    save_button.grid(row=len(form_fields), column=3, padx=10, pady=5, sticky='e')

    return_button = tk.Button(form_frame, text=translations.get("Main Menu", "Main Menu"), command=return_to_main_menu)
    return_button.grid(row=len(form_fields), column=2, padx=10, pady=5, sticky='e')

    for i in range(len(form_fields)):
        form_frame.grid_rowconfigure(i, weight=1)
    form_frame.grid_columnconfigure(1, weight=1)

    return form_fields


def update_combobox_from_linked_table(combobox, table_name, linked_column):
    data = fetch_linked_data(table_name, linked_column)
    values = [item[1] for item in data]
    combobox['values'] = values

def validate_data(form_values, columns_info):
    errors = []
    required_fields = [column[1] for column in columns_info if column[3] == '1']  
    for field_name in required_fields:
        if not form_values.get(field_name):  
            errors.append(f"{field_name} is required.")
    return "\n".join(errors)  

def save_button_click(table_name, required_fields):
    global is_saved
    form_values = {}
    for column_name, field in form_fields.items():
        if isinstance(field, tk.Text):
            form_values[column_name] = field.get("1.0", tk.END)
        else:
            form_values[column_name] = field.get()
    
    if successfully_saved_data():
        is_saved = True
        return_to_main_menu()
    else:
        messagebox.showerror(translate("Error"), translate("Failed to save data."))
        is_saved = False
    
    if any(form_values.get(field_name) for field_name in required_fields):
        errors = validate_data(form_values, fetch_table_columns(table_name))
        if errors:
            messagebox.showerror(translate("Validation Error"), errors)
        else:
            try:
                insert_data(table_name, form_values)
                messagebox.showinfo(translate("Success"), translate("Data saved successfully."))
            except sqlite3.IntegrityError as e:
                messagebox.showerror(translate("Insertion Error"), str(e))
    else:
        messagebox.showerror(translate("Validation Error"), translate("At least one required field must be filled."))
    return_to_main_menu()

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

    for widget in root.winfo_children():
        widget.destroy()

    root.title(f"{selected_table} Editor")
    form_fields = create_dynamic_form(root, selected_table, columns_info, foreign_keys, new_number)

def search_data(search_term):
    query = "SELECT * FROM sqlite_master WHERE type='table' ORDER BY name;"
    tables = execute_query(query, fetchall=True)
    results = []

    for table in tables:
        table_name = table[1]
        select_query = f"SELECT * FROM {table_name} WHERE "
        columns = fetch_table_columns(table_name)

        where_clause = " OR ".join([f"{column[1]} LIKE ?" for column in columns])
        select_query += where_clause

        table_results = execute_query(select_query, params=(f"%{search_term}%",), fetchall=True)
        prefixed_results = [(table_name, *row) for row in table_results]
        results.extend(prefixed_results)

    return results

def display_search_results(results):
    search_results_listbox.delete(0, tk.END)
    for row in results:
        search_results_listbox.insert(tk.END, row)

def successfully_saved_data():
    return True  

def main_menu(root):
    for widget in root.winfo_children():
        widget.destroy()
    
    menu_label = tk.Label(root, text=translations.get("Main Menu", "Main Menu"), font=("Arial", 18))
    menu_label.pack(pady=20)

    search_label = ttk.Label(root, text=translations.get("Search Term", "Search Term") + ":")
    search_label.pack()

    search_entry = ttk.Entry(root)
    search_entry.pack()

    search_button = ttk.Button(root, text=translations.get("Search", "Search"), command=lambda: search_button_click(search_entry.get()))
    search_button.pack()

    table_label = ttk.Label(root, text=translations.get("Select a table to edit", "Select a table to edit") + ":")
    table_label.pack()

    available_tables = fetch_tables()  
    table_menu = ttk.Combobox(root, values=available_tables)
    table_menu.pack()

    select_button = ttk.Button(root, text=translations.get("Select", "Select"), command=lambda: table_menu_select(table_menu.get(), root))
    select_button.pack()

    quit_button = ttk.Button(root, text=translations.get("Quit", "Quit"), command=root.quit)
    quit_button.pack(pady=20)


def return_to_main_menu():
    if not is_saved:
        if messagebox.askyesno(translate("Unsaved Changes"), translate("You have unsaved changes. Are you sure you want to continue?")):
            for widget in root.winfo_children():
                widget.destroy()
            main_menu(root)
    else:
        for widget in root.winfo_children():
            widget.destroy()
        main_menu(root)

def search_button_click(search_term):
    if search_term:
        results = search_all_tables(search_term)
        display_search_results(results)
    else:
        messagebox.showwarning(translate("Empty Search Term"), translate("Please enter a search term."))

def search_all_tables(search_term):
    results = []
    for table in available_tables:
        table_results = search_data(table, search_term)
        results.extend(table_results)
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
