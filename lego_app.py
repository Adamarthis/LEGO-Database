import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import requests
import io
import os

# TODO:
# In statistics add the display mode for all LEGOS of the same series
# Optimize loading of the display mode

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
                picture TEXT,
                series TEXT,
                favorite INTEGER DEFAULT 0 -- 0 for False, 1 for True
            )
        ''')

        # Check if 'series' column exists, add if not
        cursor.execute("PRAGMA table_info(legos)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'series' not in columns:
            cursor.execute("ALTER TABLE legos ADD COLUMN series TEXT")
            print("Added 'series' column to the database.")
        if 'favorite' not in columns:
            cursor.execute("ALTER TABLE legos ADD COLUMN favorite INTEGER DEFAULT 0")
            print("Added 'favorite' column to the database.")

        conn.commit()
        print("Database initialized successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def add_lego_to_db(articul, name, part_count, all_parts, picture, series, favorite):
    """Adds a new LEGO entry to the database."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO legos (articul, name, part_count, all_parts, picture, series, favorite) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (articul, name, part_count, all_parts, picture, series, favorite))
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

def update_lego_in_db(original_articul, new_articul, name, part_count, all_parts, picture, series, favorite):
    """Updates an existing LEGO entry in the database."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE legos SET articul = ?, name = ?, part_count = ?, all_parts = ?, picture = ?, series = ?, favorite = ? WHERE articul = ?",
                       (new_articul, name, part_count, all_parts, picture, series, favorite, original_articul))
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

def search_legos_in_db(articul=None, name=None, min_part_count=None, max_part_count=None, all_parts=None, series=None, favorite_only=None):
    """Searches for LEGO entries in the database based on criteria."""
    conn = None # Initialize conn to None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        query = "SELECT articul, name, part_count, all_parts, picture, series, favorite FROM legos WHERE 1=1"
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
        if favorite_only is not None: # Can be True (1) or False (0)
            query += " AND favorite = ?"
            params.append(1 if favorite_only else 0)

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

        # Style for favorite items in display mode
        FAVORITE_BG_COLOR = '#fff5cc' # Light gold/yellow for favorites
        style.configure('Favorite.TLabelframe', background=FAVORITE_BG_COLOR, foreground=TEXT_COLOR)
        style.configure('Favorite.TLabelframe.Label', background=FAVORITE_BG_COLOR, foreground=TEXT_COLOR)
        style.configure('Favorite.TLabel', background=FAVORITE_BG_COLOR, foreground=TEXT_COLOR) # For labels inside a favorite frame

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

        tk.Label(add_frame, text="Улюблене:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=6, column=0, sticky=tk.W) # Favorite label
        self.favorite_var = tk.IntVar()
        self.favorite_checkbutton = tk.Checkbutton(add_frame, variable=self.favorite_var, bg=BG_COLOR)
        self.favorite_checkbutton.grid(row=6, column=1, padx=5, pady=2, sticky=tk.W)

        self.add_button = tk.Button(add_frame, text="Додати LEGO", command=self.add_lego, bg=FRAME_COLOR, fg=TEXT_COLOR, font=("TkDefaultFont", 10, "bold")) # Translated button text, bold
        self.add_button.grid(row=7, column=0, pady=10, padx=5, sticky=tk.E) # Adjusted row

        self.clear_add_form_button = tk.Button(add_frame, text="Очистити форму", command=self.clear_add_form, bg=FRAME_COLOR, fg=TEXT_COLOR)
        self.clear_add_form_button.grid(row=7, column=1, pady=10, padx=5, sticky=tk.W) # Adjusted row

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

        tk.Label(search_frame, text="Тільки улюблені:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=6, column=0, sticky=tk.W)
        self.search_favorite_only_var = tk.IntVar()
        self.search_favorite_only_checkbutton = tk.Checkbutton(search_frame, variable=self.search_favorite_only_var, bg=BG_COLOR)
        self.search_favorite_only_checkbutton.grid(row=6, column=1, padx=5, pady=2, sticky=tk.W)

        self.search_button = tk.Button(search_frame, text="Пошук", command=self.search_lego, bg=FRAME_COLOR, fg=TEXT_COLOR, font=("TkDefaultFont", 10, "bold")) # Translated button text, bold
        self.search_button.grid(row=7, column=0, pady=10, padx=5, sticky=tk.E) # Adjusted row

        self.clear_search_button = tk.Button(search_frame, text="Очистити пошук", command=self.clear_search_fields, bg=FRAME_COLOR, fg=TEXT_COLOR)
        self.clear_search_button.grid(row=7, column=1, pady=10, padx=5, sticky=tk.W) # Adjusted row

        # Search Results Section
        results_frame = tk.LabelFrame(master, text="Результати Пошуку", bg=BG_COLOR, fg=TEXT_COLOR) # Translated title
        results_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.results_tree = ttk.Treeview(results_frame, columns=("Артикул", "Назва", "Кількість деталей", "Всі деталі", "Зображення", "Серія", "Улюблене"), show="headings") # Translated column names, added Favorite
        self.results_tree.heading("Артикул", text="Артикул") # Translated heading
        self.results_tree.heading("Назва", text="Назва") # Translated heading
        self.results_tree.heading("Кількість деталей", text="Кількість деталей") # Translated heading
        self.results_tree.heading("Всі деталі", text="Всі деталі") # Translated heading
        self.results_tree.heading("Зображення", text="Зображення") # Translated heading
        self.results_tree.heading("Серія", text="Серія") # Translated heading
        self.results_tree.heading("Улюблене", text="Улюблене") # Translated heading for Favorite

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

        self.clear_results_button = tk.Button(action_button_frame, text="Очистити результати", command=self.clear_search_results, bg=FRAME_COLOR, fg=TEXT_COLOR)
        self.clear_results_button.pack(side=tk.LEFT, padx=5)

        self.toggle_favorite_button = tk.Button(action_button_frame, text="Змінити статус Улюбленого", command=self.toggle_selected_favorite, bg=FRAME_COLOR, fg=TEXT_COLOR)
        self.toggle_favorite_button.pack(side=tk.LEFT, padx=5)

        # Display Mode Button
        self.display_button = tk.Button(master, text="Показати галерею", command=self.show_display_mode, bg=FRAME_COLOR, fg=TEXT_COLOR, font=("TkDefaultFont", 14, "bold")) # Translated button text, bold and bigger
        self.display_button.grid(row=2, column=0, pady=10)

        # Statistics Button
        self.stats_button = tk.Button(master, text="Показати статистику", command=self.show_statistics, bg=FRAME_COLOR, fg=TEXT_COLOR, font=("TkDefaultFont", 14, "bold")) # Translated button text, bold and bigger
        self.stats_button.grid(row=2, column=1, pady=10)

        self.favorite_display_button = tk.Button(master, text="Показати улюблені", command=self.show_favorite_display_mode, bg=FRAME_COLOR, fg=TEXT_COLOR, font=("TkDefaultFont", 14, "bold"))
        self.favorite_display_button.grid(row=3, column=0, columnspan=2, pady=10)

    def add_lego(self):
        articul = self.articul_entry.get().strip()
        name = self.name_entry.get().strip()
        part_count_str = self.part_count_entry.get().strip()
        all_parts_str = self.all_parts_entry.get().strip()
        picture = self.picture_entry.get().strip()
        series = self.series_combobox.get().strip() # Get series from combobox
        favorite = self.favorite_var.get() # Get favorite status

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
            if update_lego_in_db(self.editing_articul, articul, name, part_count, all_parts, picture, series, favorite):
                messagebox.showinfo("Успіх", "LEGO успішно оновлено!") # Translated message
                self.clear_add_form()
                self.editing_articul = None
                self.add_button.config(text="Додати LEGO", command=self.add_lego, bg=FRAME_COLOR, fg=TEXT_COLOR) # Update button color and text
                self.update_series_comboboxes() # Update series dropdowns
                self.search_lego() # Refresh results after update
        else:
            # We are in add mode, perform insert
            if add_lego_to_db(articul, name, part_count, all_parts, picture, series, favorite):
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
        self.favorite_var.set(0) # Clear favorite checkbox

    def clear_search_fields(self):
        """Clears the input fields in the Search LEGO section."""
        self.search_articul_entry.delete(0, tk.END)
        self.search_name_entry.delete(0, tk.END)
        self.search_min_part_count_entry.delete(0, tk.END)
        self.search_max_part_count_entry.delete(0, tk.END)
        self.search_all_parts_entry.delete(0, tk.END)
        self.search_series_combobox.set('')
        self.search_favorite_only_var.set(0)

    def search_lego(self):
        articul = self.search_articul_entry.get().strip()
        name = self.search_name_entry.get().strip()
        min_part_count_str = self.search_min_part_count_entry.get().strip()
        max_part_count_str = self.search_max_part_count_entry.get().strip()
        all_parts_str = self.search_all_parts_entry.get().strip()
        series = self.search_series_combobox.get().strip() # Get series from search combobox
        favorite_only = self.search_favorite_only_var.get()

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
                                   series=series if series else None,
                                   favorite_only=favorite_only)

        # Clear previous results
        self.clear_search_results()

        # Display new results
        for row in results:
            # Ensure the row has 7 elements (articul, name, part_count, all_parts, picture, series, favorite)
            padded_row = list(row) + [None] * (7 - len(row))
            # Replace all_parts (index 3) with 'Так'/'Ні'/'N/A'
            if padded_row[3] == 1:
                padded_row[3] = 'Так'
            elif padded_row[3] == 0:
                padded_row[3] = 'Ні'
            else:
                padded_row[3] = 'N/A'
            # Replace favorite (index 6) with 'Так'/'Ні'
            if padded_row[6] == 1:
                padded_row[6] = 'Так'
            elif padded_row[6] == 0:
                padded_row[6] = 'Ні'
            else: # Should not happen with DEFAULT 0, but good for robustness
                padded_row[6] = 'Ні'
            self.results_tree.insert("", tk.END, values=padded_row)

    def clear_search_results(self):
        """Clears the search results from the Treeview."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

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

    def toggle_selected_favorite(self):
        """Toggles the favorite status of the selected LEGO items."""
        selected_items = self.results_tree.selection()
        if not selected_items:
            messagebox.showwarning("Немає вибору", "Будь ласка, виберіть один або кілька LEGO для зміни статусу улюбленого.")
            return

        updated_count = 0
        for item_id in selected_items:
            values = self.results_tree.item(item_id, "values")
            if not values or len(values) < 7: # Ensure favorite status is present
                continue

            articul = values[0]
            current_favorite_text = values[6] # 'Так' or 'Ні'
            new_favorite_status = 1 if current_favorite_text == 'Ні' else 0
            
            name = values[1]
            try:
                part_count = int(values[2]) if values[2] and values[2] != 'N/A' else None
            except ValueError:
                part_count = None
            all_parts_db_val = 1 if values[3] == 'Так' else 0 if values[3] == 'Ні' else None # Convert 'Так'/'Ні' back to 1/0
            picture = values[4] if values[4] and values[4] != 'N/A' else '' 
            series = values[5] if values[5] and values[5] != 'N/A' else ''

            if update_lego_in_db(articul, articul, name, part_count, all_parts_db_val, picture, series, new_favorite_status):
                updated_count += 1
            else:
                messagebox.showerror("Помилка", f"Не вдалося оновити статус для {articul}")

        if updated_count > 0:
            messagebox.showinfo("Успіх", f"Статус улюбленого оновлено для {updated_count} LEGO.")
            self.search_lego() 
        elif not selected_items: 
            pass 
        else: 
            messagebox.showwarning("Оновлення не відбулось", "Не вдалося оновити статус улюбленого для обраних LEGO.")

    def on_item_double_click(self, event):
        """Handles double-click on an item in the results tree."""
        selected_item = self.results_tree.focus() 
        if not selected_item:
            return

        values = self.results_tree.item(selected_item, "values")
        if not values:
            return

        self.show_lego_details(values)

    def show_lego_details(self, values):
        """Displays detailed information about a selected LEGO in a new window."""
        articul, name, part_count, all_parts_text, picture, series, favorite_text = (list(values) + [None]*7)[:7]

        details_window = tk.Toplevel(self.master)
        details_window.title(f"Деталі: {name} ({articul})") 
        details_window.geometry("400x400")
        details_window.configure(bg=BG_COLOR) 

        details_frame = ttk.Frame(details_window, padding="10")
        details_frame.pack(expand=True, fill="both")

        ttk.Label(details_frame, text=f"Артикул: {articul}").pack(anchor=tk.W, pady=2) 
        ttk.Label(details_frame, text=f"Назва: {name}").pack(anchor=tk.W, pady=2) 
        ttk.Label(details_frame, text=f"Серія: {series if series else 'N/A'}").pack(anchor=tk.W, pady=2) 
        ttk.Label(details_frame, text=f"Кількість деталей: {part_count if part_count is not None else 'N/A'}").pack(anchor=tk.W, pady=2) 
        ttk.Label(details_frame, text=f"Всі деталі: {all_parts_text if all_parts_text else 'N/A'}").pack(anchor=tk.W, pady=2) # Display as is from tree
        ttk.Label(details_frame, text=f"Улюблене: {favorite_text if favorite_text else 'Ні'}").pack(anchor=tk.W, pady=2) # Display favorite status

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
        if len(values) > 6 and values[6] is not None: # Check if favorite exists
            self.favorite_var.set(values[6])
        else:
            self.favorite_var.set(0) # Default to not favorite if not present

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
            articul, name, part_count, all_parts, picture, series, favorite = lego # Unpack favorite status

            item_frame_style = 'Favorite.TLabelframe' if favorite == 1 else 'TLabelframe'
            label_style_to_use = 'Favorite.TLabel' if favorite == 1 else 'TLabel' # Choose label style

            item_frame = ttk.LabelFrame(display_frame, text=f"{name} ({articul})", style=item_frame_style)
            item_frame.grid(row=row_num, column=col_num, padx=5, pady=5, sticky="nsew")

            if picture:
                img = get_image_from_url(picture, size=(200, 150)) 
                if img:
                    img_label = ttk.Label(item_frame, image=img, style=label_style_to_use) 
                    img_label.image = img 
                    display_window.image_references.append(img) 
                    img_label.pack(pady=2)
                else:
                    ttk.Label(item_frame, text="Помилка завантаження зображення", wraplength=180, style=label_style_to_use).pack(pady=2) 
            else:
                ttk.Label(item_frame, text="Зображення відсутнє", wraplength=180, style=label_style_to_use).pack(pady=2) 

            ttk.Label(item_frame, text=f"Серія: {series if series else 'N/A'}", style=label_style_to_use).pack(anchor=tk.W, pady=2) 
            ttk.Label(item_frame, text=f"Деталі: {part_count if part_count is not None else 'N/A'}", style=label_style_to_use).pack(anchor=tk.W, pady=2) 
            if all_parts == 1:
                all_parts_str = 'Так'
            elif all_parts == 0:
                all_parts_str = 'Ні'
            else:
                all_parts_str = 'N/A'
            ttk.Label(item_frame, text=f"Всі деталі: {all_parts_str}", style=label_style_to_use).pack(anchor=tk.W, pady=2)

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

    def show_favorite_display_mode(self):
        """Displays favorite LEGOs in a gallery view."""
        display_window = tk.Toplevel(self.master)
        display_window.title("Галерея Улюблених LEGO") 
        display_window.geometry("900x800") 
        display_window.configure(bg=BG_COLOR) 

        canvas = tk.Canvas(display_window, bg=BG_COLOR, highlightthickness=0) 
        canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar_y = ttk.Scrollbar(display_window, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ttk.Scrollbar(display_window, orient=tk.HORIZONTAL, command=canvas.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        canvas.configure(xscrollcommand=scrollbar_x.set)

        display_frame = ttk.Frame(canvas, padding="10", style='TFrame') 
        canvas.create_window((0, 0), window=display_frame, anchor="nw")
        display_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion = canvas.bbox("all")))

        display_window.grid_columnconfigure(0, weight=1)
        display_window.grid_rowconfigure(0, weight=1)

        favorite_legos = search_legos_in_db(favorite_only=True) 

        max_cols = 4 
        for i in range(max_cols):
            display_frame.grid_columnconfigure(i, weight=1)

        row_num = 0
        col_num = 0
        display_window.image_references = []

        for lego_data in favorite_legos:
            articul, name, part_count, all_parts, picture, series, _ = lego_data # Favorite status not directly needed for display item content here

            item_frame = ttk.LabelFrame(display_frame, text=f"{name} ({articul})")
            item_frame.grid(row=row_num, column=col_num, padx=5, pady=5, sticky="nsew")

            if picture:
                img = get_image_from_url(picture, size=(200, 150)) 
                if img:
                    img_label = ttk.Label(item_frame, image=img) 
                    img_label.image = img 
                    display_window.image_references.append(img) 
                    img_label.pack(pady=2)
                else:
                    ttk.Label(item_frame, text="Помилка завантаження зображення", wraplength=180).pack(pady=2) 
            else:
                ttk.Label(item_frame, text="Зображення відсутнє", wraplength=180).pack(pady=2) 

            ttk.Label(item_frame, text=f"Серія: {series if series else 'N/A'}").pack(anchor=tk.W, pady=2) 
            ttk.Label(item_frame, text=f"Деталі: {part_count if part_count is not None else 'N/A'}").pack(anchor=tk.W, pady=2) 
            all_parts_str = 'Так' if all_parts == 1 else 'Ні' if all_parts == 0 else 'N/A'
            ttk.Label(item_frame, text=f"Всі деталі: {all_parts_str}").pack(anchor=tk.W, pady=2)
            # Favorite status is implied by being in this view, but can be added if needed.

            col_num += 1
            if col_num >= max_cols:
                col_num = 0
                row_num += 1

        def _on_mousewheel_fav(event):
            if event.num == 5 or event.delta == -120:
                canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta == 120:
                canvas.yview_scroll(-1, "units")

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"), add='+') # Use add='+ to avoid conflict with main window
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"), add='+')
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"), add='+')

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
