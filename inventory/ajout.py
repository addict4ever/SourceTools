import tkinter as tk
from tkinter import ttk, filedialog
from tkcalendar import Calendar
import sqlite3

def fetch_data(table_name, filter_type=None):
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    if filter_type:
        return [item[1] for item in data if item[2] == filter_type]
    else:
        return [item[1] for item in data]

def add_cellular():
    # Récupérez les données à partir des champs d'entrée et des menus déroulants
    brand = brand_var.get()
    model = model_entry.get()
    serial_number = serial_number_entry.get()
    os = os_var.get()
    screen_size = screen_size_entry.get()  # Ajoutez les autres champs nécessaires
    storage_capacity = storage_capacity_entry.get()
    price = price_entry.get()
    purchase_date = cal.get_date()

    # Insérez les données dans la table appropriée de votre base de données
    cursor.execute("INSERT INTO Cellulars (Brand, Model, SerialNumber, OS, ScreenSize, StorageCapacity, Price, PurchaseDate) \
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (brand, model, serial_number, os, screen_size, storage_capacity, price, purchase_date))
    connection.commit()

def add_computer():
    # Récupérez les données à partir des champs d'entrée et des menus déroulants
    number = number_entry.get()
    brand = brand_var.get()
    model = model_entry.get()
    serial_number = serial_number_entry.get()
    identification_number = identification_number_entry.get()
    state = state_var.get()
    processor = processor_var.get()
    processor_name = processor_name_entry.get()
    number_of_cpu = number_of_cpu_entry.get()
    ram_memory = ram_var.get()
    storage = storage_var.get()
    graphics_card = graphics_card_var.get()
    purchase_date = cal.get_date()  # Get selected date from calendar widget
    price = price_spinbox.get()
    other_specs = other_specs_entry.get()
    notes = notes_entry.get()
    user_history = user_history_entry.get()
    invoices = files_text.get("1.0", tk.END).strip().split("\n")

    # Insérez les données dans la table appropriée de votre base de données
    cursor.execute("INSERT INTO Computers (Number, Brand, Model, SerialNumber, IdentificationNumber, State, Processor, \
                    ProcessorName, NumberOfCPU, RamMemory, Storage, GraphicsCard, PurchaseDate, Price, OtherSpecs, Notes, \
                    UserHistory, Invoices) \
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (number, brand, model, serial_number, identification_number, state, processor, processor_name, 
                    number_of_cpu, ram_memory, storage, graphics_card, purchase_date, price, other_specs, notes, 
                    user_history, ";".join(invoices)))
    connection.commit()

def browse_files():
    files = filedialog.askopenfilenames()
    if files:
        files_text.delete(1.0, tk.END)
        for file in files:
            files_text.insert(tk.END, file + '\n')

def update_purchase_date(event):
    purchase_date = cal.get_date()
    purchase_date_entry.delete(0, tk.END)
    purchase_date_entry.insert(0, purchase_date)

connection = sqlite3.connect("data.db")
cursor = connection.cursor()

root = tk.Tk()
root.title("Add an Item")

# Définition des listes de données
processors_list = fetch_data("Processor")
ram_sizes_list = fetch_data("RAM")
states_list = fetch_data("State")
brands_list = fetch_data("Brand", "Computers")
graphics_cards_list = fetch_data("Brand", "Graphics")
storage_sizes_list = fetch_data("Storage")
cpu_numbers_list = fetch_data("CPU")

# Éléments de l'interface utilisateur
labels = ["Number:", "Brand:", "Model:", "Serial Number:", "Identification Number:", "State:", "Processor:", "Processor Name:", "Number of CPU:",
          "Ram Memory:", "Storage:", "Graphics Card:", "Price:", "Purchase Date:", "Other Specs:", "Notes:",
          "User History:", "Invoices:"]
for i, label_text in enumerate(labels):
    label = tk.Label(root, text=label_text)
    label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

# Champs d'entrée et menus déroulants
brand_var = tk.StringVar()
brand_dropdown = ttk.Combobox(root, textvariable=brand_var, values=brands_list, state="readonly")
brand_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="w")
brand_dropdown.set(brands_list[0])

