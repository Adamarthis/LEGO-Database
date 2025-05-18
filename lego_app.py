import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import requests
import io
import os

# Ensure the database is created in the same folder as the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, 'lego_database.db')

# Define color scheme
BG_COLOR = '#e0ffe0' # Light green background
FRAME_COLOR = '#c0f0c0' # Slightly darker green for frames
TEXT_COLOR = '#000000' # Black text

def initialize_database():
    """Initializes the SQLite database and creates the legos table, adding series column if needed."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS legos (
                articul TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                part_count INTEGER,
                all_parts INTEGER, -- 0 for False, 1 for True
                picture TEXT
                -- series TEXT will be added if it doesn't exist
            )
        ''')

        # Check if 'series' column exists, add if not
        cursor.execute("PRAGMA table_info(legos)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'series' not in columns:
            cursor.execute("ALTER TABLE legos ADD COLUMN series TEXT")
            print("Added 'series' column to the database.")

        conn.commit()
        print("Database initialized successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def add_lego_to_db(articul, name, part_count, all_parts, picture, series):
    """Adds a new LEGO entry to the database."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO legos (articul, name, part_count, all_parts, picture, series) VALUES (?, ?, ?, ?, ?, ?)",
                       (articul, name, part_count, all_parts, picture, series))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        messagebox.showerror("Помилка", f"LEGO з артикулом {articul} вже існує.")
        return False
    except sqlite3.Error as e:
        messagebox.showerror("Помилка Бази Даних", f"Виникла помилка: {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_lego_in_db(original_articul, new_articul, name, part_count, all_parts, picture, series):
    """Updates an existing LEGO entry in the database."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE legos SET articul = ?, name = ?, part_count = ?, all_parts = ?, picture = ?, series = ? WHERE articul = ?",
                       (new_articul, name, part_count, all_parts, picture, series, original_articul))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        messagebox.showerror("Помилка", f"Не вдалося оновити: LEGO з артикулом {new_articul} вже існує.")
        return False
    except sqlite3.Error as e:
        messagebox.showerror("Помилка Бази Даних", f"Виникла помилка під час оновлення: {e}")
        return False
    finally:
        if conn:
            conn.close()

def search_legos_in_db(articul=None, name=None, min_part_count=None, max_part_count=None, all_parts=None, series=None):
    """Searches for LEGO entries in the database based on criteria."""
    conn = None # Initialize conn to None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        query = "SELECT articul, name, part_count, all_parts, picture, series FROM legos WHERE 1=1"
        params = []

        if articul:
            query += " AND articul LIKE ?"
            params.append(f'%{articul}%')
        if name:
            query += " AND name LIKE ?"
            params.append(f'%{name}%')
        if min_part_count is not None:
            query += " AND part_count >= ?"
            params.append(min_part_count)
        if max_part_count is not None:
            query += " AND part_count <= ?"
            params.append(max_part_count)
        if all_parts is not None:
            query += " AND all_parts = ?"
            params.append(all_parts)
        if series:
            query += " AND series LIKE ?"
            params.append(f'%{series}%')

        cursor.execute(query, params)
        results = cursor.fetchall()
        return results

    except sqlite3.Error as e:
        messagebox.showerror("Помилка Бази Даних", f"Виникла помилка під час пошуку: {e}")
        return []
    finally:
        if conn:
            conn.close()

def delete_lego_from_db(articul):
    """Deletes a LEGO entry from the database based on articul."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM legos WHERE articul = ?", (articul,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        messagebox.showerror("Помилка Бази Даних", f"Виникла помилка під час видалення: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_all_series():
    """Fetches all unique series from the database."""
    conn = None # Initialize conn to None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT series FROM legos WHERE series IS NOT NULL AND series != ''")
        series_list = [row[0] for row in cursor.fetchall()]
        return sorted(series_list)
    except sqlite3.Error as e:
        print(f"Database error fetching series: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_image_from_url(image_url, size=(150, 150)):
    """Downloads an image from a URL and resizes it."""
    try:
        # Add a User-Agent header to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(image_url, stream=True, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes
        image_data = response.content
        img = Image.open(io.BytesIO(image_data))
        img = img.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing image from {image_url}: {e}")
        return None

class LegoApp:
    def __init__(self, master):
        self.master = master
        master.title("База Даних LEGO") # Translated title
        master.configure(bg=BG_COLOR) # Set main window background
        master.bind('<Return>', lambda event: self.search_lego()) # Bind Enter key to search

        # Configure style for themed widgets
        style = ttk.Style()
        style.theme_use('default') # Use the default theme as a base
        style.configure('TFrame', background=FRAME_COLOR) # Frame holding items in gallery
        # Configure general TLabel - used for labels inside item frames and potentially LabelFrame titles
        style.configure('TLabel', background=FRAME_COLOR, foreground=TEXT_COLOR)
        # Configure TLabelframe content area - used for the background of the item frames
        style.configure('TLabelframe', background=FRAME_COLOR, foreground=TEXT_COLOR) # Set content background to FRAME_COLOR
        # Configure the TLabelframe label (title text) explicitly
        style.configure('TLabelframe.Label', background=FRAME_COLOR, foreground=TEXT_COLOR) # Set LabelFrame title background to FRAME_COLOR

        style.configure('TButton', background=FRAME_COLOR, foreground=TEXT_COLOR)
        style.configure('Treeview', background=FRAME_COLOR, foreground=TEXT_COLOR, fieldbackground=FRAME_COLOR)
        style.configure('Treeview.Heading', background=FRAME_COLOR, foreground=TEXT_COLOR)
        style.map('TButton', background=[('active', ''), ('pressed', '')], foreground=[('active', ''), ('pressed', '')]) # Prevent default highlight color

        # We are no longer using specific DisplayItem styles as generic ones should work with labelwidget approach
        # style.configure('DisplayItem.TLabel', background=FRAME_COLOR, foreground=TEXT_COLOR)
        # style.configure('DisplayItem.TLabelframe', background=FRAME_COLOR, foreground=TEXT_COLOR)
        # style.configure('DisplayItem.TLabelframe.Label', background=BG_COLOR, foreground=TEXT_COLOR)

        self.editing_articul = None # To store the articul of the LEGO being edited

        # Add LEGO Section
        add_frame = tk.LabelFrame(master, text="Додати новий LEGO", bg=BG_COLOR, fg=TEXT_COLOR) # Translated title
        add_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        tk.Label(add_frame, text="Артикул:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, sticky=tk.W) # Translated label
        self.articul_entry = tk.Entry(add_frame)
        self.articul_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(add_frame, text="Назва:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=1, column=0, sticky=tk.W) # Translated label
        self.name_entry = tk.Entry(add_frame)
        self.name_entry.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(add_frame, text="Кількість деталей:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=2, column=0, sticky=tk.W) # Translated label
        self.part_count_entry = tk.Entry(add_frame)
        self.part_count_entry.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(add_frame, text="Всі деталі (0 або 1):", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=3, column=0, sticky=tk.W) # Translated label
        self.all_parts_entry = tk.Entry(add_frame)
        self.all_parts_entry.grid(row=3, column=1, padx=5, pady=2)

        tk.Label(add_frame, text="URL зображення (Необов'язково):", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=4, column=0, sticky=tk.W) # Translated label
        self.picture_entry = tk.Entry(add_frame)
        self.picture_entry.grid(row=4, column=1, padx=5, pady=2)

        tk.Label(add_frame, text="Серія:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=5, column=0, sticky=tk.W) # Translated label
        self.series_combobox = ttk.Combobox(add_frame, values=get_all_series())
        self.series_combobox.grid(row=5, column=1, padx=5, pady=2)
        self.series_combobox.set('') # Set initial value to empty

        self.add_button = tk.Button(add_frame, text="Додати LEGO", command=self.add_lego, bg=FRAME_COLOR, fg=TEXT_COLOR) # Translated button text
        self.add_button.grid(row=6, column=0, columnspan=2, pady=10)

        # Search LEGO Section
        search_frame = tk.LabelFrame(master, text="Пошук LEGO", bg=BG_COLOR, fg=TEXT_COLOR) # Translated title
        search_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        tk.Label(search_frame, text="Артикул:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, sticky=tk.W) # Translated label
        self.search_articul_entry = tk.Entry(search_frame)
        self.search_articul_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(search_frame, text="Назва:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=1, column=0, sticky=tk.W) # Translated label
        self.search_name_entry = tk.Entry(search_frame)
        self.search_name_entry.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(search_frame, text="Мінімальна кількість деталей:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=2, column=0, sticky=tk.W) # Translated label
        self.search_min_part_count_entry = tk.Entry(search_frame)
        self.search_min_part_count_entry.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(search_frame, text="Максимальна кількість деталей:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=3, column=0, sticky=tk.W) # Translated label
        self.search_max_part_count_entry = tk.Entry(search_frame)
        self.search_max_part_count_entry.grid(row=3, column=1, padx=5, pady=2)

        tk.Label(search_frame, text="Всі деталі (0 або 1):", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=4, column=0, sticky=tk.W) # Translated label
        self.search_all_parts_entry = tk.Entry(search_frame)
        self.search_all_parts_entry.grid(row=4, column=1, padx=5, pady=2)

        tk.Label(search_frame, text="Серія:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=5, column=0, sticky=tk.W) # Translated label
        self.search_series_combobox = ttk.Combobox(search_frame, values=get_all_series())
        self.search_series_combobox.grid(row=5, column=1, padx=5, pady=2)
        self.search_series_combobox.set('') # Set initial value to empty

        self.search_button = tk.Button(search_frame, text="Пошук", command=self.search_lego, bg=FRAME_COLOR, fg=TEXT_COLOR) # Translated button text
        self.search_button.grid(row=6, column=0, columnspan=2, pady=10)

        # Search Results Section
        results_frame = tk.LabelFrame(master, text="Результати Пошуку", bg=BG_COLOR, fg=TEXT_COLOR) # Translated title
        results_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.results_tree = ttk.Treeview(results_frame, columns=("Артикул", "Назва", "Кількість деталей", "Всі деталі", "Зображення", "Серія"), show="headings") # Translated column names
        self.results_tree.heading("Артикул", text="Артикул") # Translated heading
        self.results_tree.heading("Назва", text="Назва") # Translated heading
        self.results_tree.heading("Кількість деталей", text="Кількість деталей") # Translated heading
        self.results_tree.heading("Всі деталі", text="Всі деталі") # Translated heading
        self.results_tree.heading("Зображення", text="Зображення") # Translated heading
        self.results_tree.heading("Серія", text="Серія") # Translated heading

        # Optional: Add scrollbars to the Treeview
        scrollbar_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(xscrollcommand=scrollbar_x.set)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.results_tree.pack(expand=True, fill="both", padx=5, pady=5)

        # Bind double-click event
        self.results_tree.bind("<Double-1>", self.on_item_double_click)

        # Action Buttons
        action_button_frame = tk.Frame(results_frame, bg=BG_COLOR)
        action_button_frame.pack(pady=5)

        self.edit_button = tk.Button(action_button_frame, text="Редагувати обране", command=self.edit_selected_lego, bg=FRAME_COLOR, fg=TEXT_COLOR) # Translated button text
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = tk.Button(action_button_frame, text="Видалити обране", command=self.delete_selected_lego, bg=FRAME_COLOR, fg=TEXT_COLOR) # Translated button text
        self.delete_button.pack(side=tk.LEFT, padx=5)

        # Display Mode Button
        self.display_button = tk.Button(master, text="Показати галерею", command=self.show_display_mode, bg=FRAME_COLOR, fg=TEXT_COLOR, font=("TkDefaultFont", 14, "bold")) # Translated button text, bold and bigger
        self.display_button.grid(row=2, column=0, pady=10)

        # Statistics Button
        self.stats_button = tk.Button(master, text="Показати статистику", command=self.show_statistics, bg=FRAME_COLOR, fg=TEXT_COLOR, font=("TkDefaultFont", 14, "bold")) # Translated button text, bold and bigger
        self.stats_button.grid(row=2, column=1, pady=10)

    def add_lego(self):
        articul = self.articul_entry.get().strip()
        name = self.name_entry.get().strip()
        part_count_str = self.part_count_entry.get().strip()
        all_parts_str = self.all_parts_entry.get().strip()
        picture = self.picture_entry.get().strip()
        series = self.series_combobox.get().strip() # Get series from combobox

        # Basic validation
        if not articul or not name:
            messagebox.showwarning("Відсутня інформація", "Артикул та Назва є обов'язковими.") # Translated message
            return

        try:
            part_count = int(part_count_str) if part_count_str else None
        except ValueError:
            messagebox.showwarning("Невірне введення", "Кількість деталей має бути цілим числом.") # Translated message
            return

        try:
            # all_parts should be 0 or 1, or empty or 'N/A'
            if all_parts_str == "" or all_parts_str.upper() == "N/A" or all_parts_str.upper() == "НІ" or all_parts_str.upper() == "ТАК":
                all_parts = None
            else:
                all_parts = int(all_parts_str)
                if all_parts not in [0, 1]:
                    raise ValueError("Невірне значення для 'Всі деталі'") # Translated error
        except ValueError as e:
            messagebox.showwarning("Невірне введення", f"'Всі деталі' має бути 0, 1 або N/A ({e})") # Translated message
            return

        if self.editing_articul:
            # We are in edit mode, perform update
            if update_lego_in_db(self.editing_articul, articul, name, part_count, all_parts, picture, series):
                messagebox.showinfo("Успіх", "LEGO успішно оновлено!") # Translated message
                self.clear_add_form()
                self.editing_articul = None
                self.add_button.config(text="Додати LEGO", command=self.add_lego, bg=FRAME_COLOR, fg=TEXT_COLOR) # Update button color and text
                self.update_series_comboboxes() # Update series dropdowns
                self.search_lego() # Refresh results after update
        else:
            # We are in add mode, perform insert
            if add_lego_to_db(articul, name, part_count, all_parts, picture, series):
                messagebox.showinfo("Успіх", "LEGO успішно додано!") # Translated message
                self.clear_add_form()
                self.update_series_comboboxes() # Update series dropdowns

    def clear_add_form(self):
        """Clears the input fields in the Add LEGO section."""
        self.articul_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.part_count_entry.delete(0, tk.END)
        self.all_parts_entry.delete(0, tk.END)
        self.picture_entry.delete(0, tk.END)
        self.series_combobox.set('') # Clear combobox

    def search_lego(self):
        articul = self.search_articul_entry.get().strip()
        name = self.search_name_entry.get().strip()
        min_part_count_str = self.search_min_part_count_entry.get().strip()
        max_part_count_str = self.search_max_part_count_entry.get().strip()
        all_parts_str = self.search_all_parts_entry.get().strip()
        series = self.search_series_combobox.get().strip() # Get series from search combobox

        min_part_count = None
        max_part_count = None
        all_parts = None

        try:
            if min_part_count_str:
                min_part_count = int(min_part_count_str)
            if max_part_count_str:
                max_part_count = int(max_part_count_str)
        except ValueError:
            messagebox.showwarning("Невірне введення", "Значення кількості деталей має бути цілим числом.") # Translated message
            return

        try:
            if all_parts_str:
                 all_parts = int(all_parts_str)
                 if all_parts not in [0, 1]:
                    raise ValueError("Невірне значення для 'Всі деталі'") # Translated error
        except ValueError:
             messagebox.showwarning("Невірне введення", "'Всі деталі' має бути 0 або 1.") # Translated message
             return

        results = search_legos_in_db(articul=articul if articul else None,
                                   name=name if name else None,
                                   min_part_count=min_part_count,
                                   max_part_count=max_part_count,
                                   all_parts=all_parts,
                                   series=series if series else None)

        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Display new results
        for row in results:
            # Ensure the row has 6 elements (articul, name, part_count, all_parts, picture, series)
            # In case older entries without series are retrieved
            padded_row = list(row) + [None] * (6 - len(row))
            # Replace all_parts (index 3) with 'Так'/'Ні'/'N/A'
            if padded_row[3] == 1:
                padded_row[3] = 'Так'
            elif padded_row[3] == 0:
                padded_row[3] = 'Ні'
            else:
                padded_row[3] = 'N/A'
            self.results_tree.insert("", tk.END, values=padded_row)

    def delete_selected_lego(self):
        selected_items = self.results_tree.selection()
        if not selected_items:
            messagebox.showwarning("Немає вибору", "Будь ласка, виберіть один або кілька LEGO для видалення.") # Translated message
            return

        # Ask for confirmation
        confirm = messagebox.askyesno("Підтвердження видалення", f"Ви впевнені, що хочете видалити {len(selected_items)} обраних LEGO?") # Translated message
        if not confirm:
            return

        for item in selected_items:
            # Get the articul from the selected row (assuming articul is the first column)
            articul = self.results_tree.item(item, "values")[
                0
            ]  # Ensure articul is correctly retrieved
            if delete_lego_from_db(articul):
                self.results_tree.delete(item) # Remove from Treeview on successful deletion

        messagebox.showinfo("Видалення завершено", "Вибрані LEGO видалено.") # Translated message
        self.update_series_comboboxes() # Update series dropdowns after deletion


    def on_item_double_click(self, event):
        """Handles double-click on an item in the results tree."""
        selected_item = self.results_tree.focus() # Get the item under the mouse
        if not selected_item:
            return

        values = self.results_tree.item(selected_item, "values")
        if not values:
            return

        self.show_lego_details(values)

    def show_lego_details(self, values):
        """Displays detailed information about a selected LEGO in a new window."""
        articul, name, part_count, all_parts, picture, series = values

        details_window = tk.Toplevel(self.master)
        details_window.title(f"Деталі: {name} ({articul})") # Translated title
        details_window.geometry("400x400")
        details_window.configure(bg=BG_COLOR) # Set background for details window

        # Use a frame for better organization
        details_frame = ttk.Frame(details_window, padding="10")
        details_frame.pack(expand=True, fill="both")

        # Display information
        ttk.Label(details_frame, text=f"Артикул: {articul}").pack(anchor=tk.W, pady=2) # Translated label
        ttk.Label(details_frame, text=f"Назва: {name}").pack(anchor=tk.W, pady=2) # Translated label
        ttk.Label(details_frame, text=f"Серія: {series if series else 'N/A'}").pack(anchor=tk.W, pady=2) # Translated label
        ttk.Label(details_frame, text=f"Кількість деталей: {part_count if part_count is not None else 'N/A'}").pack(anchor=tk.W, pady=2) # Translated label
        ttk.Label(details_frame, text=f"Всі деталі: {'Так' if all_parts == 1 else 'Ні' if all_parts == 0 else 'N/A'}").pack(anchor=tk.W, pady=2) # Translated label

        # Display picture if available
        if picture:
            img = get_image_from_url(picture, size=(350, 250))
            if img:
                img_label = ttk.Label(details_frame, image=img) # Changed to ttk.Label
                img_label.image = img # Keep a reference
                details_window.image_reference = img # Store reference in window
                img_label.pack(pady=10)
            else:
                ttk.Label(details_frame, text="Помилка завантаження зображення", wraplength=350).pack(pady=10) # Translated message
        else:
            ttk.Label(details_frame, text="Зображення відсутнє", wraplength=350).pack(pady=10) # Translated message


    def edit_selected_lego(self):
        selected_items = self.results_tree.selection()
        if len(selected_items) != 1:
            messagebox.showwarning("Невірний вибір", "Будь ласка, виберіть рівно один LEGO для редагування.") # Translated message
            return

        selected_item = selected_items[0]
        values = self.results_tree.item(selected_item, "values")

        # Populate the add form with the selected LEGO's data
        self.clear_add_form()
        self.articul_entry.insert(0, values[0])
        self.name_entry.insert(0, values[1])
        if values[2] is not None: # Check if part_count is not None
            self.part_count_entry.insert(0, values[2])
        if values[3] is not None: # Check if all_parts is not None
            self.all_parts_entry.insert(0, values[3])
        if values[4] is not None: # Check if picture is not None
            self.picture_entry.insert(0, values[4])
        if len(values) > 5 and values[5] is not None: # Check if series exists and is not None
             self.series_combobox.set(values[5]) # Set series combobox value

        # Set the editing state and change the button text/command
        self.editing_articul = values[0]  # Store the original articul
        self.add_button.config(text="Оновити LEGO", command=self.add_lego, bg=FRAME_COLOR, fg=TEXT_COLOR) # Update button color and text

    def update_series_comboboxes(self):
        """Updates the values in the series comboboxes."""
        all_series = get_all_series()
        self.series_combobox['values'] = all_series
        self.search_series_combobox['values'] = all_series


    def show_display_mode(self):
        # Create a new top-level window for the display mode
        display_window = tk.Toplevel(self.master)
        display_window.title("Галерея LEGO") # Translated title
        display_window.geometry("900x800") # Set a larger default size
        display_window.configure(bg=BG_COLOR) # Set background for display window

        # Create a Canvas and attach scrollbars
        canvas = tk.Canvas(display_window, bg=BG_COLOR, highlightthickness=0) # Ensure canvas background and remove border
        canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar_y = ttk.Scrollbar(display_window, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ttk.Scrollbar(display_window, orient=tk.HORIZONTAL, command=canvas.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        canvas.configure(xscrollcommand=scrollbar_x.set)

        # Create a frame inside the canvas to hold the grid items
        # Use FRAME_COLOR for the background of the frame holding the items
        display_frame = ttk.Frame(canvas, padding="10", style='TFrame') # Explicitly use TFrame style to ensure background color

        # Add the frame to the canvas
        canvas.create_window((0, 0), window=display_frame, anchor="nw")

        # Update scrollregion when the frame size changes
        display_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion = canvas.bbox("all")))

        # Configure canvas and window to resize
        display_window.grid_columnconfigure(0, weight=1)
        display_window.grid_rowconfigure(0, weight=1)

        # Fetch all LEGOs
        all_legos = search_legos_in_db() # Get all legos by searching with no filters

        # Configure grid columns to expand within the display_frame
        max_cols = 4 # Number of columns in the grid
        for i in range(max_cols):
            display_frame.grid_columnconfigure(i, weight=1)

        row_num = 0
        col_num = 0

        # Store image references to prevent garbage collection
        display_window.image_references = []

        for lego in all_legos:
            articul, name, part_count, all_parts, picture, series = lego

            # Create the ttk.LabelFrame for the item
            # The title styling is handled by the TLabelframe.Label style
            item_frame = ttk.LabelFrame(display_frame, text=f"{name} ({articul})") # Reverted to using text parameter and removed labelwidget
            item_frame.grid(row=row_num, column=col_num, padx=5, pady=5, sticky="nsew")

            # Display picture
            if picture:
                img = get_image_from_url(picture, size=(200, 150)) # Increased image size
                if img:
                    # Use the generic TLabel style for image labels within the item frame
                    img_label = ttk.Label(item_frame, image=img) # Removed style
                    img_label.image = img # Keep a reference
                    display_window.image_references.append(img) # Store reference in window
                    img_label.pack(pady=2)
                else:
                    # Use the generic TLabel style for error labels within the item frame
                    ttk.Label(item_frame, text="Помилка завантаження зображення", wraplength=180).pack(pady=2) # Removed style and translated message
            else:
                # Use the generic TLabel style for "no image" labels within the item frame
                ttk.Label(item_frame, text="Зображення відсутнє", wraplength=180).pack(pady=2) # Removed style, changed to ttk.Label and translated

            # Display other information - Use the generic TLabel style for text labels within the item frame
            ttk.Label(item_frame, text=f"Серія: {series if series else 'N/A'}").pack(anchor=tk.W, pady=2) # Removed style, Changed to ttk.Label and translated
            ttk.Label(item_frame, text=f"Деталі: {part_count if part_count is not None else 'N/A'}").pack(anchor=tk.W, pady=2) # Removed style, Changed to ttk.Label and translated
            # Add all_parts as Так/Ні/N/A
            if all_parts == 1:
                all_parts_str = 'Так'
            elif all_parts == 0:
                all_parts_str = 'Ні'
            else:
                all_parts_str = 'N/A'
            ttk.Label(item_frame, text=f"Всі деталі: {all_parts_str}").pack(anchor=tk.W, pady=2)

            col_num += 1
            if col_num >= max_cols:
                col_num = 0
                row_num += 1

        # Mousewheel scrolling (Windows and Linux)
        def _on_mousewheel(event):
            if event.num == 5 or event.delta == -120:
                canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta == 120:
                canvas.yview_scroll(-1, "units")

        # Windows and MacOS
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        # Linux (event.num 4=up, 5=down)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    def show_statistics(self):
        """Displays database statistics in a new window."""
        conn = None # Initialize conn to None
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()

            # Get total count
            cursor.execute("SELECT COUNT(*) FROM legos")
            total_count = cursor.fetchone()[0]

            # Get total parts (only for entries with part_count)
            cursor.execute("SELECT SUM(part_count) FROM legos WHERE part_count IS NOT NULL")
            total_parts = cursor.fetchone()[0]
            if total_parts is None:
                total_parts = 0

            # Get count by series
            cursor.execute("SELECT series, COUNT(*) FROM legos GROUP BY series HAVING series IS NOT NULL AND series != '' ORDER BY series")
            series_counts = cursor.fetchall()

            # Create statistics window
            stats_window = tk.Toplevel(self.master)
            stats_window.title("Статистика Бази Даних") # Translated title
            stats_window.geometry("300x400")
            stats_window.configure(bg=BG_COLOR) # Set background for stats window

            stats_frame = ttk.Frame(stats_window, padding="10")
            stats_frame.pack(expand=True, fill="both")

            ttk.Label(stats_frame, text="Статистика Бази Даних", font=('TkDefaultFont', 14, 'bold')).pack(pady=5) # Translated title
            ttk.Label(stats_frame, text=f"Загальна кількість наборів LEGO: {total_count}").pack(anchor=tk.W, pady=2) # Translated label
            ttk.Label(stats_frame, text=f"Загальна кількість деталей (орієнтовно): {total_parts}").pack(anchor=tk.W, pady=2) # Translated label

            if series_counts:
                ttk.Label(stats_frame, text="\nНабори за серіями:", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=5) # Translated label
                for series, count in series_counts:
                    ttk.Label(stats_frame, text=f"{series}: {count}").pack(anchor=tk.W, pady=1)

        except sqlite3.Error as e:
            messagebox.showerror("Помилка Бази Даних", f"Виникла помилка під час отримання статистики: {e}") # Translated message
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    initialize_database()

    root = tk.Tk()
    app = LegoApp(root)
    root.mainloop() 
