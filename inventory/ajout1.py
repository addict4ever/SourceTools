import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import Calendar
import sqlite3
import os
import shutil

def fetch_data(table_name, filter_type=None):
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    if filter_type:
        return [item[1] for item in data if item[2] == filter_type]
    else:
        return [item[1] for item in data]

def add_cellular():
    # Récupérer les données à partir des champs d'entrée et des menus déroulants
    brand = brand_var.get()
    model = model_entry.get()
    serial_number = serial_number_entry.get()
    os_val = os_var.get()
    screen_size = screen_size_entry.get()
    storage_capacity = storage_capacity_var.get()
    ram = ram_var.get()  # Récupération de la RAM à partir du menu déroulant
    sim_count = sim_count_var.get()
    price = price_entry.get()
    purchase_date = cal.get_date()

    # Insérer les données dans la table des téléphones cellulaires de votre base de données
    cursor.execute("INSERT INTO Cellulars (Brand, Model, SerialNumber, OS, ScreenSize, StorageCapacity, RAM, SIMCount, Price, PurchaseDate) \
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (brand, model, serial_number, os_val, screen_size, storage_capacity, ram, sim_count, price, purchase_date))
    connection.commit()

    folder_name = f"Cellular_{serial_number}"
    folder_path = os.path.join("cellulars", folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # Copier les fichiers sélectionnés dans le répertoire du téléphone cellulaire
    files = filedialog.askopenfilenames()
    for file in files:
        file_name = os.path.basename(file)
        destination = os.path.join(folder_path, file_name)
        shutil.copy(file, destination)

    # Afficher un message de confirmation
    messagebox.showinfo("Success", "Cellular phone added successfully.")

def browse_files():
    files = filedialog.askopenfilenames()
    if files:
        files_text.delete(1.0, tk.END)
        for file in files:
            files_text.insert(tk.END, file + '\n')

connection = sqlite3.connect("data.db")
cursor = connection.cursor()

root = tk.Tk()
root.title("Add a Cellular Phone")

# Obtenez la liste des marques à partir de la base de données
brands_list = fetch_data("Brand", "Cellulars")
os_list = ["iOS", "Android", "Other"]
storage_sizes_list = fetch_data("Storage")
ram_sizes_list = fetch_data("RAM")

# Éléments de l'interface utilisateur
labels = ["Number:", "Brand:", "Model:", "Serial Number:", "Operating System:", "Screen Size:", "Storage Capacity:", "RAM:", "SIM Count:", "Price:", "Purchase Date:", "Files:"]
for i, label_text in enumerate(labels):
    label = tk.Label(root, text=label_text)
    label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

# Champs d'entrée et menus déroulants
number_entry = tk.Entry(root)
number_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

brand_var = tk.StringVar()
brand_dropdown = ttk.Combobox(root, textvariable=brand_var, values=brands_list, state="readonly")
brand_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="w")
brand_dropdown.set(brands_list[0])

model_entry = tk.Entry(root)
model_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

serial_number_entry = tk.Entry(root)
serial_number_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

os_var = tk.StringVar()
os_dropdown = ttk.Combobox(root, textvariable=os_var, values=os_list, state="readonly")
os_dropdown.grid(row=4, column=1, padx=10, pady=5, sticky="w")
os_dropdown.set(os_list[0])

screen_size_entry = tk.Entry(root)
screen_size_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")

storage_capacity_var = tk.StringVar()
storage_capacity_entry = ttk.Combobox(root, textvariable=storage_capacity_var, values=storage_sizes_list, state="readonly")
storage_capacity_entry.grid(row=6, column=1, padx=10, pady=5, sticky="w")
storage_capacity_entry.set(storage_sizes_list[0])

ram_var = tk.StringVar()
ram_dropdown = ttk.Combobox(root, textvariable=ram_var, values=ram_sizes_list, state="readonly")
ram_dropdown.grid(row=7, column=1, padx=10, pady=5, sticky="w")
ram_dropdown.set(ram_sizes_list[0])

sim_count_var = tk.IntVar()
sim_count_entry = ttk.Entry(root, textvariable=sim_count_var)
sim_count_entry.grid(row=8, column=1, padx=10, pady=5, sticky="w")

price_entry = tk.Entry(root)
price_entry.grid(row=9, column=1, padx=10, pady=5, sticky="w")

cal = Calendar(root, selectmode="day", date_pattern="yyyy-mm-dd")
cal.grid(row=10, column=1, padx=10, pady=5, sticky="w")

files_text = tk.Text(root, height=5, width=30)
files_text.grid(row=11, column=1, padx=10, pady=5, sticky="w")

browse_button = tk.Button(root, text="Browse...", command=browse_files)
browse_button.grid(row=11, column=2, padx=10, pady=5, sticky="e")

add_button = tk.Button(root, text="Add Cellular Phone", command=add_cellular)
add_button.grid(row=12, columnspan=2, pady=10)

root.mainloop()

connection.close()