number_entry = tk.Entry(root)
number_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

model_entry = tk.Entry(root)
model_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

serial_number_entry = tk.Entry(root)
serial_number_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

identification_number_entry = tk.Entry(root)
identification_number_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

state_var = tk.StringVar()
state_dropdown = ttk.Combobox(root, textvariable=state_var, values=states_list, state="readonly")
state_dropdown.grid(row=5, column=1, padx=10, pady=5, sticky="w")

processor_var = tk.StringVar()
processor_dropdown = ttk.Combobox(root, textvariable=processor_var, values=processors_list, state="readonly")
processor_dropdown.grid(row=6, column=1, padx=10, pady=5, sticky="w")

processor_name_entry = tk.Entry(root)
processor_name_entry.grid(row=7, column=1, padx=10, pady=5, sticky="w")

number_of_cpu_entry = ttk.Combobox(root, values=cpu_numbers_list, state="readonly")
number_of_cpu_entry.grid(row=8, column=1, padx=10, pady=5, sticky="w")

ram_var = tk.StringVar()
ram_dropdown = ttk.Combobox(root, textvariable=ram_var, values=ram_sizes_list, state="readonly")
ram_dropdown.grid(row=9, column=1, padx=10, pady=5, sticky="w")

storage_var = tk.StringVar()
storage_dropdown = ttk.Combobox(root, textvariable=storage_var, values=storage_sizes_list, state="readonly")
storage_dropdown.grid(row=10, column=1, padx=10, pady=5, sticky="w")

graphics_card_var = tk.StringVar()
graphics_card_dropdown = ttk.Combobox(root, textvariable=graphics_card_var, values=graphics_cards_list, state="readonly")
graphics_card_dropdown.grid(row=11, column=1, padx=10, pady=5, sticky="w")

price_spinbox = ttk.Spinbox(root, from_=0, to=10000, increment=10)
price_spinbox.grid(row=12, column=1, padx=10, pady=5, sticky="w")

other_specs_entry = tk.Entry(root)
other_specs_entry.grid(row=13, column=1, padx=10, pady=5, sticky="w")

notes_entry = tk.Entry(root)
notes_entry.grid(row=14, column=1, padx=10, pady=5, sticky="w")

user_history_entry = tk.Entry(root)
user_history_entry.grid(row=15, column=1, padx=10, pady=5, sticky="w")

files_text = tk.Text(root, height=5, width=30)
files_text.grid(row=16, column=1, padx=10, pady=5, sticky="w")

browse_button = tk.Button(root, text="Browse...", command=browse_files)
browse_button.grid(row=16, column=2, padx=10, pady=5, sticky="e")

add_button = tk.Button(root, text="Add Item", command=add_computer)  # Bouton par défaut pour "Computers"
add_button.grid(row=17, columnspan=2, pady=10)

purchase_date_entry = tk.Entry(root)
purchase_date_entry.grid(row=13, column=1, padx=10, pady=5, sticky="w")

cal = Calendar(root, selectmode="day", date_pattern="yyyy-mm-dd")
cal.grid(row=12, column=2, padx=10, pady=5, sticky="w")
cal.bind("<<CalendarSelected>>", update_purchase_date)

# Sélectionner le premier choix par défaut dans les menus déroulants
for dropdown in (state_dropdown, processor_dropdown, number_of_cpu_entry, ram_dropdown, storage_dropdown, graphics_card_dropdown):
    dropdown.current(0)

# Cadre pour la sélection de la table (Computers ou Cellulars)
selected_table = tk.StringVar()
selected_table.set("Computers")  # Défaut sélectionné comme "Computers"
table_selection_frame = tk.Frame(root)
table_selection_frame.grid(row=18, columnspan=2, pady=10)
tk.Label(table_selection_frame, text="Select Table:").pack(side="left")
computers_radio = tk.Radiobutton(table_selection_frame, text="Computers", variable=selected_table, value="Computers")
computers_radio.pack(side="left")
cellulars_radio = tk.Radiobutton(table_selection_frame, text="Cellulars", variable=selected_table, value="Cellulars")
cellulars_radio.pack(side="left")

root.mainloop()

connection.close()
