import json
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog
from tkcalendar import DateEntry

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Database configuration
database_name = config["database_name"]
database_path = config["database_path"]
language_file = config["language"]

# Load language translations
with open(language_file, 'r') as translations_file:
    translations = json.load(translations_file)

# Function to detect foreign keys in the database
def detect_foreign_keys():
    connection = sqlite3.connect(database_path + '/' + database_name)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_key_list(Cellulars)")
    foreign_keys = cursor.fetchall()
    connection.close()
    return foreign_keys

# Function to fetch foreign keys for a specific table
def fetch_foreign_keys(table_name):
    connection = sqlite3.connect(database_path + '/' + database_name)
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    foreign_keys = cursor.fetchall()
    connection.close()
    return foreign_keys

# Function to fetch data linked to a specific table and column
def fetch_linked_data(table_name, linked_column):
    connection = sqlite3.connect(database_path + '/' + database_name)
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    connection.close()
    return data

# Function to fetch column information for a specific table
def fetch_table_columns(table_name):
    connection = sqlite3.connect(database_path + '/' + database_name)
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    connection.close()
    return columns_info

# Function to update combobox with data from a linked table
def update_combobox_from_linked_table(combobox, table_name, linked_column):
    data = fetch_linked_data(table_name, linked_column)
    values = [item[1] for item in data]
    combobox['values'] = values

# Function to create a date entry field
def create_date_field(root):
    date_field = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
    return date_field

def create_dynamic_form(root, columns_info, foreign_keys, new_number):
    row = 0
    form_fields = {}
    combobox_columns = [fk[3] for fk in foreign_keys]  # Get column names that have comboboxes
    for column_info in columns_info:
        column_name = column_info[1]
        translated_column_name = translations.get(column_name, column_name)
        if column_name != 'Number':  # Skip creating a field for 'Number' column
            if column_name not in combobox_columns:  # Exclude columns associated with comboboxes
                if not column_name.lower().endswith("id"):  # Exclude ID columns from display
                    label = tk.Label(root, text=translated_column_name)
                    label.grid(row=row, column=0, padx=10, pady=5, sticky='w')
                    if 'DATE' in column_info[2].upper():
                        entry = create_date_field(root)
                    elif 'FILE_PATHS' in column_name.upper():  # Handle FILE_PATHS column
                        file_paths_entry = tk.Entry(root, width=50)
                        file_paths_entry.grid(row=row, column=1, padx=10, pady=5, sticky='w')
                        button = tk.Button(root, text="Select a file", command=lambda col=column_name, entry=file_paths_entry: open_file_dialog(root, col, entry))
                        button.grid(row=row, column=2, padx=10, pady=5, sticky='w')
                        entry = file_paths_entry
                    else:
                        entry = ttk.Entry(root)
                    entry.grid(row=row, column=1, padx=10, pady=5, sticky='w')
                    form_fields[column_name] = entry
                    row += 1
            else:  # Column associated with a combobox
                linked_table = next((fk[2] for fk in foreign_keys if fk[3] == column_name), None)
                if linked_table:
                    label = tk.Label(root, text=translated_column_name)
                    label.grid(row=row, column=0, padx=10, pady=5, sticky='w')
                    combobox = ttk.Combobox(root)
                    combobox.grid(row=row, column=1, padx=10, pady=5, sticky='w')
                    update_combobox_from_linked_table(combobox, linked_table, column_name)
                    form_fields[column_name] = combobox
                    row += 1

    label = tk.Label(root, text="Number")
    label.grid(row=row, column=0, padx=10, pady=5, sticky='w')
    number_entry = ttk.Entry(root)
    number_entry.insert(0, str(new_number))  # Insert the generated number into the entry field
    number_entry.grid(row=row, column=1, padx=10, pady=5, sticky='w')
    form_fields['Number'] = number_entry
    row += 1

    return form_fields

# Function to open file dialog for selecting files
def open_file_dialog(root, column_name, file_paths_entry):
    file_paths = filedialog.askopenfilenames()
    if file_paths:
        file_paths_entry.delete(0, tk.END)
        file_paths_entry.insert(0, ', '.join(file_paths))


# Function to save data to the database
def save_data(form_values):
    connection = sqlite3.connect(database_path + '/' + database_name)
    cursor = connection.cursor()
    
    # Construct SQL query dynamically based on form values
    columns = ', '.join(form_values.keys())
    placeholders = ', '.join(['?' for _ in form_values])
    values = tuple(form_values.values())
    
    cursor.execute(f"INSERT INTO Cellulars ({columns}) VALUES ({placeholders})", values)
    
    connection.commit()
    connection.close()
    
    print("Data saved successfully.")

def save_button_click():
    form_values = {column_name: field.get() for column_name, field in form_fields.items()}
    # Ajouter le numéro généré dans form_values
    form_values['Number'] = form_fields['Number'].get()
    save_data(form_values)
    
if __name__ == "__main__":
    print("Relations between tables at startup:")
    print(detect_foreign_keys())

    connection = sqlite3.connect(database_path + '/' + database_name)
    cursor = connection.cursor()
    cursor.execute("SELECT MAX(Number) FROM Cellulars")
    last_number = cursor.fetchone()[0]

    if last_number is None or last_number == '':
        new_number = 10000  # Valeur par défaut si aucun numéro n'est trouvé
    else:
        new_number = int(last_number) + 1

    connection.close()

    # Initialize main window
    root = tk.Tk()
    root.title("Auto-detected Comboboxes")

    # Fetch and display foreign key comboboxes
    foreign_keys = fetch_foreign_keys("Cellulars")

    # Create form elements based on table columns
    cellulars_columns = fetch_table_columns("Cellulars")
    form_fields = create_dynamic_form(root, cellulars_columns, foreign_keys, new_number)

    

    # Create the Save button
    save_button = tk.Button(root, text="Save", command=save_button_click)
    save_button.grid(row=len(form_fields), column=1, padx=10, pady=5, sticky='e')

    root.mainloop()
