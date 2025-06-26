import os
import sqlite3
import zipfile
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
from PIL import Image, ImageTk
import logging
import io
import re
import threading
import time
# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Colores estilo THEME
THEME_DARK = "#2b2d31"         # Gris oscuro
THEME_DARKER = "#232428"       # Más oscuro
THEME_DARKEST = "#1a1b1e"      # Casi negro
THEME_TEXT = "#c8c9ca"         # Gris claro, legible pero no blanco puro
THEME_ACCENT = "#5a5a5a"       # Usado para botones o elementos interactivos
THEME_ACCENT_HOVER = "#6a6a6a" # Versión hover más clara
THEME_CARD_BG = "#2f3035"      # Fondo de tarjetas
THEME_SELECTION = "#3c3c3c"    # Color de selección tipo resaltado
THEME_TAB = "#d9d9d9"          # Color para texto de pestañas
THEME_WARNING = "#ff6666"      # Color para botones de advertencia


# === Language Dictionary (i18n) ===
LANG = {
    "app_title": "Wagic Collection Manager",
    "tab_search": "Search Cards",
    "tab_collection": "My Collection",
    "tab_decks": "My Decks",
    "label_card_name": "Card name:",
    "button_search": "Search",
    "label_copies": "Copies:",
    "button_add_selected": "Add selected cards",
    "info_select_card": "Select a card to see details",
    "button_view_spoiler": "View Deck Spoiler",
 
    "button_add_new_card": "Add New Card",
    "title_add_card_dialog": "Add Card to Deck",
    "label_search_card": "Search card:",
    "button_add_to_deck_dialog": "Add to Deck",

    "button_refresh": "Refresh",
    "button_save": "Save",
    "button_clear": "Clear",
    "button_open_file": "Open File",
    "button_import_deck": "Import Deck",

    "tree_columns": ["ID", "Name", "Set", "Quantity"],

    "button_add_copy": "Add copy",
    "button_remove_copy": "Remove copy",
    "button_remove_all": "Remove all",

    "msg_search_empty": "Enter a search term",
    "msg_no_cards_found": "No cards found for",
    "msg_select_card": "Select at least one card",
    "msg_invalid_quantity": "Quantity must be at least 1",
    "msg_confirm_clear": "Are you sure you want to clear the whole collection?",
    "msg_confirm_remove_all": "Remove all copies of {name} (ID: {card_id})?",
    "msg_deck_empty": "No valid cards found in the file",
    "msg_deck_imported": "Deck successfully imported!",
    "msg_file_open_fail": "Could not open the file:",
    "msg_collection_saved": "Collection saved",
    "msg_collection_loaded": "Collection loaded",
    "msg_collection_cleared": "Collection cleared",
    "msg_cards_added": "{count} cards added to collection",
    "msg_quantity_updated": "Card {card_id}: updated quantity to {quantity}",
    "img_card": "Card",

    # New strings for decks tab
    "label_select_deck": "Select deck:",
    "button_new_deck": "New Deck",
    "button_rename_deck": "Rename Deck",
    "button_delete_deck": "Delete Deck",
    "button_export_deck": "Export Deck",
    "button_import_deck": "Import Deck",
    "button_add_to_deck": "Add copy",  # Changed from "Add cards to deck"
    "button_remove_from_deck": "Remove copy",  # Changed from "Remove from deck"
    "button_save_deck": "Save Deck",
    "label_deck_name": "Deck name:",
    "tree_deck_columns": ["ID", "Name", "Set", "Quantity"],
    "msg_new_deck": "Enter deck name:",
    "msg_rename_deck": "Enter new deck name:",
    "msg_confirm_delete": "Delete deck '{name}'?",
    "msg_deck_saved": "Deck saved",
    "msg_deck_loaded": "Deck loaded",
    "msg_deck_created": "Deck created",
    "msg_deck_renamed": "Deck renamed",
    "msg_deck_deleted": "Deck deleted",
    "msg_no_deck_selected": "No deck selected",
    "msg_cards_added_to_deck": "{count} cards added to deck",
    "msg_cards_removed": "{count} cards removed from deck",
    "label_card_text": "Card Text:",
    "label_total_cards": "Total cards:",
    "label_unique_cards": "Unique cards:",
}


