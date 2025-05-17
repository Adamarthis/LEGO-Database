# LEGO Database Application

This is a simple desktop application built with Python and Tkinter to manage a personal LEGO collection database.

## Features

*   **Add LEGO Sets:** Easily add new LEGO sets to your database with details like Articul, Name, Part Count, whether you have all parts, a picture URL, and Series.
*   **Search Functionality:** Search your collection based on various criteria.
*   **Edit and Delete Entries:** Modify or remove existing LEGO entries.
*   **Gallery View:** Visualize your collection in a grid layout, displaying images downloaded from provided URLs.
*   **Statistics:** View basic statistics about your collection, including total sets and counts per series.
*   **Ukrainian Localization:** The user interface is translated into Ukrainian.

## Requirements

*   Python 3.x
*   Tkinter (usually included with Python)
*   Pillow (PIL) library
*   Requests library

## Installation

1.  Make sure you have Python 3.x installed.
2.  Install the required Python libraries using pip:

    ```bash
    pip install Pillow requests
    ```

## How to Run

1.  Save the application code as `lego_app.py` (or your preferred filename).
2.  Open a terminal or command prompt.
3.  Navigate to the directory where you saved the file.
4.  Run the script using Python:

    ```bash
    python lego_app.py
    ```

This will open the main application window. A SQLite database file named `lego_database.db` will be created automatically in the same directory if it doesn't exist.

## Database

The application uses an SQLite database file named `lego_database.db` to store your LEGO collection data. This file will be created in the same directory as the script when you run the application for the first time. 