class WagicCollectionManager:
    def __init__(self, root):
        self.root = root
        self.root.title(LANG["app_title"])
        self.root.geometry("1300x800")
        self.root.state('zoomed')
        self.root.configure(bg=THEME_DARK)
        
        # Rutas especificadas
        self.db_path = 'cards.db'
        self.sets_base_path = 'User\\sets'
        self.collection_path = 'User\\player\\collection.dat'
        self.decks_path = 'User\\player'  # Nueva ruta para decks
        
        # Configurar estilo oscuro
        self.setup_dark_theme()
        
        # Verificar rutas
        self.check_paths()
        
        # Conectar a la base de datos
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Crear widgets
        self.create_widgets()
        
        # Cargar colección actual
        self.load_collection()
        
        # Actualizar información de sets
        self.update_sets_info()
        
        # Cargar lista de decks
        self.load_decks_list()
        
        # Forzar prueba de imagen
        self.root.after(1000, self.test_image_display)

    def setup_dark_theme(self):
        """Configura el tema oscuro estilo THEME"""
        style = ttk.Style()
        
        # Configurar tema general
        style.theme_use('clam')
        
        # Configurar colores
        style.configure('.', 
                       background=THEME_DARK, 
                       foreground=THEME_TEXT,
                       font=('Segoe UI', 10))
        
        # Configurar frames
        style.configure('TFrame', background=THEME_DARK)
        style.configure('TLabelframe', background=THEME_DARK, foreground=THEME_TEXT)
        style.configure('TLabelframe.Label', background=THEME_DARK, foreground=THEME_TEXT)
        
        # Configurar botones
        style.configure('TButton', 
                       background=THEME_ACCENT, 
                       foreground='white',
                       borderwidth=0,
                       focusthickness=0,
                       focuscolor='none')
        style.map('TButton', 
                 background=[('active', THEME_ACCENT_HOVER), ('pressed', THEME_ACCENT_HOVER)])
        
        # Configurar botones de advertencia
        style.configure('Warning.TButton', 
                       background=THEME_WARNING,
                       foreground='white')
        style.map('Warning.TButton', 
                 background=[('active', '#ff8888'), ('pressed', '#ff4444')])
        
        # Configurar entrada de texto
        style.configure('TEntry', 
                      fieldbackground=THEME_DARKER,
                      foreground=THEME_TEXT,
                      insertcolor=THEME_TEXT,
                      bordercolor=THEME_DARKEST,
                      lightcolor=THEME_DARKEST,
                      darkcolor=THEME_DARKEST)
        
        # Configurar Treeview
        style.configure('Treeview', 
                      background=THEME_DARKER,
                      foreground=THEME_TEXT,
                      fieldbackground=THEME_DARKER,
                      rowheight=25)
        style.configure('Treeview.Heading', 
                      background=THEME_DARKEST,
                      foreground=THEME_TEXT,
                      relief='flat')
        style.map('Treeview', 
                background=[('selected', THEME_SELECTION)])
        
        # Configurar Scrollbar
        style.configure('Vertical.TScrollbar', 
                       background=THEME_DARKEST,
                       troughcolor=THEME_DARK,
                       arrowcolor=THEME_TEXT,
                       bordercolor=THEME_DARK)
        style.configure('Horizontal.TScrollbar', 
                       background=THEME_DARKEST,
                       troughcolor=THEME_DARK,
                       arrowcolor=THEME_TEXT,
                       bordercolor=THEME_DARK)
        
        # Configurar Spinbox
        style.configure('TSpinbox', 
                      fieldbackground=THEME_DARKER,
                      foreground=THEME_TEXT,
                      insertcolor=THEME_TEXT,
                      bordercolor=THEME_DARKEST,
                      lightcolor=THEME_DARKEST,
                      darkcolor=THEME_DARKEST)
        
        # Configurar Notebook (pestañas)
        style.configure('TNotebook', background=THEME_DARK)
        style.configure('TNotebook.Tab', 
                       background=THEME_DARK,
                       foreground=THEME_TAB,
                       padding=[10, 5],
                       font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab', 
                 background=[('selected', THEME_DARKER)],
                 foreground=[('selected', 'white')])
        
        # Configurar el área de texto para el texto de la carta
        style.configure('CardText.TFrame', background=THEME_DARK)
        style.configure('CardText.TLabel', background=THEME_DARK, foreground=THEME_TEXT)
        style.configure('CardText.TScrolledText', 
                      background=THEME_DARKER, 
                      foreground=THEME_TEXT,
                      insertbackground=THEME_TEXT,
                      relief='flat',
                      borderwidth=0)

    def check_paths(self):
        """Verificar que las rutas existan y sean accesibles"""
        logging.info("Verificando rutas...")
        
        # Verificar carpeta de sets
        if not os.path.exists(self.sets_base_path):
            logging.error(f"Carpeta de sets no encontrada: {self.sets_base_path}")
            messagebox.showerror("Error", f"Carpeta de sets no encontrada:\n{self.sets_base_path}")
            return
        
        # Verificar archivo de colección
        if not os.path.exists(self.collection_path):
            logging.info(f"Creando archivo de colección: {self.collection_path}")
            os.makedirs(os.path.dirname(self.collection_path), exist_ok=True)
            open(self.collection_path, 'w').close()
        
        # Verificar carpeta de decks
        if not os.path.exists(self.decks_path):
            logging.info(f"Creando carpeta de decks: {self.decks_path}")
            os.makedirs(self.decks_path, exist_ok=True)
        
        # Buscar un set de ejemplo
        example_set = None
        for d in os.listdir(self.sets_base_path):
            dir_path = os.path.join(self.sets_base_path, d)
            if os.path.isdir(dir_path):
                example_set = d
                break
        
        if example_set:
            zip_path = os.path.join(self.sets_base_path, example_set, f"{example_set}.zip")
            if not os.path.exists(zip_path):
                logging.warning(f"Archivo ZIP no encontrado para set de ejemplo: {zip_path}")
            else:
                logging.info(f"Set de ejemplo encontrado: {zip_path}")
        else:
            logging.warning("No se encontraron sets en la carpeta de sets")

    def test_image_display(self):
        """Función para probar la visualización de imágenes automáticamente"""
        try:
            # Buscar una carta conocida para probar
            self.cursor.execute("SELECT id, nombre, mana, set_nombre, rarity FROM cartas LIMIT 1")
            test_card = self.cursor.fetchone()
            
            if test_card:
                card_id, name, mana, set_name, rarity = test_card
                logging.info(f"Probando visualización de imagen para carta: {name} [{mana}] (ID: {card_id}, Set: {set_name})")
                
                # Mostrar en la interfaz
                self.result_tree.delete(*self.result_tree.get_children())
                self.result_tree.insert('', tk.END, values=(card_id, name, mana, set_name, rarity))
                if self.result_tree.get_children():
                    self.result_tree.selection_set(self.result_tree.get_children()[0])
                    self.result_tree.focus_set()
                    self.on_card_select(None)
        except sqlite3.Error as e:
            logging.error(f"Error al probar imagen: {str(e)}")

    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear notebook para pestañas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña 1: Buscar cartas
        search_tab = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(search_tab, text=LANG["tab_search"])
        self.create_search_tab(search_tab)
        
        # Pestaña 2: Mi Colección
        collection_tab = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(collection_tab, text=LANG["tab_collection"])
        self.create_collection_tab(collection_tab)
        
        # Pestaña 3: Mis Mazos
        decks_tab = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(decks_tab, text=LANG["tab_decks"])
        self.create_decks_tab(decks_tab)
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W,
                                  background=THEME_DARKEST, foreground=THEME_TEXT)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.update_status(f"Base: {self.db_path} | Sets: {self.sets_base_path} | Colección: {self.collection_path} | Decks: {self.decks_path}")

    def create_search_tab(self, parent):
        """Crea la pestaña de búsqueda de cartas con nuevos campos"""
        # Frame de búsqueda
        search_frame = ttk.LabelFrame(parent, text=LANG["tab_search"], padding=10)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Configurar grid con 4 columnas
        search_frame.columnconfigure(1, weight=1)  # La columna del campo de búsqueda se expandirá
        
        # Etiqueta y campo de búsqueda
        ttk.Label(search_frame, text=LANG["label_card_name"], foreground=THEME_TEXT).grid(row=0, column=0, padx=5, sticky=tk.W)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        self.search_entry.bind('<Return>', lambda e: self.search_cards())
        
        # Botón de búsqueda
        ttk.Button(search_frame, text=LANG["button_search"], command=self.search_cards).grid(row=0, column=2, padx=5)
        
        # Controles de cantidad y botón de agregar en la misma fila
        quantity_frame = ttk.Frame(search_frame)
        quantity_frame.grid(row=0, column=3, padx=(10, 0))
        
        ttk.Label(quantity_frame, text=LANG["label_copies"], foreground=THEME_TEXT).pack(side=tk.LEFT)
        self.quantity_var = tk.IntVar(value=1)
        self.quantity_spin = ttk.Spinbox(quantity_frame, from_=1, to=99, width=3, textvariable=self.quantity_var)
        self.quantity_spin.pack(side=tk.LEFT, padx=5)
        
        # Botón para agregar múltiples cartas
        add_button = ttk.Button(quantity_frame, text=LANG["button_add_selected"], 
                               command=self.add_selected_to_collection)
        add_button.pack(side=tk.LEFT)
        
        # Frame para resultados e imagen (dos columnas)
        results_frame = ttk.Frame(parent)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Columna izquierda: Lista de resultados
        left_frame = ttk.Frame(results_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Treeview para resultados con nueva columna "Tipo"
        columns = ("ID", "Name", "Mana", "Set", "Rarity")
        self.result_tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="extended")
        
        # Configurar columnas
        col_widths = [80, 250, 100, 80, 150]  # Nuevo ancho para la columna Tipo
        for col, width in zip(columns, col_widths):
            self.result_tree.heading(col, text=col, 
                                   command=lambda c=col: self.sort_treeview(self.result_tree, c, False))
            self.result_tree.column(col, width=width, minwidth=50)
        
        # Scrollbar vertical
        vsb = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=vsb.set)
        
        # Scrollbar horizontal
        hsb = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(xscrollcommand=hsb.set)
        
        # Layout
        self.result_tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)
        
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # Evento de selección
        self.result_tree.bind('<<TreeviewSelect>>', self.on_card_select)
        
        # Columna derecha: Imagen de la carta y detalles
        right_frame = ttk.LabelFrame(results_frame, text="Detalles de la Carta", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10)
        
        # Establecer un ancho mínimo y máximo para el panel derecho
        right_frame.pack_propagate(False)  # Esto evita que el frame cambie de tamaño con sus contenidos
        right_frame.config(width=400)      # Ancho fijo de 400 píxeles
        
        # Contenedor principal para imagen y texto
        content_frame = ttk.Frame(right_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para la imagen
        image_frame = ttk.LabelFrame(content_frame, text=LANG["img_card"], padding=5)
        image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Fondo para la imagen
        image_bg = ttk.Frame(image_frame)
        image_bg.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        image_bg.configure(style='Card.TFrame')
        
        # Imagen de la carta
        self.card_image = ttk.Label(image_bg)
        self.card_image.pack(fill=tk.BOTH, expand=True)
        
        # Información de la carta
        self.card_info = ttk.Label(image_frame, text=LANG["info_select_card"], 
                                 justify=tk.LEFT, foreground=THEME_TEXT)
        self.card_info.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Frame para el texto de la carta (ahora en la mitad inferior)
        text_frame = ttk.LabelFrame(content_frame, text=LANG["label_card_text"], padding=5)
        text_frame.pack(fill=tk.BOTH, expand=False)  # No expandir verticalmente
        
        # Área de texto con altura fija
        self.card_text = scrolledtext.ScrolledText(
            text_frame, 
            wrap=tk.WORD, 
            height=10,  # Altura ajustada
            background=THEME_DARKER,
            foreground=THEME_TEXT,
            insertbackground=THEME_TEXT
        )
        self.card_text.pack(fill=tk.BOTH, expand=True)
        self.card_text.config(state=tk.DISABLED)
        
        # Crear estilo adicional para el fondo de imagen
        style = ttk.Style()
        style.configure('Card.TFrame', background=THEME_CARD_BG)

    def create_collection_tab(self, parent):
        """Crea la pestaña para visualizar la colección"""
        # Frame para controles de colección
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(controls_frame, text=LANG["button_refresh"], command=self.load_collection).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text=LANG["button_save"], command=self.save_collection).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text=LANG["button_clear"], command=self.clear_collection).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text=LANG["button_open_file"], 
                  command=self.open_collection_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text=LANG["button_import_deck"], 
                  command=self.import_deck).pack(side=tk.LEFT, padx=5)
        
        # Etiqueta para mostrar el total de cartas
        self.collection_total_var = tk.StringVar(value="Total cards: 0")
        total_label = ttk.Label(controls_frame, textvariable=self.collection_total_var, 
                               foreground=THEME_TEXT, font=('Segoe UI', 9, 'bold'))
        total_label.pack(side=tk.RIGHT, padx=10)
        
        # Frame para colección e imagen (dos columnas)
        collection_frame = ttk.Frame(parent)
        collection_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Columna izquierda: Lista de la colección
        left_frame = ttk.Frame(collection_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Treeview para la colección
        columns = ("ID", "Name", "Set", "quantity")
        self.collection_tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="extended")
        
        # Configurar columnas con capacidad de ordenamiento
        col_widths = [80, 300, 150, 80]
        for col, width in zip(columns, col_widths):
            self.collection_tree.heading(col, text=col, 
                                       command=lambda c=col: self.sort_treeview(self.collection_tree, c, False))
            self.collection_tree.column(col, width=width, minwidth=50)
        
        # Scrollbar vertical
        vsb = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.collection_tree.yview)
        self.collection_tree.configure(yscrollcommand=vsb.set)
        
        # Scrollbar horizontal
        hsb = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=self.collection_tree.xview)
        self.collection_tree.configure(xscrollcommand=hsb.set)
        
        # Layout
        self.collection_tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)
        
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # Evento de selección
        self.collection_tree.bind('<<TreeviewSelect>>', self.on_collection_card_select)
        
        # Columna derecha: Imagen de la carta
        right_frame = ttk.LabelFrame(collection_frame, text=LANG["img_card"], padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10)
        
        # Fondo para la imagen
        image_bg = ttk.Frame(right_frame)
        image_bg.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        image_bg.configure(style='Card.TFrame')
        
        # Imagen de la carta
        self.card_image_collection = ttk.Label(image_bg)
        self.card_image_collection.pack(fill=tk.BOTH, expand=True)
        
        # Información de la carta
        self.card_info_collection = ttk.Label(right_frame, text=LANG["info_select_card"], 
                                 justify=tk.LEFT, foreground=THEME_TEXT)
        self.card_info_collection.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # Botones para gestionar cartas
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        # Botón para agregar copias
        self.add_button = ttk.Button(button_frame, text=LANG["button_add_copy"], 
                                   command=lambda: self.adjust_card_quantity(1))
        self.add_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Botón para quitar copias
        self.remove_button = ttk.Button(button_frame, text=LANG["button_remove_copy"], 
                                      style='Warning.TButton',
                                      command=lambda: self.adjust_card_quantity(-1))
        self.remove_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Botón para eliminar todas las copias
        self.remove_all_button = ttk.Button(button_frame, text=LANG["button_remove_all"], 
                                          style='Warning.TButton',
                                          command=self.remove_all_copies)
        self.remove_all_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
    def show_deck_spoiler(self):
        """Muestra un spoiler visual del deck actual similar a deckstats.net"""
        if not hasattr(self, 'deck_cards') or not self.deck_cards:
            messagebox.showinfo("Info", "No deck loaded or deck is empty")
            return
        
        # Crear ventana emergente
        spoiler_win = tk.Toplevel(self.root)
        spoiler_win.title(f"Deck Spoiler: {self.deck_name_var.get()}")
        spoiler_win.geometry("1250x800")
        spoiler_win.transient(self.root)
        spoiler_win.grab_set()
        
        # Frame principal con scrollbar
        main_frame = ttk.Frame(spoiler_win)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame, bg=THEME_DARK)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        main_frame.pack(fill=tk.BOTH, expand=True)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Agrupar cartas por tipo (Creature, Instant, Sorcery, Land, etc.)
        card_groups = {}
        for card_id, quantity in self.deck_cards.items():
            try:
                self.cursor.execute("SELECT tipo FROM cartas WHERE id = ?", (card_id,))
                card_type = self.cursor.fetchone()[0]
                
                # Simplificar tipo para agrupación
                if "Creature" in card_type:
                    group = "Creatures"
                elif "Land" in card_type:
                    group = "Lands"
                elif "Instant" in card_type or "Sorcery" in card_type:
                    group = "Spells"
                elif "Artifact" in card_type:
                    group = "Artifacts"
                elif "Enchantment" in card_type:
                    group = "Enchantments"
                elif "Planeswalker" in card_type:
                    group = "Planeswalkers"
                else:
                    group = "Other"
                
                if group not in card_groups:
                    card_groups[group] = []
                
                card_groups[group].append((card_id, quantity))
            except:
                pass
        
        # Ordenar grupos
        ordered_groups = ["Creatures", "Planeswalkers", "Artifacts", "Enchantments", 
                         "Spells", "Lands", "Other"]
        
        # Mostrar cada grupo
        for group in ordered_groups:
            if group not in card_groups or not card_groups[group]:
                continue
                
            # Frame para el grupo
            group_frame = ttk.LabelFrame(scrollable_frame, text=f"{group} ({len(card_groups[group])})", 
                                       padding=10)
            group_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Frame para las cartas del grupo (con wrap)
            cards_frame = ttk.Frame(group_frame)
            cards_frame.pack(fill=tk.X)
            
            row_frame = None
            cards_in_row = 0
            max_cards_per_row = 8
            
            for card_id, quantity in card_groups[group]:
                # Crear nueva fila si es necesario
                if cards_in_row == 0 or cards_in_row >= max_cards_per_row:
                    row_frame = ttk.Frame(cards_frame)
                    row_frame.pack(fill=tk.X, pady=5)
                    cards_in_row = 0
                
                # Frame para cada carta
                card_frame = ttk.Frame(row_frame)
                card_frame.pack(side=tk.LEFT, padx=10)
                
                # Etiqueta de cantidad
                qty_label = ttk.Label(card_frame, text=f"x{quantity}", font=("Arial", 10, "bold"),
                                     foreground="white", background=THEME_DARKER)
                qty_label.pack(side=tk.TOP, anchor=tk.NE)
                
                # Imagen de la carta (miniatura)
                img_label = ttk.Label(card_frame)
                img_label.pack(side=tk.TOP)
                
                # Nombre de la carta
                try:
                    self.cursor.execute("SELECT nombre FROM cartas WHERE id = ?", (card_id,))
                    card_name = self.cursor.fetchone()[0]
                    name_label = ttk.Label(card_frame, text=card_name, width=15, wraplength=150)
                    name_label.pack(side=tk.TOP, pady=(5, 0))
                except:
                    name_label = ttk.Label(card_frame, text=f"ID: {card_id}")
                    name_label.pack(side=tk.TOP, pady=(5, 0))
                
                # Cargar imagen en miniatura (en segundo plano para no bloquear la UI)
                # Obtener el set_name desde la base de datos
                try:
                    self.cursor.execute("SELECT set_nombre FROM cartas WHERE id = ?", (card_id,))
                    result = self.cursor.fetchone()
                    if result:
                        set_name = result[0]
                        # Cargar imagen en miniatura con el set correcto
                        self.load_card_thumbnail(card_id, set_name, img_label)
                    else:
                        logging.warning(f"No se encontró set para la carta {card_id}")
                except Exception as e:
                    logging.error(f"Error al obtener set de la carta {card_id}: {e}")

                
                cards_in_row += 1
        
        # Botón para cerrar
        btn_frame = ttk.Frame(spoiler_win)
        btn_frame.pack(fill=tk.X, pady=0)
        
        #ttk.Button(btn_frame, text="Close", command=spoiler_win.destroy).pack()
        
        # Centrar ventana
        self.center_window(spoiler_win)    

    def load_card_thumbnail(self, card_id, set_name, img_label):
        """Carga una miniatura de la carta en un label usando las miniaturas preexistentes"""
        # Crear un hilo para cargar la imagen sin bloquear la UI
        def load_image_thread():
            try:
                # Construir ruta al archivo ZIP
                zip_path = os.path.join(self.sets_base_path, set_name, f"{set_name}.zip")
                
                if not os.path.exists(zip_path):
                    return
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Primero buscar en la carpeta de miniaturas
                    thumbnail_paths = [
                        f"thumbnails/{card_id}.jpg",
                        f"thumbnails/{card_id}.JPG",
                        f"thumbnails/{card_id}.png",
                        f"thumbnails/{card_id}.PNG",
                        f"{set_name}/thumbnails/{card_id}.jpg",
                        f"{set_name}/thumbnails/{card_id}.JPG",
                        f"{set_name}/thumbnails/{card_id}.png",
                        f"{set_name}/thumbnails/{card_id}.PNG",
                    ]
                    
                    # Si no se encuentra en thumbnails, buscar en las ubicaciones originales
                    standard_paths = [
                        f"{set_name}/{card_id}.jpg",
                        f"{set_name}/{card_id}.JPG",
                        f"{set_name}/{card_id}.png",
                        f"{set_name}/{card_id}.PNG",
                        f"{set_name.lower()}/{card_id}.jpg",
                        f"{set_name.lower()}/{card_id}.png",
                        f"{card_id}.jpg",
                        f"{card_id}.JPG",
                        f"{card_id}.png",
                        f"{card_id}.PNG"
                    ]
                    
                    img_found = None
                    # Buscar primero en thumbnails
                    for path in thumbnail_paths:
                        if path in zip_ref.namelist():
                            img_found = path
                            break
                    
                    # Si no se encontró en thumbnails, buscar en ubicaciones estándar
                    if not img_found:
                        for path in standard_paths:
                            if path in zip_ref.namelist():
                                img_found = path
                                break
                    
                    if not img_found:
                        return
                    
                    # Extraer imagen
                    img_data = zip_ref.read(img_found)
                    
                    # Cargar con PIL
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Si la imagen viene de la carpeta thumbnails, usar directamente
                    # De lo contrario, redimensionar (por si acaso)
                    if "thumbnails" not in img_found:
                        # Calcular nuevo tamaño para miniatura
                        original_width, original_height = img.size
                        ratio = min(150 / original_width, 210 / original_height)
                        new_size = (int(original_width * ratio), int(original_height * ratio))
                        img = img.resize(new_size, Image.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(img)
                    
                    # Actualizar UI en el hilo principal
                    self.root.after(0, lambda: self.update_thumbnail(img_label, photo))
                    
            except Exception as e:
                logging.error(f"Error loading thumbnail: {str(e)}")
        
        # Iniciar hilo
        threading.Thread(target=load_image_thread, daemon=True).start()
    
    def update_thumbnail(self, img_label, photo):
        """Actualiza el label con la miniatura cargada"""
        img_label.config(image=photo)
        img_label.image = photo  # Mantener referencia
    
    def update_thumbnail(self, img_label, photo):
        """Actualiza el label con la miniatura cargada"""
        img_label.config(image=photo)
        img_label.image = photo  # Mantener referencia 
        
    def center_window(self, window):
        """Centra una ventana en la pantalla"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'+{x}+{y}')

    def refresh_decks(self):
        """Recarga la lista de decks desde el disco"""
        self.load_decks_list()
        self.update_status("Decks list refreshed")

    def create_decks_tab(self, parent):
        """Crea la pestaña para gestionar decks con columna Type agregada"""
        # Frame para controles de decks
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(controls_frame, text=LANG["label_select_deck"], foreground=THEME_TEXT).pack(side=tk.LEFT, padx=5)
        
        # Combobox para seleccionar deck
        self.deck_var = tk.StringVar()
        self.deck_combo = ttk.Combobox(controls_frame, textvariable=self.deck_var, state="readonly", width=30)
        self.deck_combo.pack(side=tk.LEFT, padx=5)
        self.deck_combo.bind('<<ComboboxSelected>>', self.on_deck_selected)
        
        # Botones para gestionar decks
        ttk.Button(controls_frame, text=LANG["button_new_deck"], command=self.create_new_deck).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Refresh Decks", command=self.refresh_decks).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text=LANG["button_rename_deck"], command=self.rename_deck).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text=LANG["button_delete_deck"], command=self.delete_deck, style='Warning.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text=LANG["button_export_deck"], command=self.export_deck).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text=LANG["button_save_deck"], command=self.save_current_deck).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text=LANG["button_add_new_card"], command=self.open_add_card_to_deck_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text=LANG["button_view_spoiler"], command=self.show_deck_spoiler).pack(side=tk.LEFT, padx=5)
        
        # Etiqueta para mostrar el total de cartas en el deck
        self.deck_total_var = tk.StringVar(value="Total cards: 0")
        total_label = ttk.Label(controls_frame, textvariable=self.deck_total_var, 
                               foreground=THEME_TEXT, font=('Segoe UI', 9, 'bold'))
        total_label.pack(side=tk.RIGHT, padx=10)
        
        # Frame para nombre del deck
        name_frame = ttk.Frame(parent)
        name_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(name_frame, text=LANG["label_deck_name"], foreground=THEME_TEXT).pack(side=tk.LEFT, padx=5)
        self.deck_name_var = tk.StringVar()
        self.deck_name_entry = ttk.Entry(name_frame, textvariable=self.deck_name_var, width=50)
        self.deck_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.deck_name_entry.bind('<Return>', lambda e: self.save_current_deck())
        
        # Frame para deck e imagen (dos columnas)
        deck_frame = ttk.Frame(parent)
        deck_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Columna izquierda: Lista de cartas en el deck
        left_frame = ttk.Frame(deck_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Treeview para cartas en el deck con nueva columna Type
        columns = ("ID", "Name", "Mana", "Set", "Quantity", "Type")
        self.deck_tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="extended")
        
        # Configurar columnas
        col_widths = [80, 250, 80, 150, 80, 150]  # Nuevo ancho para Type
        for col, width in zip(columns, col_widths):
                self.deck_tree.heading(col, text=col, 
                                      command=lambda c=col: self.sort_treeview(self.deck_tree, c, False))
                self.deck_tree.column(col, width=width, minwidth=50)
        
        # Scrollbar vertical
        vsb = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.deck_tree.yview)
        self.deck_tree.configure(yscrollcommand=vsb.set)
        
        # Scrollbar horizontal
        hsb = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=self.deck_tree.xview)
        self.deck_tree.configure(xscrollcommand=hsb.set)
        
        # Layout
        self.deck_tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)
        
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # Evento de selección
        self.deck_tree.bind('<<TreeviewSelect>>', self.on_deck_card_select)
        
        # Columna derecha: Imagen de la carta
        right_frame = ttk.LabelFrame(deck_frame, text=LANG["img_card"], padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10)
        
        # Fondo para la imagen
        image_bg = ttk.Frame(right_frame)
        image_bg.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        image_bg.configure(style='Card.TFrame')
        
        # Imagen de la carta
        self.deck_card_image = ttk.Label(image_bg)
        self.deck_card_image.pack(fill=tk.BOTH, expand=True)
        
        # Información de la carta
        self.deck_card_info = ttk.Label(right_frame, text=LANG["info_select_card"], 
                                      justify=tk.LEFT, foreground=THEME_TEXT)
        self.deck_card_info.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # Botones para gestionar cartas en el deck
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        # Botón para agregar copias
        self.add_to_deck_button = ttk.Button(button_frame, text=LANG["button_add_to_deck"], 
                                           command=self.increment_deck_card_quantity)
        self.add_to_deck_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Botón para quitar copias
        self.remove_from_deck_button = ttk.Button(button_frame, text=LANG["button_remove_from_deck"], 
                                                style='Warning.TButton',
                                                command=self.decrement_deck_card_quantity)
        self.remove_from_deck_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def search_cards(self, event=None):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showinfo("Búsqueda", LANG["msg_search_empty"])
            return
        
        self.result_tree.delete(*self.result_tree.get_children())
        self.card_info.config(text="Buscando...")
        self.card_image.config(image='')
        self.card_text.config(state=tk.NORMAL)
        self.card_text.delete(1.0, tk.END)
        self.card_text.config(state=tk.DISABLED)
        self.update_status(f"Buscando: {query}...")
        
        try:
            # CAMBIO 2: Modificar consulta para incluir "mana"
            self.cursor.execute("""
                SELECT id, nombre, mana, set_nombre, rarity, tipo, subtipo, texto 
                FROM cartas 
                WHERE nombre LIKE ? 
                   OR tipo LIKE ? 
                   OR subtipo LIKE ?
                   OR texto LIKE ?
                ORDER BY nombre
            """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
            
            results = self.cursor.fetchall()
            
            if not results:
                self.update_status(f"No se encontraron cartas para: {query}")
                self.card_info.config(text="No se encontraron resultados")
                return
            
            for card in results:
                # CAMBIO 3: Añadir "mana" en los valores mostrados
                self.result_tree.insert('', tk.END, values=(
                    card[0],  # ID
                    card[1],  # Nombre
                    card[2],  # Mana
                    card[3],  # Set
                    card[4],  # Rareza
                    card[5],   # Tipo
                    card[6]   # Texto
                ))
            
            self.update_status(f"Encontradas {len(results)} cartas para: {query}")
            if self.result_tree.get_children():
                self.result_tree.selection_set(self.result_tree.get_children()[0])
                self.result_tree.focus_set()
            
        except sqlite3.Error as e:
            messagebox.showerror("Error de base de datos", str(e))

    def on_card_select(self, event):
        selected_items = self.result_tree.selection()
        if not selected_items:
            return
        
        # Mostrar solo la primera carta seleccionada
        item = selected_items[0]
        all_values = self.result_tree.item(item, 'values')
        if not all_values:
            return
        
        # Obtener todos los valores de la carta
        card_id = all_values[0]
        try:
            # CAMBIO 4: Modificar consulta para incluir "mana"
            self.cursor.execute("""
                SELECT id, nombre, mana, set_nombre, rarity, texto, tipo, subtipo 
                FROM cartas 
                WHERE id = ?
            """, (card_id,))
            card = self.cursor.fetchone()
            
            if card:
                # CAMBIO 5: Añadir "mana" en la información mostrada
                info_text = f"ID: {card[0]}\nName: {card[1]}\nMana: {card[2]}\nSet: {card[3]}\nRarity: {card[4]}"
                if card[6]:  # Tipo
                    info_text += f"\nType: {card[6]}"
                if card[7]:  # Subtipo
                    info_text += f"\nSubtype: {card[7]}"
                
                self.card_info.config(text=info_text)
                
                # Mostrar texto de la carta
                self.card_text.config(state=tk.NORMAL)
                self.card_text.delete(1.0, tk.END)
                self.card_text.insert(tk.END, card[5] or "Sin texto")  # Texto de la carta
                self.card_text.config(state=tk.DISABLED)
                
                # Mostrar imagen
                self.show_card_image(card_id, card[3], self.card_image)
        
        except sqlite3.Error as e:
            logging.error(f"Error al obtener detalles de la carta: {str(e)}")

    def on_collection_card_select(self, event):
        """Manejador de selección de cartas en la colección"""
        selected_items = self.collection_tree.selection()
        if not selected_items:
            return
        
        # Mostrar solo la primera carta seleccionada
        values = self.collection_tree.item(selected_items[0], 'values')
        if not values or len(values) < 4:
            return
        
        card_id, name, set_name, quantity = values
        self.card_info_collection.config(text=f"ID: {card_id}\nNombre: {name}\nSet: {set_name}\nCantidad: {quantity}")
        
        # Mostrar imagen
        self.show_card_image(card_id, set_name, self.card_image_collection)
    
    def on_deck_card_select(self, event):
        """Manejador de selección de cartas en el deck con nueva columna Type"""
        selected_items = self.deck_tree.selection()
        if not selected_items:
            return
        
        # Mostrar solo la primera carta seleccionada
        values = self.deck_tree.item(selected_items[0], 'values')
        if not values or len(values) < 6:  # Ahora esperamos 6 valores
            return
        
        card_id, name, mana, set_name, quantity, card_type = values
        self.deck_card_info.config(text=f"ID: {card_id}\nName: {name}\nMana: {mana}\nSet: {set_name}\nType: {card_type}\nQuantity: {quantity}")
        
        # Mostrar imagen
        self.show_card_image(card_id, set_name, self.deck_card_image)

    def show_card_image(self, card_id, set_name, image_label):
        # Limpiar imagen actual
        image_label.config(image='')
        image_label.image = None  # Eliminar referencia anterior
        
        # Crear carpeta temp si no existe, dentro del directorio de la aplicación
        base_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(base_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Construir ruta al archivo ZIP
        zip_path = os.path.join(self.sets_base_path, set_name, f"{set_name}.zip")
        logging.info(f"Intentando cargar imagen desde: {zip_path}")
        
        if not os.path.exists(zip_path):
            # Intentar diferentes variaciones de nombre
            possible_zip_names = [
                f"{set_name}.zip",
                f"{set_name.lower()}.zip",
                f"{set_name.upper()}.zip",
                f"{set_name.replace(' ', '_')}.zip",
                f"{set_name.replace(':', '')}.zip"
            ]
            
            for zip_name in possible_zip_names:
                test_path = os.path.join(self.sets_base_path, set_name, zip_name)
                if os.path.exists(test_path):
                    zip_path = test_path
                    logging.info(f"Archivo ZIP encontrado: {zip_path}")
                    break
            else:
                self.update_status(f"Archivo ZIP no encontrado para el set: {set_name}")
                logging.error(f"No se encontró archivo ZIP para el set: {set_name}")
                return
        
        try:
            # Abrir el archivo ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Generar posibles rutas de imagen
                possible_paths = [
                    f"{set_name}/{card_id}.jpg",
                    f"{set_name}/{card_id}.JPG",
                    f"{set_name}/{card_id}.png",
                    f"{set_name}/{card_id}.PNG",
                    f"{set_name.lower()}/{card_id}.jpg",
                    f"{set_name.lower()}/{card_id}.png",
                    f"{card_id}.jpg",  # Algunos sets no tienen subcarpeta
                    f"{card_id}.JPG",
                    f"{card_id}.png",
                    f"{card_id}.PNG"
                ]
                
                img_found = None
                for path in possible_paths:
                    if path in zip_ref.namelist():
                        img_found = path
                        logging.info(f"Imagen encontrada en ZIP: {path}")
                        break
                
                if not img_found:
                    self.update_status(f"Imagen no encontrada en ZIP para ID: {card_id}")
                    logging.warning(f"Imagen no encontrada en ZIP. Rutas intentadas: {possible_paths}")
                    return
                
                # Crear un nombre de archivo temporal único en la carpeta temp
                temp_filename = f"{set_name}_{card_id}.jpg"
                temp_path = os.path.join(temp_dir, temp_filename)
                
                img_data = zip_ref.read(img_found)
                
                # Verificar si es PNG y convertir a JPG si es necesario
                if img_found.lower().endswith('.png'):
                    png_image = Image.open(io.BytesIO(img_data))
                    if png_image.mode == 'RGBA':
                        png_image = png_image.convert('RGB')
                    # Guardar como JPG en la ruta temporal
                    png_image.save(temp_path, format='JPEG')
                    logging.info("Imagen PNG convertida a JPG")
                else:
                    # Guardar directamente
                    with open(temp_path, 'wb') as f:
                        f.write(img_data)
                
                # Cargar imagen con PIL
                img = Image.open(temp_path)
                
                # Calcular nuevo tamaño manteniendo relación de aspecto
                original_width, original_height = img.size
                ratio = min(350 / original_width, 490 / original_height)
                new_size = (int(original_width * ratio), int(original_height * ratio))
                
                # Redimensionar con alta calidad
                img = img.resize(new_size, Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Actualizar widget de imagen
                image_label.config(image=photo)
                image_label.image = photo  # Mantener referencia
                
                self.update_status(f"Imagen cargada: {set_name}/{card_id}")
                logging.info(f"Imagen temporal guardada en: {temp_path}")
                
        except Exception as e:
            self.update_status(f"Error al cargar imagen: {str(e)}")
            logging.exception("Error al cargar imagen")
        
    def clean_temp_folder(self):
        """Limpia la carpeta de archivos temporales al iniciar la aplicación"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(base_dir, "temp")
        if os.path.exists(temp_dir):
            logging.info(f"Limpiando carpeta temporal: {temp_dir}")
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        logging.debug(f"Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logging.error(f"No se pudo eliminar {file_path}: {str(e)}")
        else:
            os.makedirs(temp_dir, exist_ok=True)
            logging.info(f"Carpeta temporal creada: {temp_dir}")
        
    def safe_delete(self, path):
        """Eliminar archivo de manera segura"""
        try:
            if os.path.exists(path):
                os.unlink(path)
                logging.info(f"Archivo temporal eliminado: {path}")
        except Exception as e:
            logging.error(f"Error al eliminar temporal: {str(e)}")

    def load_collection(self):
        try:
            # Cambiamos a un diccionario para almacenar cantidades
            self.collection = {}
            if os.path.exists(self.collection_path):
                with open(self.collection_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and line.isdigit():
                            card_id = line
                            self.collection[card_id] = self.collection.get(card_id, 0) + 1
            
            self.update_collection_display()
            self.update_collection_total()  # Actualizar el contador total
            total_cards = sum(self.collection.values())
            self.update_status(f"Colección cargada: {len(self.collection)} cartas únicas, {total_cards} copias")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la colección: {str(e)}")

    def update_collection_display(self):
        """Actualiza la visualización de la colección en el Treeview"""
        # Limpiar treeview existente
        self.collection_tree.delete(*self.collection_tree.get_children())
        
        if not self.collection:
            return
        
        try:
            # Obtener detalles de las cartas en la colección
            card_ids = list(self.collection.keys())
            placeholders = ','.join('?' for _ in card_ids)
            
            self.cursor.execute(f"""
                SELECT id, nombre, set_nombre 
                FROM cartas 
                WHERE id IN ({placeholders})
            """, card_ids)
            
            card_details = {row[0]: (row[1], row[2]) for row in self.cursor.fetchall()}
            
            # Insertar en el treeview
            for card_id, count in self.collection.items():
                if card_id in card_details:
                    name, set_name = card_details[card_id]
                    self.collection_tree.insert('', tk.END, values=(card_id, name, set_name, count))
                else:
                    # Si no encontramos detalles, intentar obtenerlos de nuevo
                    self.cursor.execute("SELECT nombre, set_nombre FROM cartas WHERE id = ?", (card_id,))
                    result = self.cursor.fetchone()
                    if result:
                        name, set_name = result
                        self.collection_tree.insert('', tk.END, values=(card_id, name, set_name, count))
                    else:
                        # Si aún no se encuentra, mostrar como desconocida
                        self.collection_tree.insert('', tk.END, values=(card_id, "Carta no encontrada", "Set desconocido", count))
        
        except sqlite3.Error as e:
            logging.error(f"Error al cargar detalles de colección: {str(e)}")
        
        # Actualizar el contador total
        self.update_collection_total()

    def add_to_collection(self, card_id, quantity=1):
        # Agregar o actualizar cantidad
        current = self.collection.get(card_id, 0)
        self.collection[card_id] = current + quantity

    def add_selected_to_collection(self):
        selected_items = self.result_tree.selection()
        if not selected_items:
            messagebox.showinfo("Colección", LANG["msg_select_card"])
            return
        
        quantity = self.quantity_var.get()
        if quantity < 1:
            messagebox.showwarning("Cantidad inválida", LANG["msg_invalid_quantity"])
            return
        
        added_count = 0
        for item in selected_items:
            values = self.result_tree.item(item, 'values')
            if values:
                card_id = values[0]
                self.add_to_collection(card_id, quantity)
                added_count += quantity
        
        if added_count > 0:
            self.update_collection_display()
            self.save_collection()
            self.update_collection_total()  # Actualizar el contador total
            self.update_status(f"{added_count} cartas agregadas a la colección")
        else:
            self.update_status("No se agregaron nuevas cartas")

    def save_collection(self):
        try:
            with open(self.collection_path, 'w') as f:
                for card_id, count in self.collection.items():
                    # Escribir el ID tantas veces como copias haya
                    for _ in range(count):
                        f.write(f"{card_id}\n")
            
            total_cards = sum(self.collection.values())
            self.update_status(f"Colección guardada: {len(self.collection)} cartas únicas, {total_cards} copias")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la colección: {str(e)}")

    def clear_collection(self):
        if messagebox.askyesno("Confirmar", LANG["msg_confirm_clear"]):
            self.collection = {}
            self.save_collection()
            self.update_collection_display()
            self.update_collection_total()  # Actualizar el contador total
            self.update_status(LANG["msg_collection_cleared"])

    def open_collection_file(self):
        try:
            os.startfile(self.collection_path)
            self.update_status(f"Archivo de colección abierto: {self.collection_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {str(e)}")

    def update_sets_info(self):
        try:
            self.cursor.execute("SELECT COUNT(DISTINCT set_nombre) FROM cartas")
            sets_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM cartas")
            cards_count = self.cursor.fetchone()[0]
            
            self.update_status(f"Sets disponibles: {sets_count} | Cartas en base de datos: {cards_count}")
        except sqlite3.Error:
            pass

    def import_deck(self):
        """Importa un archivo de deck y lo convierte al formato de Wagic"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de deck",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                deck_lines = f.readlines()
            
            deck_name = "Deck Importado"
            cards = []  # Lista de tuplas (card_id, quantity)
            total_copies = 0
            
            # Expresión regular para analizar las líneas del deck
            card_pattern = re.compile(r'(.+?)\s*(?:\(([^)]+)\))?\s*\*?(\d+)?$')
            
            for line in deck_lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Extraer nombre del deck
                if line.startswith('#NAME:'):
                    deck_name = line.split(':', 1)[1].strip()
                    continue
                    
                # Buscar cartas con el patrón
                match = card_pattern.match(line)
                if not match:
                    # Intentar formato de ID directo (ej: "123456 4")
                    if line.replace(' ', '').isdigit() or ' ' in line:
                        parts = line.split()
                        if len(parts) == 1 and parts[0].isdigit():
                            card_id = parts[0]
                            cards.append((card_id, 1))
                            self.add_to_collection(card_id, 1)
                            total_copies += 1
                        elif len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                            card_id = parts[0]
                            quantity = int(parts[1])
                            cards.append((card_id, quantity))
                            self.add_to_collection(card_id, quantity)
                            total_copies += quantity
                    continue
                    
                card_name = match.group(1).strip()
                set_name = match.group(2).strip() if match.group(2) else None
                quantity = int(match.group(3)) if match.group(3) else 1
                
                # Buscar la carta en la base de datos
                query = "SELECT id FROM cartas WHERE nombre = ?"
                params = [card_name]
                
                if set_name:
                    query += " AND set_nombre = ?"
                    params.append(set_name)
                    
                self.cursor.execute(query + " LIMIT 1", params)
                result = self.cursor.fetchone()
                
                if result:
                    card_id = result[0]
                    cards.append((card_id, quantity))
                    # Agregar a la colección
                    self.add_to_collection(card_id, quantity)
                    total_copies += quantity
                else:
                    logging.warning(f"Carta no encontrada: {card_name} ({set_name})")
            
            if not cards:
                messagebox.showwarning("Deck vacío", LANG["msg_deck_empty"])
                return
            
            # Guardar la colección actualizada
            self.save_collection()
            self.update_collection_display()
            self.update_collection_total()  # Actualizar el contador total
                
            # Guardar el deck en formato Wagic
            deck_number = self.get_next_deck_number()
            deck_filename = os.path.join(self.decks_path, f"deck{deck_number}.txt")
            
            with open(deck_filename, 'w', encoding='utf-8') as f:
                f.write(f"#NAME:{deck_name}\n")
                for card_id, quantity in cards:
                    # Escribir el ID la cantidad de veces especificada
                    for _ in range(quantity):
                        f.write(f"{card_id}\n")
            
            messagebox.showinfo("Deck importado", 
                f"Deck importado con éxito!\n"
                f"Nombre: {deck_name}\n"
                f"Cartas únicas: {len(cards)}\n"
                f"Copias totales: {total_copies}\n"
                f"Guardado como: {deck_filename}")
                
            self.update_status(f"Deck importado: {deck_name} ({len(cards)} cartas únicas, {total_copies} copias)")
            
        except Exception as e:
            logging.exception("Error al importar deck")
            messagebox.showerror("Error", f"No se pudo importar el deck:\n{str(e)}")

    def get_next_deck_number(self):
        """Encuentra el próximo número de deck disponible empezando desde 3"""
        # Crear directorio si no existe
        os.makedirs(self.decks_path, exist_ok=True)
        
        # Buscar decks existentes
        existing_decks = []
        for filename in os.listdir(self.decks_path):
            if filename.startswith("deck") and filename.endswith(".txt"):
                try:
                    # Extraer número del nombre deckX.txt
                    num = int(filename[4:-4])
                    existing_decks.append(num)
                except ValueError:
                    continue
        
        # Comenzar desde 1 y encontrar el primer número disponible
        deck_number = 1
        while deck_number in existing_decks:
            deck_number += 1
            
        return deck_number

    def adjust_card_quantity(self, amount):
        """Ajusta la cantidad de una carta en la colección"""
        selected_items = self.collection_tree.selection()
        if not selected_items:
            messagebox.showinfo("Colección", LANG["msg_select_card"])
            return
        
        # Operar solo sobre la primera carta seleccionada
        item = selected_items[0]
        values = self.collection_tree.item(item, 'values')
        if not values or len(values) < 4:
            return
        
        card_id = values[0]
        current_quantity = int(values[3])
        
        # Calcular nueva cantidad
        new_quantity = current_quantity + amount
        
        if new_quantity <= 0:
            # Eliminar todas las copias
            self.remove_all_copies(selected_items)
        else:
            # Actualizar cantidad
            self.collection[card_id] = new_quantity
            self.save_collection()
            self.update_collection_display()
            self.update_collection_total()  # Actualizar el contador total
            self.update_status(f"Carta {card_id}: cantidad actualizada a {new_quantity}")
            
            # Actualizar la información mostrada
            self.on_collection_card_select(None)

    def remove_all_copies(self, selected_items=None):
        """Elimina todas las copias de la carta seleccionada"""
        if not selected_items:
            selected_items = self.collection_tree.selection()
        if not selected_items:
            messagebox.showinfo("Colección", LANG["msg_select_card"])
            return
        
        # Operar solo sobre la primera carta seleccionada
        item = selected_items[0]
        values = self.collection_tree.item(item, 'values')
        if not values or len(values) < 4:
            return
        
        card_id = values[0]
        name = values[1]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar todas las copias de {name} (ID: {card_id})?"):
            # Eliminar carta de la colección
            if card_id in self.collection:
                del self.collection[card_id]
                self.save_collection()
                self.update_collection_display()
                self.update_collection_total()  # Actualizar el contador total
                self.update_status(f"Todas las copias de {name} (ID: {card_id}) eliminadas")
                
                # Limpiar imagen e información
                self.card_image_collection.config(image='')
                self.card_image_collection.image = None
                self.card_info_collection.config(text=LANG["info_select_card"])

    def load_decks_list(self):
        """Carga la lista de decks disponibles"""
        self.decks = []
        if os.path.exists(self.decks_path):
            for filename in os.listdir(self.decks_path):
                if filename.startswith("deck") and filename.endswith(".txt"):
                    deck_path = os.path.join(self.decks_path, filename)
                    deck_name = self.get_deck_name(deck_path)
                    self.decks.append((filename, deck_name))
        
        # Actualizar combobox
        self.deck_combo['values'] = [name for _, name in self.decks]
        if self.decks:
            self.deck_combo.current(0)
            self.on_deck_selected()
    
    def get_deck_name(self, deck_path):
        """Obtiene el nombre del deck desde el archivo"""
        try:
            with open(deck_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('#NAME:'):
                    return first_line[6:].strip()
        except:
            pass
        return os.path.basename(deck_path).replace('.txt', '')
    
    def on_deck_selected(self, event=None):
        """Carga el deck seleccionado"""
        deck_name = self.deck_var.get()
        if not deck_name:
            return
        
        # Encontrar el archivo correspondiente
        filename = None
        for f, name in self.decks:
            if name == deck_name:
                filename = f
                break
        
        if not filename:
            return
        
        deck_path = os.path.join(self.decks_path, filename)
        self.current_deck_path = deck_path
        self.current_deck_filename = filename
        
        # Cargar nombre del deck
        self.deck_name_var.set(deck_name)
        
        # Cargar cartas del deck
        self.deck_cards = {}
        try:
            with open(deck_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#NAME:'):
                        continue
                    if line and line.isdigit():
                        card_id = line
                        self.deck_cards[card_id] = self.deck_cards.get(card_id, 0) + 1
        except Exception as e:
            logging.error(f"Error loading deck: {str(e)}")
            messagebox.showerror("Error", f"Could not load deck: {str(e)}")
        
        self.update_deck_display()
        self.update_deck_total()  # Actualizar el contador total
        self.update_status(f"Deck loaded: {deck_name} - {len(self.deck_cards)} unique cards")
    
    def update_deck_display(self):
        """Actualiza la visualización del deck con nueva columna Type"""
        self.deck_tree.delete(*self.deck_tree.get_children())
        
        if not self.deck_cards:
            return
        
        try:
            # Obtener detalles de las cartas en el deck
            card_ids = list(self.deck_cards.keys())
            placeholders = ','.join('?' for _ in card_ids)
            
            self.cursor.execute(f"""
                SELECT id, nombre, mana, set_nombre, tipo 
                FROM cartas 
                WHERE id IN ({placeholders})
            """, card_ids)
            
            card_details = {row[0]: (row[1], row[2], row[3], row[4]) for row in self.cursor.fetchall()}
            
            # Insertar en el treeview
            for card_id, count in self.deck_cards.items():
                if card_id in card_details:
                    name, mana, set_name, card_type = card_details[card_id]
                    self.deck_tree.insert('', tk.END, values=(card_id, name, mana, set_name, count, card_type))
                else:
                    self.cursor.execute("SELECT nombre, mana, set_nombre, tipo FROM cartas WHERE id = ?", (card_id,))
                    result = self.cursor.fetchone()
                    if result:
                        name, mana, set_name, card_type = result
                        self.deck_tree.insert('', tk.END, values=(card_id, name, mana, set_name, count, card_type))
                    else:
                        self.deck_tree.insert('', tk.END, values=(card_id, "Card not found", "", "Unknown set", count, ""))
        
        except sqlite3.Error as e:
            logging.error(f"Error loading deck details: {str(e)}")
        
        # Actualizar el contador total
        self.update_deck_total()

    def increment_deck_card_quantity(self):
        """Incrementa en 1 la cantidad de la carta seleccionada en el deck"""
        selected_items = self.deck_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Select a card from the deck.")
            return

        # Solo la primera selección
        item = selected_items[0]
        values = self.deck_tree.item(item, 'values')
        if not values or len(values) < 6:
            return

        card_id = values[0]
        current_quantity = int(values[4])
        new_quantity = current_quantity + 1

        # Actualizar en el diccionario de cartas del deck
        self.deck_cards[card_id] = new_quantity

        # Actualizar la fila en el treeview
        self.deck_tree.item(item, values=(card_id, values[1], values[2], values[3], new_quantity, values[5]))

        # Actualizar la información de la carta si está seleccionada
        if self.deck_tree.selection() == selected_items:
            self.on_deck_card_select(None)
            
        # Actualizar el contador total
        self.update_deck_total()

    def decrement_deck_card_quantity(self):
        """Reduce en 1 la cantidad de la carta seleccionada en el deck. Si llega a 0, la elimina."""
        selected_items = self.deck_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Select a card from the deck.")
            return

        item = selected_items[0]
        values = self.deck_tree.item(item, 'values')
        if not values or len(values) < 6:
            return

        card_id = values[0]
        current_quantity = int(values[4])
        new_quantity = current_quantity - 1

        if new_quantity <= 0:
            # Eliminar la carta del deck
            del self.deck_cards[card_id]
            self.deck_tree.delete(item)
        else:
            # Actualizar cantidad
            self.deck_cards[card_id] = new_quantity
            self.deck_tree.item(item, values=(card_id, values[1], values[2], values[3], new_quantity, values[5]))

        # Actualizar la información de la carta si está seleccionada
        if self.deck_tree.selection() == selected_items and new_quantity > 0:
            self.on_deck_card_select(None)
        else:
            # Si se eliminó, limpiar la imagen y la información
            self.deck_card_image.config(image='')
            self.deck_card_image.image = None
            self.deck_card_info.config(text=LANG["info_select_card"])
            
        # Actualizar el contador total
        self.update_deck_total()
    
    def create_new_deck(self):
        """Crea un nuevo deck"""
        deck_name = simpledialog.askstring(LANG["button_new_deck"], LANG["msg_new_deck"])
        if not deck_name:
            return
        
        # Encontrar el próximo número de deck disponible
        deck_number = self.get_next_deck_number()
        filename = f"deck{deck_number}.txt"
        deck_path = os.path.join(self.decks_path, filename)
        
        # Crear archivo con nombre
        with open(deck_path, 'w', encoding='utf-8') as f:
            f.write(f"#NAME:{deck_name}\n")
        
        # Actualizar lista de decks
        self.decks.append((filename, deck_name))
        self.deck_combo['values'] = [name for _, name in self.decks]
        self.deck_combo.set(deck_name)
        
        # Limpiar deck actual
        self.deck_cards = {}
        self.update_deck_display()
        self.deck_name_var.set(deck_name)
        self.current_deck_path = deck_path
        self.current_deck_filename = filename
        
        self.update_status(f"New deck created: {deck_name}")
        messagebox.showinfo("Success", LANG["msg_deck_created"])
    
    def rename_deck(self):
        """Renombra el deck actual"""
        if not hasattr(self, 'current_deck_path') or not self.current_deck_path:
            messagebox.showinfo("Error", LANG["msg_no_deck_selected"])
            return
        
        new_name = simpledialog.askstring(LANG["button_rename_deck"], LANG["msg_rename_deck"], 
                                         initialvalue=self.deck_name_var.get())
        if not new_name:
            return
        
        # Actualizar archivo
        lines = []
        try:
            with open(self.current_deck_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('#NAME:'):
                        lines.append(f"#NAME:{new_name}\n")
                    else:
                        lines.append(line)
            
            with open(self.current_deck_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        except Exception as e:
            logging.error(f"Error renaming deck: {str(e)}")
            messagebox.showerror("Error", f"Could not rename deck: {str(e)}")
            return
        
        # Actualizar UI
        self.deck_name_var.set(new_name)
        
        # Actualizar lista de decks
        for i, (filename, name) in enumerate(self.decks):
            if filename == self.current_deck_filename:
                self.decks[i] = (filename, new_name)
                break
        
        self.deck_combo['values'] = [name for _, name in self.decks]
        self.deck_combo.set(new_name)
        
        self.update_status(f"Deck renamed to: {new_name}")
        messagebox.showinfo("Success", LANG["msg_deck_renamed"])
    
    def delete_deck(self):
        """Elimina el deck seleccionado"""
        if not hasattr(self, 'current_deck_path') or not self.current_deck_path:
            messagebox.showinfo("Error", LANG["msg_no_deck_selected"])
            return
        
        deck_name = self.deck_name_var.get()
        if not messagebox.askyesno("Confirm", LANG["msg_confirm_delete"].format(name=deck_name)):
            return
        
        try:
            os.remove(self.current_deck_path)
            
            # Actualizar lista de decks
            self.decks = [d for d in self.decks if d[0] != self.current_deck_filename]
            self.deck_combo['values'] = [name for _, name in self.decks]
            
            if self.decks:
                self.deck_combo.current(0)
                self.on_deck_selected()
            else:
                self.deck_combo.set('')
                self.deck_name_var.set('')
                self.deck_cards = {}
                self.update_deck_display()
                self.current_deck_path = None
                self.current_deck_filename = None
            
            self.update_status(f"Deck deleted: {deck_name}")
            messagebox.showinfo("Success", LANG["msg_deck_deleted"])
        except Exception as e:
            logging.error(f"Error deleting deck: {str(e)}")
            messagebox.showerror("Error", f"Could not delete deck: {str(e)}")
    
    def save_current_deck(self):
        """Guarda el deck actual"""
        if not hasattr(self, 'current_deck_path') or not self.current_deck_path:
            messagebox.showinfo("Error", LANG["msg_no_deck_selected"])
            return
        
        deck_name = self.deck_name_var.get().strip()
        if not deck_name:
            messagebox.showinfo("Error", "Deck name cannot be empty")
            return
        
        try:
            with open(self.current_deck_path, 'w', encoding='utf-8') as f:
                f.write(f"#NAME:{deck_name}\n")
                for card_id, count in self.deck_cards.items():
                    for _ in range(count):
                        f.write(f"{card_id}\n")
            
            self.update_status(f"Deck saved: {deck_name}")
            messagebox.showinfo("Success", LANG["msg_deck_saved"])
        except Exception as e:
            logging.error(f"Error saving deck: {str(e)}")
            messagebox.showerror("Error", f"Could not save deck: {str(e)}")
    
    def export_deck(self):
        """Exporta el deck en formato legible"""
        if not hasattr(self, 'current_deck_path') or not self.current_deck_path:
            messagebox.showinfo("Error", LANG["msg_no_deck_selected"])
            return
        
        deck_name = self.deck_name_var.get()
        file_path = filedialog.asksaveasfilename(
            title="Export Deck",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            defaultextension=".txt",
            initialfile=f"{deck_name}.txt"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as out_file:
                out_file.write(f"#NAME:{deck_name}\n")
                
                for card_id, count in self.deck_cards.items():
                    # Obtener detalles de la carta
                    self.cursor.execute("SELECT nombre, set_nombre FROM cartas WHERE id = ?", (card_id,))
                    result = self.cursor.fetchone()
                    
                    if result:
                        name, set_name = result
                        set_name = set_name if set_name else "Unknown"
                        out_file.write(f"{name} ({set_name}) *{count}\n")
                    else:
                        out_file.write(f"Unknown Card (ID: {card_id}) *{count}\n")
            
            self.update_status(f"Deck exported: {file_path}")
            messagebox.showinfo("Success", f"Deck successfully exported to:\n{file_path}")
        except Exception as e:
            logging.error(f"Error exporting deck: {str(e)}")
            messagebox.showerror("Error", f"Could not export deck: {str(e)}")
    
    def import_deck_to_deck(self):
        """Importa un deck al deck actual"""
        if not hasattr(self, 'current_deck_path') or not self.current_deck_path:
            messagebox.showinfo("Error", LANG["msg_no_deck_selected"])
            return
        
        file_path = filedialog.askopenfilename(
            title="Select Deck File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                deck_lines = f.readlines()
            
            cards = []  # Lista de tuplas (card_id, quantity)
            imported_deck_name = "Imported Deck"
            total_copies = 0
            
            # Expresión regular para analizar las líneas del deck
            card_pattern = re.compile(r'(.+?)\s*(?:\(([^)]+)\))?\s*\*?(\d+)?$')
            
            for line in deck_lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Extraer nombre del deck
                if line.startswith('#NAME:'):
                    imported_deck_name = line.split(':', 1)[1].strip()
                    continue
                    
                # Buscar cartas con el patrón
                match = card_pattern.match(line)
                if not match:
                    # Intentar formato de ID directo (ej: "123456 4")
                    if line.replace(' ', '').isdigit() or ' ' in line:
                        parts = line.split()
                        if len(parts) == 1 and parts[0].isdigit():
                            card_id = parts[0]
                            cards.append((card_id, 1))
                            self.add_to_deck(card_id, 1)
                            total_copies += 1
                        elif len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                            card_id = parts[0]
                            quantity = int(parts[1])
                            cards.append((card_id, quantity))
                            self.add_to_deck(card_id, quantity)
                            total_copies += quantity
                    continue
                    
                card_name = match.group(1).strip()
                set_name = match.group[2].strip() if match.group[2] else None
                quantity = int(match.group[3]) if match.group[3] else 1
                
                # Buscar la carta en la base de datos
                query = "SELECT id FROM cartas WHERE nombre = ?"
                params = [card_name]
                
                if set_name:
                    query += " AND set_nombre = ?"
                    params.append(set_name)
                    
                self.cursor.execute(query + " LIMIT 1", params)
                result = self.cursor.fetchone()
                
                if result:
                    card_id = result[0]
                    cards.append((card_id, quantity))
                    # Agregar al deck
                    self.add_to_deck(card_id, quantity)
                    total_copies += quantity
                else:
                    logging.warning(f"Card not found: {card_name} ({set_name})")
            
            if cards:
                self.update_deck_display()
                self.save_current_deck()
                messagebox.showinfo("Success", 
                    f"Deck imported!\n"
                    f"Cards added: {len(cards)} unique, {total_copies} total copies")
                self.update_status(f"Deck imported: {len(cards)} cards")
            else:
                messagebox.showwarning("Empty Deck", "No valid cards found in the file")
            
        except Exception as e:
            logging.exception("Error importing deck")
            messagebox.showerror("Error", f"Could not import deck:\n{str(e)}")
    
    def add_to_deck(self, card_id, quantity=1):
        """Agrega una carta al deck actual"""
        current = self.deck_cards.get(card_id, 0)
        self.deck_cards[card_id] = current + quantity
    
    def open_add_card_to_deck_dialog(self):
        """Abre un diálogo para buscar cartas y agregar al deck actual"""
        # Verificar que haya un deck seleccionado
        if not hasattr(self, 'current_deck_path') or not self.current_deck_path:
            messagebox.showinfo("Error", LANG["msg_no_deck_selected"])
            return

        # Crear ventana de diálogo
        dialog = tk.Toplevel(self.root)
        dialog.title(LANG["title_add_card_dialog"])
        dialog.geometry("900x700")  # Tamaño más cuadrado
        dialog.transient(self.root)
        dialog.grab_set()

        # Frame principal con padding
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Frame de búsqueda con diseño mejorado
        search_frame = ttk.LabelFrame(main_frame, text="Buscar Cartas", padding=10)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)  # Dar peso al campo de búsqueda

        # Etiqueta y campo de búsqueda
        ttk.Label(search_frame, text=LANG["label_search_card"], 
                 foreground=THEME_TEXT).grid(row=0, column=0, padx=5, sticky="w")
        search_entry = ttk.Entry(search_frame)
        search_entry.grid(row=0, column=1, padx=5, sticky="ew")
        search_entry.focus()

        # Botones en el mismo frame
        button_container = ttk.Frame(search_frame)
        button_container.grid(row=0, column=2, padx=(10, 0))

        # Botón de búsqueda
        search_button = ttk.Button(button_container, text=LANG["button_search"], 
                                  width=10, command=lambda: perform_search())
        search_button.pack(side=tk.LEFT, padx=5)

        # Botón de agregar con icono (opcional)
        add_button = ttk.Button(button_container, text=LANG["button_add_to_deck_dialog"], 
                               width=15, command=lambda: add_selected_cards())
        add_button.pack(side=tk.LEFT, padx=5)

        # Contenedor para resultados
        results_frame = ttk.Frame(main_frame)
        results_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Treeview para resultados con scrollbars integradas
        columns = ("ID", "Name", "Set", "Rarity", "Type")
        result_tree = ttk.Treeview(results_frame, columns=columns, show="headings", selectmode="extended")
        
        # Configurar columnas
        col_widths = [80, 300, 150, 100, 150]  # Nuevo ancho para Type
        for col, width in zip(columns, col_widths):
            result_tree.heading(col, text=col)
            result_tree.column(col, width=width, minwidth=50, anchor=tk.W if col != "ID" else tk.CENTER)

        # Scrollbars
        vsb = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=result_tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=result_tree.xview)
        result_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Layout con grid para mejor control
        result_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Frame para botones inferiores
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=2, column=0, sticky="e", pady=(15, 5))

        # Botón de cerrar
        close_button = ttk.Button(bottom_frame, text="Cerrar", 
                                 command=dialog.destroy)
        close_button.pack(side=tk.RIGHT, padx=5)

        # Función de búsqueda
        def perform_search():
            query = search_entry.get().strip()
            if not query:
                return
            
            result_tree.delete(*result_tree.get_children())
            
            try:
                # Búsqueda mejorada: nombre, tipo o texto
                self.cursor.execute("""
                    SELECT id, nombre, set_nombre, rarity, tipo 
                    FROM cartas 
                    WHERE nombre LIKE ? 
                       OR tipo LIKE ?
                       OR texto LIKE ?
                    ORDER BY nombre
                    LIMIT 1000  -- Limitar resultados para mejor rendimiento
                """, (f'%{query}%', f'%{query}%', f'%{query}%'))
                
                results = self.cursor.fetchall()
                
                if not results:
                    messagebox.showinfo("Sin resultados", "No se encontraron cartas")
                    return
                
                for card in results:
                    result_tree.insert('', tk.END, values=card)
                    
            except sqlite3.Error as e:
                logging.error(f"Database error: {e}")
                messagebox.showerror("Error", f"Error de base de datos: {str(e)}")

        # Función para agregar cartas seleccionadas
        def add_selected_cards():
            selected_items = result_tree.selection()
            if not selected_items:
                messagebox.showinfo("Info", "Selecciona al menos una carta")
                return

            added_count = 0
            for item in selected_items:
                values = result_tree.item(item, 'values')
                if values:
                    card_id = values[0]
                    
                    # Agregar al deck actual (1 copia por carta)
                    self.add_to_deck(card_id, 1)
                    
                    # Agregar a la colección principal
                    current = self.collection.get(card_id, 0)
                    self.collection[card_id] = current + 1
                    
                    added_count += 1

            # Actualizar datos
            self.save_collection()
            self.update_collection_display()
            self.update_deck_display()
            self.update_deck_total()
            
            dialog.destroy()
            messagebox.showinfo("Éxito", 
                               f"Se agregaron {added_count} cartas al deck y colección")

        # Permitir buscar al presionar Enter
        search_entry.bind('<Return>', lambda e: perform_search())
        
        # Centrar diálogo
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'+{x}+{y}')
        
    # ===== FUNCIONES PARA ORDENAMIENTO Y TOTALES =====
    
    def sort_treeview(self, tree, column, reverse):
        """Ordena un Treeview por la columna seleccionada"""
        items = [(tree.set(item, column), item) for item in tree.get_children('')]
        
        # Determinar el tipo de datos para ordenar adecuadamente
        if column == "ID" or column == "Cantidad" or column == "Quantity":
            # Ordenar como números
            try:
                items.sort(key=lambda t: int(t[0]) if t[0].isdigit() else 0, reverse=reverse)
            except:
                items.sort(key=lambda t: t[0], reverse=reverse)
        else:
            # Ordenar como texto
            items.sort(key=lambda t: t[0].lower(), reverse=reverse)
        
        # Reordenar los ítems en el Treeview
        for index, (val, item) in enumerate(items):
            tree.move(item, '', index)
        
        # Alternar la dirección para el próximo clic
        tree.heading(column, command=lambda: self.sort_treeview(tree, column, not reverse))
    
    def update_collection_total(self):
        """Actualiza el contador total de cartas en la colección"""
        if not hasattr(self, 'collection'):
            return
            
        total_cards = sum(self.collection.values())
        unique_cards = len(self.collection)
        self.collection_total_var.set(f"Total cards: {total_cards} ({unique_cards} unique)")
    
    def update_deck_total(self):
        """Actualiza el contador total de cartas en el deck"""
        if not hasattr(self, 'deck_cards'):
            return
            
        total_cards = sum(self.deck_cards.values())
        unique_cards = len(self.deck_cards)
        self.deck_total_var.set(f"Total cards: {total_cards} ({unique_cards} unique)")

    def on_closing(self):
        self.conn.close()
        self.clean_temp_folder()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WagicCollectionManager(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
