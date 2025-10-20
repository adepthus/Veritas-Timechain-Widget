# -*- coding: utf-8 -*-
"""
TimeChain Watermark Widget v21.0.12 "Stabile"

Cel główny:
W pełni wielojęzyczna, dopracowana i zoptymalizowana aplikacja desktopowa,
z inteligentnym wykrywaniem właściwości monitorów i pełną obsługą szablonów
w nazwach plików.

OPIS WERSJI (v21.0.12 "Stabile"):
- KRYTYCZNA POPRAWKA: Naprawiono błąd `SyntaxError` w metodzie `apply`,
  który był spowodowany nieprawidłowym użyciem instrukcji `if` w łańcuchu
  poleceń. Metoda została przepisana zgodnie ze standardami, co przywróciło
  działanie przycisku "Zastosuj" w ustawieniach.
- ZACHOWANIE FUNKCJI: Aplikacja jest w pełni funkcjonalna i zawiera wszystkie
  poprawki i funkcje z poprzednich wersji.
"""
from __future__ import annotations

# --- Standard Library Imports ---
import datetime
import hashlib
import json
import logging
import os
import platform
import random
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple

# --- GUI Library Imports (Tkinter) ---
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, font as tkfont, ttk

# --- Metadata ---
APP_VERSION = "21.0.12"
APP_CODENAME = "Stabile"
CONFIG_FILENAME = f"timechain_config_v15.json"

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# --- Dependency Availability Management ---
try:
    from PIL import (Image, ImageGrab, PngImagePlugin, ImageDraw, ImageFont, ImageTk)
except ImportError:
    logging.critical("Krytyczny błąd: Brak modułu Pillow (PIL). Aplikacja nie może działać.")
    messagebox.showerror("Błąd krytyczny", "Nie znaleziono biblioteki Pillow (PIL).\nZainstaluj ją komendą: pip install Pillow")
    sys.exit(1)

_OPTIONAL_DEPENDENCIES: Dict[str, bool] = {
    'requests': False, 'mss': False, 'cv2': False, 'numpy': False,
    'pynput': False, 'pyperclip': False, 'screeninfo': False, 'simpleaudio': False,
    'qrcode': False
}
try: import requests; _OPTIONAL_DEPENDENCIES['requests'] = True
except ImportError: logging.warning("Brak 'requests'. Pobieranie danych z publicznych API będzie niemożliwe.")
try: import mss; _OPTIONAL_DEPENDENCIES['mss'] = True
except ImportError: logging.warning("Brak 'mss'. Przechwytywanie ekranu będzie wolniejsze lub niemożliwe dla wideo.")
try: import cv2; _OPTIONAL_DEPENDENCIES['cv2'] = True
except ImportError: logging.warning("Brak 'opencv-python'. Nagrywanie wideo niedostępne.")
try: import numpy as np; _OPTIONAL_DEPENDENCIES['numpy'] = True
except ImportError: logging.warning("Brak 'numpy'. Nagrywanie wideo i zaawansowana analiza obrazu niedostępne.")
try: from pynput import keyboard; _OPTIONAL_DEPENDENCIES['pynput'] = True
except ImportError: logging.warning("Brak 'pynput'. Globalne skróty klawiszowe niedostępne.")
try: import pyperclip; _OPTIONAL_DEPENDENCIES['pyperclip'] = True
except ImportError: logging.warning("Brak 'pyperclip'. Kopiowanie do schowka niedostępne.")
try: from screeninfo import get_monitors; _OPTIONAL_DEPENDENCIES['screeninfo'] = True
except ImportError: logging.warning("Brak 'screeninfo'. Wybór monitora ograniczony.")
try: import simpleaudio as sa; _OPTIONAL_DEPENDENCIES['simpleaudio'] = True
except ImportError: logging.warning("Brak 'simpleaudio'. Funkcje dźwiękowe niedostępne.")
try: import qrcode; _OPTIONAL_DEPENDENCIES['qrcode'] = True
except ImportError: logging.warning("Brak 'qrcode'. Dynamiczny kod QR niedostępny. Zainstaluj: pip install qrcode[pil]")


# --- Global Constants & Helper Functions ---
REQUESTS_TIMEOUT = 10

def _is_windows() -> bool: return platform.system() == "Windows"

def set_dpi_awareness_windows() -> None:
    if _is_windows():
        try:
            from ctypes import windll, c_void_p
            awareness_context = c_void_p(-4) # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            windll.user32.SetProcessDpiAwarenessContext(awareness_context)
            logging.info("Ustawiono DPI awareness (Per-Monitor V2) dla Windows.")
        except (AttributeError, TypeError):
            try:
                from ctypes import windll
                windll.user32.SetProcessDPIAware()
                logging.info("Ustawiono DPI awareness (starsza metoda) dla Windows.")
            except Exception as e:
                logging.warning(f"Nie udało się ustawić DPI awareness: {e}")

class LanguageManager:
    """Manages all translations and language settings."""
    def __init__(self, app: "TimechainApp", initial_lang: str = "en"):
        self.app = app
        self.language_map = {"Polski": "pl", "English": "en"}
        self.translations = {
            'pl': {
                "lang_name": "Polski", "settings_title": "Ustawienia - Timechain Widget v{version}", "apply_button": "Zastosuj", "close_button": "Zamknij", "apply_success": "Ustawienia zapisane.", "lang_changed_title": "Zmiana języka", "lang_changed_msg": "Język został zmieniony. Interfejs ustawień zostanie odświeżony.", "tab_template": "Szablon i Wygląd", "tab_capture": "Przechwytywanie", "tab_data": "Dane i Integracje", "tab_about": "O programie", "ctx_copy": "Kopiuj tekst", "ctx_pyblock": "Uruchom PyBlock (w konsoli)...", "ctx_settings": "Ustawienia...", "ctx_stamp": "Zapisz stempel...", "ctx_close": "Zamknij", "general_lang_label": "Język:", "template_creator_title": "Kreator Szablonu", "samples_btn": "Przykłady...", "date_btn": "Data...", "time_btn": "Czas...", "separator_btn": "Separator...", "special_btn": "Specjalne...", "reset_btn": "Reset", "appearance_title": "Wygląd i Opcje", "font_label": "Czcionka:", "size_label": "Rozmiar:", "bold_chk": "Pogrubienie", "italic_chk": "Kursywa", "color_text_btn": "Kolor tekstu", "color_shadow_btn": "Kolor cienia", "use_shadow_chk": "Użyj cienia", "thickness_label": "Grubość:", "style_label": "Styl:", "direction_label": "Kierunek:", "style_outline": "Obrys", "style_3d": "Cień 3D", "dir_dr": "Prawy-Dół", "dir_dl": "Lewy-Dół", "dir_ur": "Prawy-Góra", "dir_ul": "Lewy-Góra", "gen_glyph_chk": "Generuj glif:", "insert_glyph_btn": "Wstaw", "full_hash_chk": "Wyświetlaj pełny hash bloku", "lock_position_chk": "Zablokuj pozycję", "always_on_top_chk": "Zawsze na wierzchu", "hotkeys_title": "Skróty Klawiszowe", "hotkeys_desc": "Cały ekran (PNG/MP4/GIF): Ctrl + Shift + 1 / 2 / 3\nZaznaczony obszar (PNG/MP4/GIF): Ctrl + Alt + 1 / 2 / 3", "capture_options_title": "Opcje Przechwytywania", "capture_monitor_label": "Przechwytywany monitor:", "capture_all_screens": "Wszystkie ekrany", "primary_monitor_tag": " (Główny)", "hide_widget_chk": "Ukryj widget podczas przechwytywania", "recording_options_title": "Opcje Nagrywania", "video_duration_label": "Długość wideo (s):", "gif_duration_label": "Długość GIF (s):", "path_title": "Lokalizacja i Nazwa Plików", "change_btn": "Zmień...", "prefix_chk": "Używaj prefiksu w nazwie pliku:", "prefix_template_creator_title": "Kreator Szablonu Prefiksu", "watermark_title": "Znak Wodny (Odcisk Widgeta)", "line_1_chk": "Linia 1", "line_2_chk": "Linia 2", "line_3_chk": "Linia 3", "opacity_label": "Krycie (%):", "angle_label": "Kąt (°):", "watermark_style_label": "Styl:", "watermark_style_tiled": "Kafelki", "watermark_style_arranged": "Aranżowany", "watermark_style_single": "Pojedynczy (skalowany)", "watermark_style_vertical": "Wyrównany w pionie", "watermark_style_qrcode": "Kod QR", "watermark_count_label": "Liczba:", "watermark_use_shadow_chk": "Użyj cienia", "watermark_auto_scale_chk": "Skaluj automatycznie (rozmiar, kąt)", "watermark_qr_size_label": "Rozmiar QR Kodu:", "watermark_qr_position_label": "Pozycja QR Kodu:", "pos_center": "Środek", "pos_tl": "Górny-Lewy", "pos_tr": "Górny-Prawy", "pos_bl": "Dolny-Lewy", "pos_br": "Dolny-Prawy", "glyph_mech_title": "Mechanizm Glifów", "glyph_desc": "Glif to unikalny, stylizowany identyfikator wizualny, który reprezentuje podany przez Ciebie tekst (np. nazwę projektu, pseudonim lub hasło). Działa jak cyfrowy 'symbol' lub 'sigil' – jest zawsze taki sam dla tego samego tekstu, ale zupełnie inny nawet po drobnej zmianie.\n\n**Instrukcja:**\n1. Wpisz swoje słowa-klucze w polu 'Generuj glif' w zakładce 'Szablon i Wygląd'.\n2. Użyj przycisku 'Wstaw' obok pola, aby dodać znacznik `%glyph%` w wybranym miejscu szablonu.", "node_title": "Własny Węzeł ₿itcoina", "use_node_chk": "Użyj własnego węzła", "rpc_url_label": "RPC URL:", "user_label": "Użytkownik:", "pass_label": "Hasło:", "pyblock_title": "Integracja z PyBlock", "pyblock_cmd_label": "Komenda uruchamiająca PyBlock:", "about_info_title": "Informacje", "about_author": "Autor: Wojciech 'adepthus' Durmaj", "about_desc": "Narzędzie służące do trwałego osadzania dowodu istnienia danych w czasie (timestamping) poprzez powiązanie ich z publicznym timechainem ₿itcoina. Aplikacja wyświetla aktualne informacje o ostatnim bloku i pozwala na tworzenie cyfrowych 'stempli' oraz wizualnych znaków wodnych, które mogą służyć jako kryptograficzny dowód, że dane istniały w określonym momencie.", "about_instruction_title": "Do Czego Służy Timechain Widget?", "about_instruction_desc": "Timechain Widget to \"cyfrowa pieczęć notarialna\", która pozwala na błyskawiczne tworzenie niepodważalnych, datowanych dowodów cyfrowych. Jego zadaniem jest walka z dezinformacją i \"przedawnieniem\" prawdy poprzez trwałe \"zapieczętowywanie\" dowolnego fragmentu Twojego ekranu w czasie.\n\nJak Działa?\nZa pomocą prostego skrótu klawiszowego, program robi zrzut ekranu (lub nagranie wideo/GIF), pobiera w czasie rzeczywistym dane z publicznego blockchaina Bitcoina (numer i hash ostatniego bloku), a następnie nakłada te informacje na obraz w formie spersonalizowanego znaku wodnego (\"watermarka\"). Zapisany w ten sposób plik staje się \"pieczęcią czasu\" – artefaktem, którego istnienia w danym momencie nie da się podważyć, ponieważ jest on kryptograficznie powiązany z globalnym, zdecentralizowanym zegarem, jakim jest Bitcoin.", "about_glyph_title": "Czym Jest i Jak Działa 'Glif'?", "about_glyph_desc": "Funkcja Glifu:\n\"Glif\" (%glyph%) to Twoja osobista, unikalna sygnatura cyfrowa wpleciona w pieczęć czasu. Nie jest to losowy ciąg znaków. Jest to wizualny \"odcisk palca\" dowolnego tekstu, który wpiszesz – czy to Twojego pseudonimu, nazwy projektu, czy tajnego hasła.\n\nDlaczego to Działa (Mechanizm):\nGlif działa w oparciu o kryptograficzną funkcję skrótu (hash), w tym przypadku SHA-256 (poprzednio SHA-1).\n\n- Wejście: Bierze dowolny tekst, który podasz (np. \"adepthus-was-here\").\n- Przetwarzanie: Przekształca ten tekst w długi, unikalny ciąg znaków (hash).\n- Wizualizacja: Bierze fragment tego hasha (np. pierwsze 8 znaków) i stylizuje go (np. AbCd12Ef), tworząc charakterystyczny, powtarzalny, ale trudny do odgadnięcia \"glif\".\n\nKluczowa Właściwość:\nDzięki właściwościom funkcji skrótu, nawet najmniejsza zmiana w tekście wejściowym (np. dodanie kropki) spowoduje wygenerowanie całkowicie innego glifu. Jednocześnie, ten sam tekst wejściowy zawsze wygeneruje ten sam glif.\n\nW Rezultacie:\nGlif jest Twoim osobistym, tajnym podpisem. Tylko Ty, znając oryginalny tekst (\"ziarno\"), jesteś w stanie odtworzyć ten sam, unikalny wzorzec. Dla reszty świata jest to enigmatyczny, ale konsekwentny znak, który potwierdza Twoje autorstwo na przestrzeni wielu różnych dowodów.", "about_deps_title": "Status zależności", "about_qr_options_title": "Opcje kodu QR", "about_show_qr_chk": "Pokaż kod QR", "about_qr_size_label": "Rozmiar obrazów:", "dep_found": "Znaleziono", "dep_missing": "Brak", "days_full": ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"], "days_abbr": ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"], "months_full": ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"], "months_abbr": ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze", "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"],
            },
            'en': {"lang_name": "English", "settings_title": "Settings - Timechain Widget v{version}", "apply_button": "Apply", "close_button": "Close", "apply_success": "Settings saved.", "lang_changed_title": "Language Change", "lang_changed_msg": "Language has been changed. The settings interface will now refresh.", "tab_template": "Template & Appearance", "tab_capture": "Capture", "tab_data": "Data & Integrations", "tab_about": "About", "ctx_copy": "Copy text", "ctx_pyblock": "Run PyBlock (in console)...", "ctx_settings": "Settings...", "ctx_stamp": "Save stamp...", "ctx_close": "Close", "general_lang_label": "Language:", "template_creator_title": "Template Creator", "samples_btn": "Samples...", "date_btn": "Date...", "time_btn": "Time...", "separator_btn": "Separator...", "special_btn": "Special...", "reset_btn": "Reset", "appearance_title": "Appearance & Options", "font_label": "Font:", "size_label": "Size:", "bold_chk": "Bold", "italic_chk": "Italic", "color_text_btn": "Text color", "color_shadow_btn": "Shadow color", "use_shadow_chk": "Use shadow", "thickness_label": "Thickness:", "style_label": "Style:", "direction_label": "Direction:", "style_outline": "Outline", "style_3d": "3D Shadow", "dir_dr": "Down-Right", "dir_dl": "Down-Left", "dir_ur": "Up-Right", "dir_ul": "Up-Left", "gen_glyph_chk": "Generate glyph:", "insert_glyph_btn": "Insert", "full_hash_chk": "Display full block hash", "lock_position_chk": "Lock position", "always_on_top_chk": "Always on top", "hotkeys_title": "Hotkeys", "hotkeys_desc": "Full Screen (PNG/MP4/GIF): Ctrl + Shift + 1 / 2 / 3\nSelected Region (PNG/MP4/GIF): Ctrl + Alt + 1 / 2 / 3", "capture_options_title": "Capture Options", "capture_monitor_label": "Capture monitor:", "capture_all_screens": "All screens", "primary_monitor_tag": " (Primary)", "hide_widget_chk": "Hide widget on capture", "recording_options_title": "Recording Options", "video_duration_label": "Video duration (s):", "gif_duration_label": "GIF duration (s):", "path_title": "File Location & Naming", "change_btn": "Change...", "prefix_chk": "Use prefix in filename:", "prefix_template_creator_title": "Prefix Template Creator", "watermark_title": "Watermark (Widget Imprint)", "line_1_chk": "Line 1", "line_2_chk": "Line 2", "line_3_chk": "Line 3", "opacity_label": "Opacity (%):", "angle_label": "Angle (°):", "watermark_style_label": "Style:", "watermark_style_tiled": "Tiled", "watermark_style_arranged": "Arranged", "watermark_style_single": "Single (scaled)", "watermark_style_vertical": "Vertical Stack", "watermark_style_qrcode": "QR Code", "watermark_count_label": "Count:", "watermark_use_shadow_chk": "Use shadow", "watermark_auto_scale_chk": "Auto-scale (size, angle)", "watermark_qr_size_label": "QR Code Size:", "watermark_qr_position_label": "QR Code Position:", "pos_center": "Center", "pos_tl": "Top-Left", "pos_tr": "Top-Right", "pos_bl": "Bottom-Left", "pos_br": "Bottom-Right", "glyph_mech_title": "Glyph Mechanism", "glyph_desc": "A glyph is a unique, stylized visual identifier that represents the text you provide (e.g., a project name, nickname, or phrase). It acts like a digital 'symbol' or 'sigil'—it's always the same for the same text but completely different after even a minor change.\n\n**Instructions:**\n1. Enter your keywords in the 'Generate glyph' field in the 'Template & Appearance' tab.\n2. Use the 'Insert' button next to the field to add the `%glyph%` placeholder to your desired template location.", "node_title": "Custom ₿itcoin Node", "use_node_chk": "Use custom node", "rpc_url_label": "RPC URL:", "user_label": "User:", "pass_label": "Password:", "pyblock_title": "PyBlock Integration", "pyblock_cmd_label": "Command to run PyBlock:", "about_info_title": "Information", "about_author": "Author: Wojciech 'adepthus' Durmaj", "about_desc": "A tool for permanently timestamping data by linking it to the public ₿itcoin timechain. The application displays current information about the latest block and allows for the creation of digital 'stamps' and visual watermarks, which can serve as cryptographic proof that the data existed at a specific moment in time.", "about_instruction_title": "What is the Timechain Widget for?", "about_instruction_desc": "The Timechain Widget is a 'digital notary seal' for creating undeniable, dated digital evidence. Its purpose is to combat disinformation by 'sealing' a fragment of your screen in time. Using a keyboard shortcut, the program takes a screenshot, fetches data from the Bitcoin blockchain (block number and hash), and overlays it as a personalized watermark. The saved file becomes a 'timestamp'—an artifact cryptographically linked to the global, decentralized clock that is Bitcoin.", "about_glyph_title": "What is a 'Glyph' and How Does It Work?", "about_glyph_desc": "The 'Glyph' (%glyph%) is your unique digital signature, a visual 'fingerprint' of any text (nickname, project name). It's based on the SHA-256 hash function (formerly SHA-1): it takes text, converts it into a unique hash, and then stylizes a fragment of it (e.g., AbCd12Ef). Even a minor change in the input text creates a completely different glyph, but the same text always yields the same result. It's your personal, secret signature, confirming authorship.", "about_deps_title": "Dependency Status", "about_qr_options_title": "QR Code Options", "about_show_qr_chk": "Show QR Code", "about_qr_size_label": "Image Size:", "dep_found": "Found", "dep_missing": "Missing", "days_full": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "days_abbr": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "months_full": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], "months_abbr": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]},
        }
        self.set_language(initial_lang)

    def set_language(self, lang_code: str):
        self.current_lang_code = lang_code if lang_code in self.translations else "en"
        self.current_lang_strings = self.translations[self.current_lang_code]
        if hasattr(self.app, 'template_engine'):
            self.app.template_engine.on_language_change()

    def get(self, key: str, **kwargs) -> str:
        s = self.current_lang_strings.get(key, f"<{key}>")
        return s.format(**kwargs)

    def get_date_names(self, key: str) -> list:
        return self.current_lang_strings.get(key, [])

    def get_lang_map(self):
        return self.language_map

    def get_lang_name_from_code(self, code: str) -> str:
        for name, c in self.language_map.items():
            if c == code:
                return name
        return "English"

class ConfigManager:
    """Zarządza ładowaniem, zapisywaniem i migracją konfiguracji aplikacji."""
    def __init__(self, filename: str = CONFIG_FILENAME):
        self.config_path = self._get_config_path(filename); self._config_lock = threading.Lock(); self.config = self._load()
    def _get_config_path(self, filename: str) -> str:
        try:
            base_path = os.getenv('APPDATA') if _is_windows() else os.path.expanduser("~")
            app_dir = os.path.join(base_path, ".TimechainWidget"); os.makedirs(app_dir, exist_ok=True); return os.path.join(app_dir, filename)
        except OSError as e: logging.error(f"Nie można utworzyć katalogu konfiguracyjnego: {e}"); return filename
    def get_default_config(self) -> Dict[str, Any]:
        try:
            # Użyj tymczasowego okna root do pobrania informacji o ekranie bez pokazywania okna
            temp_root = tk.Tk()
            temp_root.withdraw()
            screen_height = temp_root.winfo_screenheight()
            temp_root.destroy()
            # Skaluj rozmiar czcionki bazując na 1080p jako punkcie odniesienia dla rozmiaru 15
            scaled_font_size = max(8, round(15 * screen_height / 1080))
            logging.info(f"Wykryto wysokość ekranu {screen_height}px, ustawiono domyślny rozmiar czcionki na {scaled_font_size}pt.")
        except Exception:
            scaled_font_size = 15 # Wartość domyślna w razie błędu
            logging.warning("Nie udało się wykryć rozdzielczości ekranu, użyto domyślnego rozmiaru czcionki.")

        return {"version": APP_VERSION, "language": "pl", "line_1_enabled": True, "prompt_line_1": "'adepthus-was-here' '@' 'timechains'", "line_2_enabled": True, "prompt_line_2": "d MMMM yyyy HH:mm:ss | '₿eattime' @ | 'Block:' %blockheight%", "line_3_enabled": True, "prompt_line_3": "'Hash:' %hash%", "generate_glyphs": True, "glyph_seed": "adepthus-was-here", "font_family": "Segoe UI", "base_font_size": scaled_font_size, "font_weight": "bold", "font_slant": "roman", "text_color": "white", "use_outline": True, "outline_color": "#333333", "outline_thickness": 2, "shadow_style": "outline", "shadow_direction": "down-right", "line_1_align": "left", "line_2_align": "left", "line_3_align": "left", "lock_position": False, "always_on_top": True, "display_full_hash": False, "capture_folder": os.path.join(os.path.expanduser("~"), "Timechain_Captures"), "capture_filename_prefix": "timechain_capture_%blockheight%_", "use_capture_filename_prefix": True, "hide_widget_on_capture": True, "capture_screen": "Wszystkie ekrany", "watermark_style": "tiled", "watermark_arranged_count": 5, "watermark_opacity": 30, "watermark_angle": 30, "watermark_use_shadow": False, "watermark_auto_scale": True, "watermark_qr_code_size": 150, "watermark_qr_position": "center", "video_duration": 10, "gif_duration": 7, "auto_color_inversion": False, "brightness_threshold": 128, "data_fetch_interval_s": 60, "use_custom_node": False, "custom_node_url": "http://127.0.0.1:8332", "custom_node_user": "", "custom_node_pass": "", "pyblock_command": "python -m pyblock" if _is_windows() else "pyblock", "last_position": "+100+100", "about_show_qr_code": True, "about_qr_code_size": 120}
    def _load(self) -> Dict[str, Any]:
        defaults = self.get_default_config()
        if not os.path.exists(self.config_path): self.save(defaults); return defaults
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f: loaded_config = json.load(f)
            updated = False
            for key, value in defaults.items():
                if key not in loaded_config: loaded_config[key] = value; updated = True
            if updated: self.save(loaded_config)
            return loaded_config
        except (json.JSONDecodeError, TypeError, IOError) as e: logging.error(f"Błąd odczytu konfiguracji: {e}. Przywracanie domyślnych."); self.save(defaults); return defaults
    def get(self, key: str, default: Any = None) -> Any:
        with self._config_lock: return self.config.get(key, default)
    def set(self, key: str, value: Any) -> None:
        with self._config_lock: self.config[key] = value
    def save(self, config_data: Optional[Dict[str, Any]] = None) -> None:
        with self._config_lock:
            data_to_save = config_data if config_data is not None else self.config
            try:
                with open(self.config_path, 'w', encoding='utf-8') as f: json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            except IOError as e: logging.error(f"Nie udało się zapisać konfiguracji: {e}")

class DataManager:
    """Zarządza pobieraniem i buforowaniem danych z blockchaina."""
    def __init__(self, app: "TimechainApp"):
        self.app = app; self.config = app.config_manager; self._data_cache: Dict[str, Any] = {"blockheight": "Ładowanie...", "hash_full": "...", "hash_short": "..."}; self._data_lock = threading.Lock()
    def fetch_all_data(self) -> None:
        if not _OPTIONAL_DEPENDENCIES['requests'] and not self.config.get("use_custom_node"):
            logging.error("Brak biblioteki 'requests' uniemożliwia pobieranie danych z publicznych API.")
            with self._data_lock: self._data_cache["error"] = "Brak 'requests'"
            self.app.request_ui_update(); return
        try:
            success = False
            if self.config.get("use_custom_node"): success = self._fetch_from_custom_node(requests)
            if not success and _OPTIONAL_DEPENDENCIES['requests']: success = self._fetch_from_combined_api(requests)
            if not success and _OPTIONAL_DEPENDENCIES['requests']: self._fetch_from_separate_apis(requests)

            with self._data_lock:
                if isinstance(self._data_cache.get("blockheight"), int): self._data_cache.pop("error", None)
                else: self._data_cache["error"] = "Błąd pobierania danych"
        except Exception as e:
            logging.error(f"Nieoczekiwany błąd podczas pobierania danych: {e}")
            with self._data_lock: self._data_cache["error"] = "Błąd sieci"
        finally: self.app.request_ui_update()
    def _fetch_from_custom_node(self, requests_lib) -> bool:
        url = self.config.get("custom_node_url"); auth = (self.config.get("custom_node_user"), self.config.get("custom_node_pass"))
        if not url: return False
        try:
            def rpc_call(method): payload = {'jsonrpc': '1.0', 'id': 'tc', 'method': method}; resp = requests_lib.post(url, json=payload, auth=auth, timeout=REQUESTS_TIMEOUT); resp.raise_for_status(); return resp.json()
            height, hash_val = rpc_call('getblockcount').get('result'), rpc_call('getbestblockhash').get('result')
            if isinstance(height, int) and isinstance(hash_val, str): self._update_cache(height, hash_val); return True
        except requests_lib.RequestException as e: logging.error(f"Błąd połączenia z węzłem ({url}): {e}")
        return False
    def _fetch_from_combined_api(self, requests_lib) -> bool:
        url = "https://blockchain.info/latestblock"
        try:
            response = requests_lib.get(url, timeout=REQUESTS_TIMEOUT); response.raise_for_status(); data = response.json()
            height, hash_val = data.get('height'), data.get('hash')
            if isinstance(height, int) and isinstance(hash_val, str): self._update_cache(height, hash_val); return True
        except requests_lib.RequestException as e: logging.error(f"Błąd pobierania danych z {url}: {e}")
        return False
    def _fetch_from_separate_apis(self, requests_lib) -> None:
        apis = {"height": ["https://blockstream.info/api/blocks/tip/height"], "hash": ["https://blockstream.info/api/blocks/tip/hash"]}; height_str = self._fetch_parallel(requests_lib, apis["height"])
        if height_str and height_str.isdigit():
            with self._data_lock: self._data_cache["blockheight"] = int(height_str)
        if (hash_val := self._fetch_parallel(requests_lib, apis["hash"])) and len(hash_val) == 64:
            if isinstance(current_height := self.get_data_snapshot().get("blockheight", 0), int): self._update_cache(current_height, hash_val)
    def _fetch_parallel(self, requests_lib, urls: List[str]) -> Optional[str]:
        with ThreadPoolExecutor(max_workers=len(urls)) as executor:
            futures = {executor.submit(requests_lib.get, url, timeout=5) for url in urls}
            for future in as_completed(futures):
                try: response = future.result(); response.raise_for_status(); return response.text.strip()
                except requests_lib.RequestException: continue
        return None
    def _update_cache(self, height: int, hash_val: str) -> None:
        with self._data_lock: self._data_cache["blockheight"] = height; self._data_cache["hash_full"] = hash_val; self._data_cache["hash_short"] = f"{hash_val[:6]}...{hash_val[-4:]}"; logging.info(f"Data updated: Block {height}")
    def get_data_snapshot(self) -> Dict[str, Any]:
        with self._data_lock: return self._data_cache.copy()

class TemplateEngine:
    """Odpowiada za renderowanie tekstu widgeta na podstawie szablonów i danych."""
    def __init__(self, app: "TimechainApp"):
        self.app, self.config, self.data_manager, self.lang = app, app.config_manager, app.data_manager, app.lang
        self.special_placeholder_regex = re.compile("(%glyph%|%blockheight%|%hash%|@|'[^']*')"); self.FORMAT_CODE_MAP: Dict = {}; self.dt_format_regex = re.compile('a^'); self.on_language_change()
    def on_language_change(self):
        self.FORMAT_CODE_MAP = {'yyyy': '%Y', 'yy': '%y', 'MMMM': self.lang.get_date_names("months_full"), 'MMM': self.lang.get_date_names("months_abbr"), 'MM': '%m', 'M': lambda dt: str(dt.month), 'dddd': self.lang.get_date_names("days_full"), 'ddd': self.lang.get_date_names("days_abbr"), 'dd': '%d', 'd': lambda dt: str(dt.day), 'HH': '%H', 'H': lambda dt: str(dt.hour), 'hh': '%I', 'h': lambda dt: str(int(dt.strftime('%I'))), 'mm': '%M', 'm': lambda dt: str(dt.minute), 'ss': '%S', 's': lambda dt: str(dt.second), 'SSS': lambda dt: f"{dt.microsecond // 1000:03d}", 'SS': lambda dt: f"{dt.microsecond // 10000:02d}", 'S': lambda dt: f"{dt.microsecond // 100000:d}", 'tt': '%p', 't': lambda dt: dt.strftime('%p')[0] if dt.strftime('%p') else ''}
        self.dt_format_regex = re.compile('(' + '|'.join(map(re.escape, sorted(self.FORMAT_CODE_MAP.keys(), key=len, reverse=True))) + ')'); logging.info(f"Zaktualizowano formaty daty dla języka: {self.lang.current_lang_code}")
    @staticmethod
    def _get_swatch_internet_time() -> str: now_utc = datetime.datetime.now(datetime.timezone.utc); biel_time = now_utc + datetime.timedelta(hours=1); return f"@{int((biel_time.hour * 3600 + biel_time.minute * 60 + biel_time.second) / 86.4):03d}"
    def render(self, config_override: Optional[Dict[str, Any]] = None) -> str:
        data = self.data_manager.get_data_snapshot(); cfg = config_override or self.config.config
        if "error" in data: return f"TimeChain Watermark Widget\n{data['error']}\nSprawdź połączenie..."
        now = datetime.datetime.now(); replacements = {'@': self._get_swatch_internet_time(), '%blockheight%': str(data.get("blockheight", "...")), '%hash%': data.get("hash_full", "...") if cfg.get("display_full_hash") else data.get("hash_short", "..."), '%glyph%': self._generate_glyph(cfg.get("glyph_seed", "")) if cfg.get("generate_glyphs") else ""}
        return '\n'.join([self._render_line(cfg.get(f"prompt_line_{i}", ""), now, replacements) for i in range(1, 4) if cfg.get(f"line_{i}_enabled")])
    def _render_line(self, template: str, now: datetime.datetime, replacements: Dict) -> str:
        parts = self.special_placeholder_regex.split(template); final_string = ""
        for i, part in enumerate(parts):
            if i % 2 == 1: final_string += part[1:-1] if part.startswith("'") and part.endswith("'") else replacements.get(part, part)
            else: final_string += self._format_datetime_in_string(part, now)
        return final_string
    def _format_datetime_in_string(self, text: str, now: datetime.datetime) -> str:
        parts = self.dt_format_regex.split(text); result = ""
        for i, part in enumerate(parts):
            if i % 2 == 1:
                if isinstance(code_map := self.FORMAT_CODE_MAP.get(part), list): result += code_map[now.month - 1 if 'M' in part else now.weekday()]
                elif callable(code_map): result += code_map(now)
                elif code_map: result += now.strftime(code_map)
                else: result += part
            else: result += part
        return result
    def _generate_glyph(self, seed: str) -> str:
        if not (norm := unicodedata.normalize('NFKD', seed).encode('ascii', 'ignore').decode('ascii')): return "........"
        sha = hashlib.sha256(norm.encode()).hexdigest()[:8]; return "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(sha))

class WidgetWindow:
    """Główne okno widgeta, odpowiedzialne za wyświetlanie tekstu i interakcje."""
    def __init__(self, ui_manager: "UIManager"):
        self.ui, self.app, self.master, self.config, self.lang = ui_manager, ui_manager.app, ui_manager.app.master, ui_manager.app.config_manager, ui_manager.app.lang
        self.last_click_pos = (0, 0); self._tk_font: Optional[tkfont.Font] = None; self._current_text: str = ""; self.canvas: Optional[tk.Canvas] = None
    def setup(self) -> None:
        self.master.overrideredirect(True); self.master.attributes('-topmost', self.config.get("always_on_top")); self.master.config(bg='#f0f0f0'); self.master.wm_attributes('-transparentcolor', '#f0f0f0')
        self.canvas = tk.Canvas(self.master, bg='#f0f0f0', highlightthickness=0); self.canvas.pack(); self._update_font(); self._bind_events(); self.master.geometry(self.config.get("last_position", "+100+100"))
    def _update_font(self, font_config: Optional[Dict] = None) -> None: cfg = font_config or self.config.config; self._tk_font = tkfont.Font(family=cfg.get('font_family'), size=cfg.get('base_font_size'), weight=cfg.get('font_weight'), slant=cfg.get('font_slant'))
    def _bind_events(self) -> None:
        if self.canvas: self.canvas.tag_bind("drag_handle", "<ButtonPress-1>", self._on_drag_start); self.canvas.tag_bind("drag_handle", "<B1-Motion>", self._on_drag_motion); self.canvas.bind("<ButtonPress-1>", self._on_drag_start); self.canvas.bind("<B1-Motion>", self._on_drag_motion); self.canvas.bind("<Button-3>", self._show_context_menu)
    def update_display(self, text: str, is_inverted: bool, config_override: Optional[Dict] = None) -> None:
        if not self.master.winfo_exists() or not self.canvas or not self._tk_font: return
        self._current_text = text; cfg = {**self.config.config, **(config_override or {})}; self._update_font(cfg); self.canvas.delete("all")
        text_color, outline_color = (cfg.get("outline_color"), cfg.get("text_color")) if cfg.get("auto_color_inversion") and is_inverted else (cfg.get("text_color"), cfg.get("outline_color"))
        thickness = cfg.get("outline_thickness", 1); lines = text.split('\n'); line_height = self._tk_font.metrics("linespace"); padding = 5; canvas_width = max((self._tk_font.measure(line) for line in lines), default=0) + 2 * padding; canvas_height = line_height * len(lines) + 2 * padding
        self.canvas.create_rectangle(0, 0, 80, line_height + 2 * padding, tags="drag_handle", fill="", outline="")
        y_pos = padding
        for i, line in enumerate(lines):
            align = cfg.get(f"line_{i+1}_align", "left"); anchor = {"left": "nw", "center": "n", "right": "ne"}.get(align, "nw"); x_pos = padding if align == "left" else canvas_width / 2 if align == "center" else canvas_width - padding
            if cfg.get("use_outline") and thickness > 0:
                if cfg.get("shadow_style") == "3d_offset":
                    direction = cfg.get("shadow_direction", "down-right"); ox, oy = (thickness, thickness) if direction == "down-right" else (-thickness, thickness) if direction == "down-left" else (thickness, -thickness) if direction == "up-right" else (-thickness, -thickness); self.canvas.create_text(x_pos + ox, y_pos + oy, text=line, font=self._tk_font, fill=outline_color, anchor=anchor)
                else:
                    for dx, dy in [(dx, dy) for dx in range(-thickness, thickness + 1) for dy in range(-thickness, thickness + 1) if dx or dy]: self.canvas.create_text(x_pos + dx, y_pos + dy, text=line, font=self._tk_font, fill=outline_color, anchor=anchor)
            self.canvas.create_text(x_pos, y_pos, text=line, font=self._tk_font, fill=text_color, anchor=anchor); y_pos += line_height
        self.canvas.config(width=canvas_width, height=canvas_height)
        try: _, x, y = self.master.geometry().split('+'); self.master.geometry(f"{int(canvas_width)}x{int(canvas_height)}+{x}+{y}")
        except (IndexError, ValueError, tk.TclError): self.master.geometry(f"{int(canvas_width)}x{int(canvas_height)}+100+100")
    def _show_context_menu(self, event: tk.Event) -> None:
        popup = tk.Menu(self.master, tearoff=0); popup.add_command(label=self.lang.get("ctx_copy"), command=self._copy_text, state="normal" if _OPTIONAL_DEPENDENCIES['pyperclip'] else "disabled"); popup.add_separator()
        popup.add_command(label=self.lang.get("ctx_pyblock"), command=self.ui.launch_pyblock); popup.add_command(label=self.lang.get("ctx_settings"), command=self.ui.show_settings); popup.add_command(label=self.lang.get("ctx_stamp"), command=self._save_stamp); popup.add_separator()
        popup.add_command(label=self.lang.get("ctx_close"), command=self.app.close_app); popup.tk_popup(event.x_root, event.y_root)
    def get_current_text(self) -> str: return self._current_text
    def _copy_text(self) -> None:
        if _OPTIONAL_DEPENDENCIES['pyperclip'] and (text := self.get_current_text()): pyperclip.copy(text); self.flash("blue")
    def _on_drag_start(self, event: tk.Event) -> None:
        if not self.config.get("lock_position"): self.last_click_pos = (event.x, event.y)
    def _on_drag_motion(self, event: tk.Event) -> None:
        if not self.config.get("lock_position"): x, y = event.x_root - self.last_click_pos[0], event.y_root - self.last_click_pos[1]; self.master.geometry(f"+{x}+{y}")
    def flash(self, color: str, duration_ms: int = 200) -> None:
        if self.master.winfo_exists() and self.canvas: self.canvas.config(bg=color); self.master.after(duration_ms, lambda: self.canvas and self.canvas.config(bg='#f0f0f0'))
    def get_geometry(self) -> Tuple[int, int, int, int]: self.master.update_idletasks(); return self.master.winfo_x(), self.master.winfo_y(), self.master.winfo_width(), self.master.winfo_height()
    def _save_stamp(self):
        data = self.app.data_manager.get_data_snapshot(); content = (f"Timechain Stamp v{self.config.get('version')}\nTimestamp: {datetime.datetime.now().isoformat()}\nBlock: {data.get('blockheight', 'N/A')}\nHash: {data.get('hash_full', 'N/A')}\n")
        if file_path := filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")], initialfile=f"stamp_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt"):
            with open(file_path, 'w', encoding='utf-8') as f: f.write(content)
            self.flash("green")

class ColorAnalyzer(threading.Thread):
    """Wątek analizujący kolor tła pod widgetem w celu automatycznej inwersji kolorów."""
    def __init__(self, app: "TimechainApp"):
        super().__init__(name="ColorAnalyzer", daemon=True); self.app, self.config = app, app.config_manager; self.should_invert = threading.Event(); self._stop_event, self._trigger_check_event = threading.Event(), threading.Event()
    def run(self) -> None:
        time.sleep(2)
        while not self._stop_event.is_set():
            if self._trigger_check_event.wait(timeout=3600) and self.config.get("auto_color_inversion"):
                if self._stop_event.is_set(): break
                self.check_background_brightness(); self._trigger_check_event.clear()
    def trigger_check(self) -> None:
        if self.is_alive(): self._trigger_check_event.set()
    def check_background_brightness(self) -> None:
        try:
            x, y, w, h = self.app.ui_manager.get_widget_geometry(); bbox = {'top': y - 5, 'left': x - 5, 'width': w + 10, 'height': h + 10}
            img = Image.frombytes("RGB", (sct_img := mss.mss().grab(bbox)).size, sct_img.bgra, "raw", "BGRX").convert("L") if _OPTIONAL_DEPENDENCIES['mss'] else ImageGrab.grab(bbox=(bbox['left'], bbox['top'], bbox['left']+bbox['width'], bbox['top']+bbox['height'])).convert("L")
            avg_brightness = np.mean(np.array(img)) if _OPTIONAL_DEPENDENCIES['numpy'] else sum(img.getdata()) / (img.width * img.height); inversion_changed = False
            if avg_brightness > self.config.get("brightness_threshold", 128):
                if not self.should_invert.is_set(): self.should_invert.set(); inversion_changed = True
            elif self.should_invert.is_set(): self.should_invert.clear(); inversion_changed = True
            if inversion_changed: self.app.request_ui_update()
        except Exception as e:
            logging.warning(f"Błąd podczas sprawdzania jasności tła: {e}", exc_info=False)
    def stop(self) -> None: self._stop_event.set(); self._trigger_check_event.set()

class RegionSelector:
    def __init__(self, app_master: tk.Tk, callback: Callable[[Tuple[int, int, int, int]], None]):
        self.master, self.callback = app_master, callback; self.start_x, self.start_y, self.rect = 0, 0, None; self.window = tk.Toplevel(self.master)
        self.window.attributes("-alpha", 0.1); self.window.overrideredirect(True); self.window.attributes("-topmost", True)
        if _OPTIONAL_DEPENDENCIES['screeninfo']:
            monitors = get_monitors(); self.window.geometry(f"{max(m.x + m.width for m in monitors) - min(m.x for m in monitors)}x{max(m.y + m.height for m in monitors) - min(m.y for m in monitors)}+{min(m.x for m in monitors)}+{min(m.y for m in monitors)}")
        else: self.window.geometry(f"{self.master.winfo_screenwidth()}x{self.master.winfo_screenheight()}+0+0")
        self.canvas = tk.Canvas(self.window, cursor="crosshair", bg="black"); self.canvas.pack(fill="both", expand=True); self.canvas.bind("<ButtonPress-1>", self._on_press); self.canvas.bind("<B1-Motion>", self._on_drag); self.canvas.bind("<ButtonRelease-1>", self._on_release)
    def _on_press(self, event: tk.Event): self.start_x, self.start_y = event.x_root, event.y_root; self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=1, fill=None)
    def _on_drag(self, event: tk.Event): self.canvas.coords(self.rect, self.start_x, self.start_y, event.x_root, event.y_root)
    def _on_release(self, event: tk.Event):
        x1, y1, x2, y2 = min(self.start_x, event.x_root), min(self.start_y, event.y_root), max(self.start_x, event.x_root), max(self.start_y, event.y_root); self.window.destroy()
        if abs(x2 - x1) > 5 and abs(y2 - y1) > 5: self.master.after(100, lambda: self.callback(region_bbox=(x1, y1, x2 - x1, y2 - y1)))

class PyBlockLauncher:
    @staticmethod
    def launch(command: str):
        try:
            args = shlex.split(command)
            if _is_windows(): subprocess.Popen(['start', 'cmd', '/k'] + args, shell=True)
            elif platform.system() == "Darwin": subprocess.Popen(['osascript', '-e', f'''tell application "Terminal" to do script "{command}"'''])
            else:
                for term in ['gnome-terminal', 'konsole', 'xterm', 'lxterminal', 'mate-terminal']:
                    if shutil.which(term): subprocess.Popen([term, '--' if term == 'gnome-terminal' else '-e', 'bash', '-c', f'{command}; exec bash'] if term in ['gnome-terminal', 'konsole'] else [term, '-e', command]); return
                messagebox.showerror("Błąd", "Nie znaleziono obsługiwanego emulatora terminala (Linux).")
            logging.info(f"Uruchomiono PyBlock komendą: {command}")
        except Exception as e: logging.error(f"Nie udało się uruchomić PyBlock: {e}"); messagebox.showerror("Błąd Uruchamiania", f"Nie udało się uruchomić komendy:\n{command}\n\nBłąd: {e}")

class CaptureManager:
    """Zarządza przechwytywaniem ekranu, wideo i GIF-ów."""
    def __init__(self, app: "TimechainApp"):
        self.app, self.ui_manager, self.config = app, app.ui_manager, app.config_manager
        self._hotkey_listener: Optional[keyboard.GlobalHotKeys] = None; self.region_selector: Optional[RegionSelector] = None
        self._capture_lock = threading.Lock()

    def _generate_arranged_positions(self, base_width: int, base_height: int, font) -> List[Tuple[int, int]]:
        watermark_text = self.app.ui_manager.widget_window.get_current_text()
        active_lines = [line for i, line in enumerate(watermark_text.split('\n')) if self.config.get(f"watermark_include_line{i+1}") and line.strip()]
        if not active_lines: return []
        
        full_text = "\n".join(active_lines)
        positions = []
        
        temp_draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        bbox = temp_draw.textbbox((0, 0), full_text, font=font)
        w_width, w_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

        grid_map = {1: [4], 3: [0, 4, 8], 5: [0, 2, 4, 6, 8], 7: [0, 2, 3, 4, 5, 6, 8]}
        count = self.config.get("watermark_arranged_count", 5)
        
        for i in grid_map.get(count, [4]):
            row, col = divmod(i, 3)
            cell_width, cell_height = base_width / 3, base_height / 3
            x = (col + 0.5) * cell_width - w_width / 2
            y = (row + 0.5) * cell_height - w_height / 2
            positions.append((x, y))
            
        return positions

    def start_hotkey_listener(self) -> None:
        if not _OPTIONAL_DEPENDENCIES['pynput']: return
        hotkeys = {'<ctrl>+<shift>+1': self.capture_screenshot, '<ctrl>+<shift>+2': self.capture_video, '<ctrl>+<shift>+3': self.capture_gif, '<ctrl>+<alt>+1': lambda: self._start_region_capture(self.capture_screenshot), '<ctrl>+<alt>+2': lambda: self._start_region_capture(self.capture_video), '<ctrl>+<alt>+3': lambda: self._start_region_capture(self.capture_gif)}
        try: self._hotkey_listener = keyboard.GlobalHotKeys(hotkeys); self._hotkey_listener.start(); logging.info("Skróty aktywne: Ekran(Ctrl+Shift+1/2/3) | Region(Ctrl+Alt+1/2/3) dla PNG/MP4/GIF.")
        except Exception as e: logging.error(f"Nie udało się uruchomić nasłuchu skrótów: {e}")
    def _start_region_capture(self, callback: Callable):
        if self.region_selector and self.region_selector.window.winfo_exists(): return
        self.region_selector = RegionSelector(self.app.master, callback)
    def stop_hotkey_listener(self) -> None:
        if self._hotkey_listener and self._hotkey_listener.is_alive(): self._hotkey_listener.stop()
    def _get_capture_filename(self, extension: str) -> str:
        capture_dir = self.config.get("capture_folder"); os.makedirs(capture_dir, exist_ok=True); now = datetime.datetime.now(); prefix = ""
        if self.config.get("use_capture_filename_prefix"): prefix = self.app.template_engine.render(config_override={"prompt_line_1": self.config.get("capture_filename_prefix"), "line_1_enabled": True, "line_2_enabled": False, "line_3_enabled": False})
        return os.path.join(capture_dir, f"{prefix}{now.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.{extension}")
    def _get_capture_bbox(self) -> Optional[Dict[str, int]]:
        if not _OPTIONAL_DEPENDENCIES['mss']: return None
        choice = self.config.get("capture_screen")
        if choice == self.app.lang.get("capture_all_screens"):
            with mss.mss() as sct: return sct.monitors[0]
        if match := re.search(r'Monitor (\d+)x(\d+) @ \((\-?\d+),(\-?\d+)\)', choice):
            try: w, h, x, y = map(int, match.groups()); return {'left': x, 'top': y, 'width': w, 'height': h}
            except (ValueError, IndexError): logging.error(f"Nie udało się sparsować geometrii monitora z: {choice}")
        logging.warning(f"Nie znaleziono dopasowania dla '{choice}', używanie monitora głównego jako domyślnego.")
        if _OPTIONAL_DEPENDENCIES['screeninfo']:
            try:
                for m in get_monitors():
                    if m.is_primary: return {'left': m.x, 'top': m.y, 'width': m.width, 'height': m.height}
            except Exception as e: logging.error(f"Błąd przy szukaniu monitora głównego: {e}")
        with mss.mss() as sct: return sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
    
    def _add_watermark(self, image: Image.Image, arranged_positions: Optional[List[Tuple[int, int]]] = None) -> Image.Image:
        base = image.convert("RGBA")
        style = self.config.get("watermark_style")
        opacity = int(2.55 * self.config.get("watermark_opacity"))

        if style == "qrcode":
            if not _OPTIONAL_DEPENDENCIES['qrcode']:
                logging.error("Styl 'Kod QR' wymaga biblioteki 'qrcode'.")
                return image.convert("RGB")
            
            qr_content = self.app.template_engine.render()
            
            size = self.config.get("watermark_qr_code_size")
            qr_img = qrcode.make(qr_content, error_correction=qrcode.constants.ERROR_CORRECT_L).convert('L')
            
            qr_rgba = Image.new('RGBA', qr_img.size)
            qr_rgba.putdata([(0,0,0,opacity) if p == 0 else (0,0,0,0) for p in qr_img.getdata()])
            
            padding = 10
            position = self.config.get("watermark_qr_position")
            pos_map = {
                "center": ((base.width - size) // 2, (base.height - size) // 2),
                "top-left": (padding, padding), "top-right": (base.width - size - padding, padding),
                "bottom-left": (padding, base.height - size - padding),
                "bottom-right": (base.width - size - padding, base.height - size - padding)
            }
            x, y = pos_map.get(position, pos_map["center"])
            
            resized_qr = qr_rgba.resize((size, size), Image.Resampling.NEAREST)
            base.paste(resized_qr, (x, y), resized_qr)
            return base.convert("RGB")

        watermark_text = self.app.template_engine.render() # Renderuj na nowo dla każdej klatki
        active_lines = [line for i, line in enumerate(watermark_text.split('\n')) if self.config.get(f"watermark_include_line{i+1}") and line.strip()]
        if not active_lines: return image.convert("RGB")

        txt_layer = Image.new('RGBA', base.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        full_text = "\n".join(active_lines)
        
        font_size, angle, spacing = 0, 0, 0
        if self.config.get("watermark_auto_scale"):
            diagonal = (image.width**2 + image.height**2)**0.5
            aspect_ratio = image.width / image.height if image.height > 0 else 1
            font_size = max(10, int(diagonal / 70))
            clamped_ratio = max(0.5, min(aspect_ratio, 2.5))
            angle = 65 - (((clamped_ratio - 0.5) / 2.0) * 40)
            spacing = max(50, int(diagonal / 5))
        else:
            font_size = max(12, int(image.height / 50))
            angle = self.config.get("watermark_angle")
            spacing = max(150, int(image.width / 5))

        use_shadow = self.config.get("watermark_use_shadow")
        shadow_offset = max(1, int(font_size / 20))
        
        try:
            hex_color = self.config.get("outline_color").lstrip('#')
            rgb_shadow = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            shadow_color = (*rgb_shadow, opacity)
        except:
            shadow_color = (0, 0, 0, opacity)
            
        main_color = (200, 200, 200, opacity)

        def get_font(size):
            try: return ImageFont.truetype("arial.ttf", size)
            except IOError: logging.warning("Nie znaleziono czcionki 'arial.ttf'. Używam domyślnej."); return ImageFont.load_default()

        def draw_text_with_shadow(pos: Tuple[int, int], text: str, font, align: str):
            if use_shadow:
                shadow_pos = (pos[0] + shadow_offset, pos[1] + shadow_offset)
                draw.text(shadow_pos, text, font=font, fill=shadow_color, align=align)
            draw.text(pos, text, font=font, fill=main_color, align=align)

        font = get_font(font_size)
        current_angle = 0 if style == "vertical" else angle

        if style == "arranged":
            positions = arranged_positions if arranged_positions is not None else self._generate_arranged_positions(base.width, base.height, font)
            for pos in positions:
                draw_text_with_shadow(pos, full_text, font, align="center")
        
        elif style == "single":
            if self.config.get("watermark_auto_scale"):
                bbox = draw.textbbox((0,0), max(active_lines, key=len), font=font)
                text_width = bbox[2] - bbox[0]
                if text_width > 0:
                    scale_factor = (image.width * 0.9) / text_width
                    if scale_factor < 1:
                        font = get_font(int(font_size * scale_factor))
            
            bbox = draw.textbbox((0,0), full_text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pos = ((base.width - w) / 2, (base.height - h) / 2)
            draw_text_with_shadow(pos, full_text, font, align="center")
        
        elif style == "vertical":
            count = self.config.get("watermark_arranged_count", 5)
            bbox = draw.textbbox((0,0), full_text, font=font)
            w_width, w_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            vertical_spacing = w_height * 0.5
            total_block_height = (count * w_height) + ((count - 1) * vertical_spacing)
            start_y = (image.height - total_block_height) / 2
            center_x = (image.width - w_width) / 2
            
            for i in range(count):
                current_y = start_y + i * (w_height + vertical_spacing)
                draw_text_with_shadow((center_x, current_y), full_text, font, align="center")

        else: # Tiled style
            for y in range(-spacing, base.height + spacing, spacing):
                for x in range(-spacing, base.width + spacing, spacing):
                    draw_text_with_shadow((x, y), full_text, font, align="center")
                    
        rotated = txt_layer.rotate(current_angle, expand=1, resample=Image.Resampling.BICUBIC)
        base.paste(rotated, (int((base.width - rotated.width) / 2), int((base.height - rotated.height) / 2)), rotated)
        return base.convert("RGB")

    def _submit_capture_task(self, task_func: Callable, *args) -> None:
        def task_wrapper():
            if not self._capture_lock.acquire(blocking=False): logging.warning("Przechwytywanie jest już w toku."); return
            should_hide = self.config.get("hide_widget_on_capture") and (not args or not args[0])
            try:
                if should_hide: self.app.master.after(0, self.app.master.withdraw); time.sleep(0.3)
                task_func(*args)
            finally:
                if should_hide: self.app.master.after(200, self.app.master.deiconify)
                self._capture_lock.release()
        self.app.executor.submit(task_wrapper)
    def capture_screenshot(self, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> None:
        self._submit_capture_task(self._screenshot_worker, region_bbox)
    
    def capture_video(self, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> None:
        if not all(_OPTIONAL_DEPENDENCIES[k] for k in ['cv2', 'numpy', 'mss']):
            messagebox.showerror("Brak bibliotek", "Nagrywanie wideo wymaga 'mss', 'opencv-python' i 'numpy'.")
            return
        self._submit_capture_task(self._video_worker, region_bbox)
    
    def capture_gif(self, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> None:
        if not _OPTIONAL_DEPENDENCIES['mss']:
            messagebox.showerror("Brak bibliotek", "Nagrywanie GIF wymaga 'mss'.")
            return
        self._submit_capture_task(self._gif_worker, region_bbox)
    
    def _screenshot_worker(self, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> None:
        try:
            file_path = self._get_capture_filename("png"); bbox_mss = {'left': region_bbox[0], 'top': region_bbox[1], 'width': region_bbox[2], 'height': region_bbox[3]} if region_bbox else self._get_capture_bbox()
            if not bbox_mss: return
            img = Image.frombytes("RGB", (sct_img := mss.mss().grab(bbox_mss)).size, sct_img.bgra, "raw", "BGRX") if _OPTIONAL_DEPENDENCIES['mss'] else ImageGrab.grab(bbox=(region_bbox[0], region_bbox[1], region_bbox[0] + region_bbox[2], region_bbox[1] + region_bbox[3]) if region_bbox else None)
            self._add_watermark(img).save(file_path, "PNG"); logging.info(f"Zapisano zrzut: {file_path}"); self.ui_manager.flash_widget("green")
        except Exception as e: logging.error(f"Błąd zrzutu ekranu: {e}"); self.ui_manager.flash_widget("red")

    def _video_worker(self, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> None:
        out = None
        try:
            file_path = self._get_capture_filename("mp4")
            bbox = {'left': region_bbox[0], 'top': region_bbox[1], 'width': region_bbox[2], 'height': region_bbox[3]} if region_bbox else self._get_capture_bbox()
            if not bbox: return

            positions = None
            if self.config.get("watermark_style") == "arranged":
                diagonal = (bbox['width']**2 + bbox['height']**2)**0.5
                font_size = max(10, int(diagonal / 70)) if self.config.get("watermark_auto_scale") else max(12, int(bbox['height'] / 50))
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()
                positions = self._generate_arranged_positions(bbox['width'], bbox['height'], font)

            FPS, FRAME_TIME = 20.0, 1.0 / 20.0
            out = cv2.VideoWriter(file_path, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (bbox['width'], bbox['height']))
            
            with mss.mss() as sct:
                end_time = time.time() + self.config.get("video_duration")
                while time.time() < end_time:
                    start_time = time.perf_counter()
                    img = Image.frombytes("RGB", (sct_img := sct.grab(bbox)).size, sct_img.bgra, "raw", "BGRX")
                    watermarked_frame = self._add_watermark(img, arranged_positions=positions)
                    out.write(cv2.cvtColor(np.array(watermarked_frame), cv2.COLOR_RGB2BGR))
                    if (sleep_time := FRAME_TIME - (time.perf_counter() - start_time)) > 0: time.sleep(sleep_time)
            logging.info(f"Zapisano wideo: {file_path}"); self.ui_manager.flash_widget("green")
        except Exception as e: logging.error(f"Błąd nagrywania wideo: {e}"); self.ui_manager.flash_widget("red")
        finally:
            if out is not None: out.release()

    def _gif_worker(self, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> None:
        try:
            file_path = self._get_capture_filename("gif")
            bbox = {'left': region_bbox[0], 'top': region_bbox[1], 'width': region_bbox[2], 'height': region_bbox[3]} if region_bbox else self._get_capture_bbox()
            frames = []
            if not bbox: return

            positions = None
            if self.config.get("watermark_style") == "arranged":
                diagonal = (bbox['width']**2 + bbox['height']**2)**0.5
                font_size = max(10, int(diagonal / 70)) if self.config.get("watermark_auto_scale") else max(12, int(bbox['height'] / 50))
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()
                positions = self._generate_arranged_positions(bbox['width'], bbox['height'], font)

            with mss.mss() as sct:
                end_time = time.time() + self.config.get("gif_duration")
                while time.time() < end_time:
                    img = Image.frombytes("RGB", (sct_img := sct.grab(bbox)).size, sct_img.bgra, "raw", "BGRX")
                    watermarked_frame = self._add_watermark(img, arranged_positions=positions)
                    frames.append(watermarked_frame.convert('P', palette=Image.Palette.ADAPTIVE))
                    time.sleep(0.1)
            if frames: frames[0].save(file_path, save_all=True, append_images=frames[1:], duration=100, loop=0); logging.info(f"Zapisano GIF: {file_path}"); self.ui_manager.flash_widget("green")
        except Exception as e: logging.error(f"Błąd nagrywania GIF: {e}"); self.ui_manager.flash_widget("red")

class SettingsWindow:
    """Zarządza oknem ustawień aplikacji."""
    def __init__(self, ui_manager: "UIManager"):
        self.ui, self.app, self.config, self.lang = ui_manager, ui_manager.app, ui_manager.app.config_manager, ui_manager.app.lang
        self.master = tk.Toplevel(self.app.master)
        self.vars: Dict[str, tk.Variable] = {}
        self.line_editors: List[ttk.Entry] = []
        self.node_widgets: List[ttk.Entry] = []
        self.last_focused_editor: Optional[ttk.Entry] = None
        self.celtic_image_tk: Optional[tk.PhotoImage] = None
        self.celtic_label: Optional[ttk.Label] = None
        self.qr_code_tk: Optional[tk.PhotoImage] = None
        self.qr_label: Optional[ttk.Label] = None
        self._qr_update_job: Optional[str] = None
        self._last_qr_content: str = ""

    def setup(self):
        self.master.title(self.lang.get("settings_title", version=APP_VERSION))
        self.master.transient(self.app.master)
        self.master.resizable(False, False)
        notebook = ttk.Notebook(self.master)
        notebook.pack(padx=10, pady=10, fill="both", expand=True)
        
        tabs = {"tab_template": self._create_tab_main, "tab_capture": self._create_tab_capture, "tab_data": self._create_tab_data, "tab_about": self._create_tab_about}
        for key, constructor in tabs.items():
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=self.lang.get(key))
            constructor(tab)

        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(pady=(0, 10), padx=10, fill="x", side="bottom")
        apply_status = ttk.Label(btn_frame, text="")
        apply_status.pack(side="left", padx=5)
        
        ttk.Button(btn_frame, text=self.lang.get("apply_button"), command=lambda: self.apply(apply_status)).pack(side="right", padx=5)
        ttk.Button(btn_frame, text=self.lang.get("close_button"), command=self._on_close).pack(side="right")
        
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)
        self.master.grab_set()

    def _on_close(self):
        if self._qr_update_job:
            self.master.after_cancel(self._qr_update_job)
            self._qr_update_job = None
        self.master.destroy()

    def _create_var(self, name: str, var_type: type = tk.StringVar) -> tk.Variable:
        self.vars[name] = var_type(value=self.config.get(name))
        return self.vars[name]
        
    def _create_tab_main(self, parent: ttk.Frame):
        lf_template = ttk.LabelFrame(parent, text=self.lang.get("template_creator_title"))
        lf_template.pack(fill='x', padx=5, pady=5)
        menu_frame = ttk.Frame(lf_template)
        menu_frame.pack(fill='x', padx=5, pady=5)
        self._create_template_menus(menu_frame)
        for i in range(1, 4): self._create_line_editor(lf_template, i)
        
        lf_appearance = ttk.LabelFrame(parent, text=self.lang.get("appearance_title"))
        lf_appearance.pack(fill='x', padx=5, pady=5)
        self._create_font_section(lf_appearance)
        self._create_color_section(lf_appearance)
        
        options_frame = ttk.Frame(lf_appearance)
        options_frame.pack(fill='x', padx=5, pady=(10, 5))
        glyph_frame = ttk.Frame(options_frame)
        glyph_frame.pack(fill='x')
        ttk.Checkbutton(glyph_frame, text=self.lang.get("gen_glyph_chk"), variable=self._create_var("generate_glyphs", tk.BooleanVar)).pack(side='left', anchor='w')
        ttk.Entry(glyph_frame, textvariable=self._create_var("glyph_seed")).pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(glyph_frame, text=self.lang.get("insert_glyph_btn"), command=lambda: self._insert_code('%glyph%')).pack(side='left')
        
        misc_options_frame = ttk.Frame(options_frame)
        misc_options_frame.pack(fill='x', pady=(5,0))
        ttk.Checkbutton(misc_options_frame, text=self.lang.get("full_hash_chk"), variable=self._create_var("display_full_hash", tk.BooleanVar)).pack(side='left')
        ttk.Checkbutton(misc_options_frame, text=self.lang.get("lock_position_chk"), variable=self._create_var("lock_position", tk.BooleanVar)).pack(side='left', padx=10)
        ttk.Checkbutton(misc_options_frame, text=self.lang.get("always_on_top_chk"), variable=self._create_var("always_on_top", tk.BooleanVar)).pack(side='left')
        
        lf_glyph_info = ttk.LabelFrame(parent, text=self.lang.get("about_glyph_title"))
        lf_glyph_info.pack(fill='x', padx=5, pady=5)
        ttk.Label(lf_glyph_info, text=self.lang.get("about_glyph_desc"), wraplength=450, justify='left').pack(padx=5, pady=5)
        
        self.master.after(100, lambda: self.line_editors[0].focus_set() if self.line_editors else None)

    def _create_template_menus(self, parent: ttk.Frame):
        SAMPLES = [("Data i czas (krótki)", "d MMM yyyy HH:mm"), ("Data (długi)", "dddd, d MMMM yyyy"), ("Data i czas (pełny)", "yyyy-MM-dd HH:mm:ss")]
        DATE_CODES = [("Dzień (1)", 'd'), ("Dzień (01)", 'dd'), ("Nazwa dnia (Pon)", 'ddd'), ("Nazwa dnia (Poniedziałek)", 'dddd'), ("-", "-"), ("Miesiąc (7)", 'M'), ("Miesiąc (07)", 'MM'), ("Nazwa miesiąca (Lip)", 'MMM'), ("Nazwa miesiąca (Lipiec)", 'MMMM'), ("-", "-"), ("Rok (25)", 'yy'), ("Rok (2025)", 'yyyy')]
        TIME_CODES = [("Godzina (1-12)", 'h'), ("(01-12)", 'hh'), ("(0-23)", 'H'), ("(00-23)", 'HH'), ("-", "-"), ("Minuta (5)", 'm'), ("(05)", 'mm'), ("-", "-"), ("Sekunda (8)", 's'), ("(08)", 'ss'), ("-", "-"), ("Dzies. sek. (1)", 'S'), ("Set. sek. (12)", 'SS'), ("Tys. sek. (123)", 'SSS'), ("-", "-"), ("AM/PM", 'tt'), ("A/P", 't')]
        SEPARATOR_CODES = [("Spacja", ' '), ("Tekst dosłowny", "''"), ("Dwukropek", ':'), ("Przecinek", ','), ("Kropka", '.'), ("Myśnik", '-'), ("Ukośnik", '/'), ("Pion. kreska", ' | ')]
        SPECIAL_CODES = [("Glif", "%glyph%"), ("Swatch Time", '@'), ("Wysokość bloku", '%blockheight%'), ("Hash bloku", '%hash%')]

        def create_menubutton(text_key, items, is_sample=False):
            mb = ttk.Menubutton(parent, text=self.lang.get(text_key))
            menu = tk.Menu(mb, tearoff=0)
            for label, code in items:
                if label == "-": menu.add_separator()
                else:
                    cmd = (lambda c=code: self._set_sample(c)) if is_sample else (lambda c=code: self._insert_code(c))
                    menu.add_command(label=f"{label} ({code})" if code != "''" else label, command=cmd)
            mb.config(menu=menu)
            mb.pack(side='left')

        create_menubutton("samples_btn", SAMPLES, True)
        create_menubutton("date_btn", DATE_CODES)
        create_menubutton("time_btn", TIME_CODES)
        create_menubutton("separator_btn", SEPARATOR_CODES)
        create_menubutton("special_btn", SPECIAL_CODES)
        ttk.Button(parent, text=self.lang.get("reset_btn"), command=self._reset_templates).pack(side='left', padx=(5,0))

    def _on_editor_focus(self, event: tk.Event): self.last_focused_editor = event.widget
    def _insert_code(self, code: str):
        if target := self.last_focused_editor: target.insert(tk.INSERT, "''" if code == "''" else code); target.icursor(target.index(tk.INSERT) - 1) if code == "''" else None; target.focus_set()
    def _set_sample(self, s: str): self.vars["prompt_line_1"].set(s); self.vars["prompt_line_2"].set(""); self.vars["prompt_line_3"].set("")
    def _reset_templates(self): d = self.config.get_default_config(); self.vars["prompt_line_1"].set(d["prompt_line_1"]); self.vars["prompt_line_2"].set(d["prompt_line_2"]); self.vars["prompt_line_3"].set(d["prompt_line_3"])
    def _create_line_editor(self, p, i): f = ttk.Frame(p); f.pack(fill='x', padx=5, pady=2); ttk.Checkbutton(f, variable=self._create_var(f"line_{i}_enabled", tk.BooleanVar)).pack(side='left'); e = ttk.Entry(f, textvariable=self._create_var(f"prompt_line_{i}")); e.pack(side='left', fill='x', expand=True, padx=5); e.bind("<FocusIn>", self._on_editor_focus); self.line_editors.append(e); ttk.Combobox(f, textvariable=self._create_var(f"line_{i}_align"), values=["left", "center", "right"], state="readonly", width=8).pack(side='left')
    def _create_font_section(self, p): f = ttk.Frame(p); f.pack(fill='x', padx=5, pady=5); ttk.Label(f, text=self.lang.get("font_label")).pack(side='left'); ttk.Combobox(f, textvariable=self._create_var("font_family"), values=sorted(tkfont.families()), state='readonly').pack(side='left', expand=True, fill='x', padx=5); ttk.Label(f, text=self.lang.get("size_label")).pack(side='left'); ttk.Combobox(f, textvariable=self._create_var("base_font_size", tk.IntVar), values=[8,10,12,14,15,16,18,24,32,36,48], width=5).pack(side='left'); f_s = ttk.Frame(p); f_s.pack(fill='x', padx=5); ttk.Checkbutton(f_s, text=self.lang.get("bold_chk"), variable=self._create_var("font_weight", tk.StringVar), onvalue='bold', offvalue='normal').pack(side='left'); ttk.Checkbutton(f_s, text=self.lang.get("italic_chk"), variable=self._create_var("font_slant", tk.StringVar), onvalue='italic', offvalue='roman').pack(side='left', padx=10)
    def _create_color_section(self, p): f = ttk.Frame(p); f.pack(fill='x', padx=5, pady=5); self._create_color_picker(f, "color_text_btn", 'text_color'); self._create_color_picker(f, "color_shadow_btn", 'outline_color'); f_o = ttk.Frame(p); f_o.pack(fill='x', padx=5, pady=(5,0)); ttk.Checkbutton(f_o, text=self.lang.get("use_shadow_chk"), variable=self._create_var("use_outline", tk.BooleanVar)).pack(side='left', padx=(0,10)); ttk.Label(f_o, text=self.lang.get("thickness_label")).pack(side='left'); ttk.Spinbox(f_o, from_=0, to=10, width=5, textvariable=self._create_var("outline_thickness", tk.IntVar)).pack(side='left', padx=(0,10)); s_map, d_map = {self.lang.get("style_outline"): "outline", self.lang.get("style_3d"): "3d_offset"}, {self.lang.get("dir_dr"): "down-right", self.lang.get("dir_dl"): "down-left", self.lang.get("dir_ur"): "up-right", self.lang.get("dir_ul"): "up-left"}; ttk.Label(f_o, text=self.lang.get("style_label")).pack(side='left'); s_var = tk.StringVar(value=next((n for n,v in s_map.items() if v == self.config.get("shadow_style")), list(s_map.keys())[0])); s_combo = ttk.Combobox(f_o, textvariable=s_var, values=list(s_map.keys()), state="readonly", width=10); s_combo.pack(side='left', padx=(0,10)); self.vars["shadow_style_display"] = s_var; dir_lbl, d_var = ttk.Label(f_o, text=self.lang.get("direction_label")), tk.StringVar(value=next((n for n,v in d_map.items() if v == self.config.get("shadow_direction")), list(d_map.keys())[0])); dir_combo = ttk.Combobox(f_o, textvariable=d_var, values=list(d_map.keys()), state="readonly", width=12); self.vars["shadow_direction_display"] = d_var; toggle = lambda e=None: [dir_lbl.pack(side='left'), dir_combo.pack(side='left')] if s_var.get() == self.lang.get("style_3d") else [dir_lbl.pack_forget(), dir_combo.pack_forget()]; s_combo.bind("<<ComboboxSelected>>", toggle); toggle()
    def _create_color_picker(self, p, lbl, k): var = self._create_var(k); f = ttk.Frame(p); f.pack(side='left', padx=5); swatch = tk.Label(f, text="  ", bg=var.get(), relief="sunken"); (lambda: ttk.Button(f, text=self.lang.get(lbl), command=lambda: (c := colorchooser.askcolor(parent=self.master, initialcolor=var.get())[1]) and (var.set(c), swatch.config(bg=c))).pack(side='left'))(); swatch.pack(side='left', padx=5)
    
    def _create_prefix_template_creator(self, parent: ttk.Frame, target_entry: ttk.Entry, target_var: tk.StringVar):
        SAMPLES = [("Blok i Data", "capture_%blockheight%_yyyy-MM-dd"), ("Data i Czas", "yyyyMMdd_HHmmss_")]; DATE_CODES = [("Rok (2025)", 'yyyy'), ("Miesiąc (07)", 'MM'), ("Dzień (01)", 'dd')]; TIME_CODES = [("Godzina (00-23)", 'HH'), ("Minuta (05)", 'mm'), ("Sekunda (08)", 'ss')]; SEPARATOR_CODES = [("Znak _", '_'), ("Myślnik", '-'), ("Kropka", '.')]; SPECIAL_CODES = [("Glif", "%glyph%"), ("Wysokość bloku", '%blockheight%'), ("Hash bloku", '%hash%')]
        def _insert_code(code: str): target_entry.insert(tk.INSERT, code); target_entry.focus_set()
        def _set_sample(sample: str): target_var.set(sample); target_entry.focus_set()
        def _reset(): target_var.set(self.app.config_manager.get_default_config()["capture_filename_prefix"])
        def create_menubutton(text_key, items, is_sample=False):
            mb = ttk.Menubutton(parent, text=self.lang.get(text_key)); menu = tk.Menu(mb, tearoff=0)
            for label, code in items:
                if label == "-": menu.add_separator()
                else:
                    cmd = (lambda s=code: _set_sample(s)) if is_sample else (lambda c=code: _insert_code(c))
                    menu.add_command(label=f"{label} ({code})", command=cmd)
            mb.config(menu=menu); mb.pack(side='left')
        create_menubutton("samples_btn", SAMPLES, is_sample=True); create_menubutton("date_btn", DATE_CODES); create_menubutton("time_btn", TIME_CODES); create_menubutton("separator_btn", SEPARATOR_CODES); create_menubutton("special_btn", SPECIAL_CODES); ttk.Button(parent, text=self.lang.get("reset_btn"), command=_reset).pack(side='left', padx=(5,0))

    def _toggle_watermark_angle_control(self, var, scale_widget, label_widget):
        state = 'disabled' if var.get() else 'normal'
        scale_widget.config(state=state)
        label_widget.config(state=state)

    def _create_tab_capture(self, p):
        lf_h = ttk.LabelFrame(p, text=self.lang.get("hotkeys_title")); lf_h.pack(fill="x", padx=5, pady=5, ipady=5); ttk.Label(lf_h, text=self.lang.get("hotkeys_desc"), justify="left").pack(anchor="w", padx=5, pady=5); lf_o = ttk.LabelFrame(p, text=self.lang.get("capture_options_title")); lf_o.pack(fill="x", padx=5, pady=5, ipady=5); m_f = ttk.Frame(lf_o); m_f.pack(fill='x', padx=5, pady=5); ttk.Label(m_f, text=self.lang.get("capture_monitor_label")).pack(side='left', padx=(0,5)); m_opts = [self.lang.get("capture_all_screens")]; [m_opts.append(f"Monitor {m.width}x{m.height} @ ({m.x},{m.y}){self.lang.get('primary_monitor_tag') if m.is_primary else ''}") for m in sorted(get_monitors(), key=lambda m: m.x)] if _OPTIONAL_DEPENDENCIES['screeninfo'] else None; var = self._create_var("capture_screen"); var.set(var.get() if var.get() in m_opts else m_opts[0]); ttk.Combobox(m_f, textvariable=var, values=m_opts, state="readonly").pack(fill='x'); ttk.Checkbutton(lf_o, text=self.lang.get("hide_widget_chk"), variable=self._create_var("hide_widget_on_capture", tk.BooleanVar)).pack(anchor='w', padx=5); lf_r = ttk.LabelFrame(p, text=self.lang.get("recording_options_title")); lf_r.pack(fill="x", padx=5, pady=5); rec_f = ttk.Frame(lf_r); rec_f.pack(fill='x', padx=5, pady=5); r_state = "normal" if all(_OPTIONAL_DEPENDENCIES[k] for k in ['cv2', 'numpy', 'mss']) else "disabled"; ttk.Label(rec_f, text=self.lang.get("video_duration_label")).pack(side='left'); ttk.Spinbox(rec_f, from_=1, to=300, width=5, textvariable=self._create_var("video_duration", tk.IntVar), state=r_state).pack(side='left', padx=(5, 15)); ttk.Label(rec_f, text=self.lang.get("gif_duration_label")).pack(side='left'); ttk.Spinbox(rec_f, from_=1, to=60, width=5, textvariable=self._create_var("gif_duration", tk.IntVar), state=r_state).pack(side='left', padx=5); lf_path = ttk.LabelFrame(p, text=self.lang.get("path_title")); lf_path.pack(fill="x", padx=5, pady=5); path_f = ttk.Frame(lf_path); path_f.pack(fill='x', padx=5, pady=5); p_var = self._create_var("capture_folder"); ttk.Entry(path_f, textvariable=p_var, state="readonly").pack(side="left", fill="x", expand=True); ttk.Button(path_f, text=self.lang.get("change_btn"), command=lambda v=p_var: v.set(filedialog.askdirectory(initialdir=v.get()) or v.get())).pack(side="left"); pfx_f = ttk.Frame(lf_path); pfx_f.pack(fill='x', padx=5, pady=(0, 5)); ttk.Checkbutton(pfx_f, text=self.lang.get("prefix_chk"), variable=self._create_var("use_capture_filename_prefix", tk.BooleanVar)).pack(side='left'); pfx_var, pfx_entry = self._create_var("capture_filename_prefix"), ttk.Entry(pfx_f, textvariable=self._create_var("capture_filename_prefix")); pfx_entry.pack(side='left', fill='x', expand=True); lf_pfx_c = ttk.LabelFrame(lf_path, text=self.lang.get("prefix_template_creator_title")); lf_pfx_c.pack(fill='x', padx=5, pady=(5,0)); c_menu_f = ttk.Frame(lf_pfx_c); c_menu_f.pack(fill='x', padx=5, pady=5); self._create_prefix_template_creator(c_menu_f, pfx_entry, pfx_var); 
        
        lf_w = ttk.LabelFrame(p, text=self.lang.get("watermark_title")); lf_w.pack(fill="x", padx=5, pady=5)
        
        style_map = {self.lang.get("watermark_style_tiled"): "tiled", self.lang.get("watermark_style_arranged"): "arranged", self.lang.get("watermark_style_single"): "single", self.lang.get("watermark_style_vertical"): "vertical"}
        if _OPTIONAL_DEPENDENCIES['qrcode']: style_map[self.lang.get("watermark_style_qrcode")] = "qrcode"
        style_f = ttk.Frame(lf_w); style_f.pack(fill='x', padx=5, pady=5)
        ttk.Label(style_f, text=self.lang.get("watermark_style_label")).pack(side='left')
        style_var = tk.StringVar(value=next((n for n, v in style_map.items() if v == self.config.get("watermark_style")), list(style_map.keys())[0]))
        style_combo = ttk.Combobox(style_f, textvariable=style_var, values=list(style_map.keys()), state="readonly", width=20); style_combo.pack(side='left')
        self.vars["watermark_style_display"] = style_var

        text_options_frame = ttk.Frame(lf_w)
        qr_options_frame = ttk.Frame(lf_w)
        
        chk_f = ttk.Frame(text_options_frame); chk_f.pack(fill='x', padx=5, pady=2); [ttk.Checkbutton(chk_f, text=self.lang.get(f"line_{i}_chk"), variable=self._create_var(f"watermark_include_line{i}", tk.BooleanVar)).pack(side='left', padx=2) for i in range(1, 4)];
        shadow_f = ttk.Frame(text_options_frame); shadow_f.pack(fill='x', padx=5, pady=2); ttk.Checkbutton(shadow_f, text=self.lang.get("watermark_use_shadow_chk"), variable=self._create_var("watermark_use_shadow", tk.BooleanVar)).pack(side='left');
        count_f = ttk.Frame(style_f)
        count_lbl = ttk.Label(count_f, text=self.lang.get("watermark_count_label"));
        count_combo = ttk.Combobox(count_f, textvariable=self._create_var("watermark_arranged_count", tk.IntVar), values=[1,3,5,7], state="readonly", width=5)
        auto_scale_f = ttk.Frame(text_options_frame); auto_scale_f.pack(fill='x', padx=5, pady=2)
        auto_scale_var = self._create_var("watermark_auto_scale", tk.BooleanVar)
        _, opacity_lbl = self._create_slider(text_options_frame, "opacity_label", "watermark_opacity", 0, 100)
        angle_scale, angle_lbl = self._create_slider(text_options_frame, "angle_label", "watermark_angle", 0, 90)
        ttk.Checkbutton(auto_scale_f, text=self.lang.get("watermark_auto_scale_chk"), variable=auto_scale_var, command=lambda: self._toggle_watermark_angle_control(auto_scale_var, angle_scale, angle_lbl)).pack(side='left')
        self._toggle_watermark_angle_control(auto_scale_var, angle_scale, angle_lbl)

        pos_map = {"center": self.lang.get("pos_center"), "top-left": self.lang.get("pos_tl"), "top-right": self.lang.get("pos_tr"), "bottom-left": self.lang.get("pos_bl"), "bottom-right": self.lang.get("pos_br")}
        qr_pos_f = ttk.Frame(qr_options_frame); qr_pos_f.pack(fill='x', padx=5, pady=2)
        ttk.Label(qr_pos_f, text=self.lang.get("watermark_qr_position_label"), width=15).pack(side='left')
        qr_pos_var = tk.StringVar(value=pos_map.get(self.config.get("watermark_qr_position"), pos_map["center"]))
        self.vars["watermark_qr_position_display"] = qr_pos_var
        ttk.Combobox(qr_pos_f, textvariable=qr_pos_var, values=list(pos_map.values()), state="readonly").pack(fill='x', expand=True)

        self._create_slider(qr_options_frame, "watermark_qr_size_label", "watermark_qr_code_size", 50, 250)
        self._create_slider(qr_options_frame, "opacity_label", "watermark_opacity", 0, 100)
        
        def _toggle_style_controls(e=None):
            is_qr = style_var.get() == self.lang.get("watermark_style_qrcode")
            is_countable = style_var.get() in [self.lang.get("watermark_style_arranged"), self.lang.get("watermark_style_vertical")]

            if is_qr: text_options_frame.pack_forget(); qr_options_frame.pack(fill='x')
            else: qr_options_frame.pack_forget(); text_options_frame.pack(fill='x')
            
            if is_countable: count_f.pack(side='left', padx=(10,5)); count_lbl.pack(side='left'); count_combo.pack(side='left')
            else: count_f.pack_forget()
        
        style_combo.bind("<<ComboboxSelected>>", _toggle_style_controls)
        _toggle_style_controls()

    def _create_slider(self, p, lbl_key, var_name, from_, to, command=None) -> Tuple[ttk.Scale, ttk.Label]:
        f = ttk.Frame(p); f.pack(fill='x', padx=5, pady=2); var = self._create_var(var_name, tk.IntVar); 
        
        def on_slide(v):
            lbl.config(text=f"{self.lang.get(lbl_key)} {round(float(v))}")
            if command: command(v)

        lbl = ttk.Label(f, text=f"{self.lang.get(lbl_key)} {var.get()}", width=15); lbl.pack(side='left'); 
        scale = ttk.Scale(f, from_=from_, to=to, orient='horizontal', variable=var, command=on_slide); 
        scale.pack(fill='x', expand=True); scale.set(var.get())
        return scale, lbl
    def _create_tab_data(self, p):
        lf_n = ttk.LabelFrame(p, text=self.lang.get("node_title"))
        lf_n.pack(fill="x", padx=5, pady=5)
        ttk.Checkbutton(lf_n, text=self.lang.get("use_node_chk"), variable=self._create_var("use_custom_node", tk.BooleanVar), command=self._toggle_node_fields).pack(anchor='w', padx=5)
        grid = ttk.Frame(lf_n)
        grid.pack(fill='x', padx=5, pady=5)
        grid.columnconfigure(1, weight=1)
        
        fields = {"rpc_url_label": "custom_node_url", "user_label": "custom_node_user", "pass_label": "custom_node_pass"}
        for i, (lbl_k, k) in enumerate(fields.items()):
            ttk.Label(grid, text=self.lang.get(lbl_k)).grid(row=i, column=0, sticky='w')
            e = ttk.Entry(grid, textvariable=self._create_var(k), show=("*" if "pass" in lbl_k else ""))
            e.grid(row=i, column=1, sticky='ew')
            self.node_widgets.append(e)
            
        self._toggle_node_fields()
        lf_p = ttk.LabelFrame(p, text=self.lang.get("pyblock_title"))
        lf_p.pack(fill="x", padx=5, pady=5)
        ttk.Label(lf_p, text=self.lang.get("pyblock_cmd_label")).pack(anchor='w', padx=5)
        ttk.Entry(lf_p, textvariable=self._create_var("pyblock_command")).pack(fill='x', padx=5, pady=5)
    
    def _redraw_about_images(self, size_val=None):
        size = int(float(size_val)) if size_val else self.vars["about_qr_code_size"].get()
        self._load_and_display_celtic_image(size)
        self._last_qr_content = ""
        if self.vars["about_show_qr_code"].get():
            self._update_qr_code()

    def _load_and_display_celtic_image(self, size: int) -> None:
        IMAGE_FILENAME = "celtic_knot.png" 
        if not self.celtic_label: return
        if not os.path.exists(IMAGE_FILENAME):
            logging.warning(f"Brak pliku graficznego: {IMAGE_FILENAME}.")
            return
        try:
            pil_image = Image.open(IMAGE_FILENAME)
            pil_image = pil_image.resize((size, size), Image.Resampling.LANCZOS)
            self.celtic_image_tk = ImageTk.PhotoImage(pil_image)
            self.celtic_label.config(image=self.celtic_image_tk)
        except Exception as e:
            logging.error(f"Błąd ładowania lub konwersji obrazu: {e}")

    def _update_qr_code(self):
        if not self.master.winfo_exists() or not _OPTIONAL_DEPENDENCIES.get('qrcode'):
            if self._qr_update_job: self.master.after_cancel(self._qr_update_job)
            return

        qr_content = self.app.template_engine.render()

        if qr_content != self._last_qr_content:
            self._last_qr_content = qr_content
            try:
                size = self.vars["about_qr_code_size"].get()
                qr_img = qrcode.make(qr_content, error_correction=qrcode.constants.ERROR_CORRECT_L)
                qr_img = qr_img.resize((size, size), Image.Resampling.NEAREST)
                self.qr_code_tk = ImageTk.PhotoImage(qr_img)
                if self.qr_label:
                    self.qr_label.config(image=self.qr_code_tk)
            except Exception as e:
                logging.error(f"Nie udało się wygenerować kodu QR: {e}")
        
        self._qr_update_job = self.master.after(1000, self._update_qr_code)

    def _toggle_qr_visibility(self):
        if self.vars["about_show_qr_code"].get():
            self.qr_label.grid()
            if not self._qr_update_job: 
                self._update_qr_code()
        else:
            self.qr_label.grid_remove()
            if self._qr_update_job:
                self.master.after_cancel(self._qr_update_job)
                self._qr_update_job = None
    
    def _create_tab_about(self, p):
        m_f = ttk.Frame(p); m_f.pack(fill="both", expand=True, padx=5, pady=5); lf_i = ttk.LabelFrame(m_f, text=self.lang.get("about_info_title")); lf_i.pack(fill="x", pady=(0, 5)); ttk.Label(lf_i, text="TimeChain Watermark Widget", font=("Segoe UI", 16, "bold")).pack(pady=(5, 0)); ttk.Label(lf_i, text=f"Wersja: {APP_VERSION} \"{APP_CODENAME}\"").pack(); ttk.Label(lf_i, text=self.lang.get("about_author"), font=("Segoe UI", 9, "italic")).pack(pady=5); lang_f = ttk.Frame(lf_i); lang_f.pack(pady=5); ttk.Label(lang_f, text=self.lang.get("general_lang_label")).pack(side='left'); lang_var = tk.StringVar(value=self.lang.get_lang_name_from_code(self.config.get("language"))); self.vars["language_display"] = lang_var; lang_combo = ttk.Combobox(lang_f, textvariable=lang_var, values=list(self.lang.get_lang_map().keys()), state="readonly"); lang_combo.pack(side='left'); lang_combo.bind("<<ComboboxSelected>>", self._on_language_change); lf_d = ttk.LabelFrame(m_f, text=self.lang.get("about_instruction_title")); lf_d.pack(fill="x", pady=(0, 5)); ttk.Label(lf_d, text=self.lang.get("about_instruction_desc"), wraplength=450, justify='left').pack(pady=5, padx=10); 
        
        lf_deps = ttk.LabelFrame(m_f, text=self.lang.get("about_deps_title"))
        lf_deps.pack(fill="x", pady=5)
        
        deps_container = ttk.Frame(lf_deps)
        deps_container.pack(pady=10, fill="x", padx=10)
        deps_container.columnconfigure(0, weight=1); deps_container.columnconfigure(1, weight=1); deps_container.columnconfigure(2, weight=1)

        self.celtic_label = ttk.Label(deps_container)
        self.celtic_label.grid(row=0, column=0, sticky='w')

        deps_grid = ttk.Frame(deps_container) 
        deps_grid.grid(row=0, column=1, sticky='')
        
        for i, (dep, found) in enumerate(_OPTIONAL_DEPENDENCIES.items()):
            ttk.Label(deps_grid, text=f"{dep}:").grid(row=i, column=0, sticky="e")
            ttk.Label(deps_grid, text=self.lang.get("dep_found") if found else self.lang.get("dep_missing"), foreground="green" if found else "red").grid(row=i, column=1, sticky="w", padx=5)

        if _OPTIONAL_DEPENDENCIES['qrcode']:
            self.qr_label = ttk.Label(deps_container)
            self.qr_label.grid(row=0, column=2, sticky='e')
            
            qr_options_lf = ttk.LabelFrame(m_f, text=self.lang.get("about_qr_options_title"))
            qr_options_lf.pack(fill='x', pady=5, padx=5)
            
            show_qr_var = self._create_var("about_show_qr_code", tk.BooleanVar)
            ttk.Checkbutton(qr_options_lf, text=self.lang.get("about_show_qr_chk"), variable=show_qr_var, command=self._toggle_qr_visibility).pack(anchor='w', padx=5)
            
            self._create_slider(qr_options_lf, "about_qr_size_label", "about_qr_code_size", 50, 150, command=self._redraw_about_images)
            
            self._toggle_qr_visibility()
            self._redraw_about_images()

    def _on_language_change(self, e=None):
        if (n_code := self.lang.get_lang_map().get(self.vars["language_display"].get(), "en")) != self.config.get("language"):
            self.config.set("language", n_code); self.config.save(); self.app.lang.set_language(n_code); self._on_close()
            self.ui.show_settings()
            
    def _toggle_node_fields(self): state = 'normal' if self.vars.get("use_custom_node", tk.BooleanVar(value=False)).get() else 'disabled'; [w.config(state=state) for w in self.node_widgets]
    
    def apply(self, status_lbl):
        pos_map_rev = {v: k for k, v in {
            "center": self.lang.get("pos_center"), "top-left": self.lang.get("pos_tl"), 
            "top-right": self.lang.get("pos_tr"), "bottom-left": self.lang.get("pos_bl"), 
            "bottom-right": self.lang.get("pos_br")
        }.items()}
        
        if "watermark_qr_position_display" in self.vars:
             self.config.set("watermark_qr_position", pos_map_rev.get(self.vars["watermark_qr_position_display"].get()))

        s_map = {self.lang.get("style_outline"): "outline", self.lang.get("style_3d"): "3d_offset"}
        d_map = {self.lang.get("dir_dr"): "down-right", self.lang.get("dir_dl"): "down-left", self.lang.get("dir_ur"): "up-right", self.lang.get("dir_ul"): "up-left"}
        w_map = {
            self.lang.get("watermark_style_tiled"): "tiled", 
            self.lang.get("watermark_style_arranged"): "arranged", 
            self.lang.get("watermark_style_single"): "single", 
            self.lang.get("watermark_style_vertical"): "vertical"
        }
        if _OPTIONAL_DEPENDENCIES['qrcode']: 
            w_map[self.lang.get("watermark_style_qrcode")] = "qrcode"
        
        self.config.set("shadow_style", s_map.get(self.vars.get("shadow_style_display").get()))
        self.config.set("shadow_direction", d_map.get(self.vars.get("shadow_direction_display").get()))
        self.config.set("watermark_style", w_map.get(self.vars.get("watermark_style_display").get()))
        
        for k, v in self.vars.items():
            if k not in ["shadow_style_display", "shadow_direction_display", "language_display", "watermark_style_display", "watermark_qr_position_display"]:
                self.config.set(k, v.get())
        
        self.config.save()
        self.app.master.attributes('-topmost', self.config.get('always_on_top'))
        self.app.request_ui_update()
        status_lbl.config(text=self.lang.get("apply_success"), foreground="green")
        self.master.after(3000, lambda: status_lbl.config(text=""))
    
    def is_alive(self) -> bool: return self.master.winfo_exists()
    def focus(self) -> None: self.master.lift(); self.master.focus_force()

class UIManager:
    """Zarządza wszystkimi oknami i elementami interfejsu użytkownika."""
    def __init__(self, app: "TimechainApp"):
        self.app = app; self.widget_window = WidgetWindow(self); self.settings_window: Optional[SettingsWindow] = None
    def setup_ui(self) -> None: self.widget_window.setup()
    def update_widget(self, text: str, is_inverted: bool, config_override: Optional[Dict] = None) -> None: self.widget_window.update_display(text, is_inverted, config_override)
    def flash_widget(self, color: str = "green", duration_ms: int = 200) -> None: self.widget_window.flash(color, duration_ms)
    def get_widget_geometry(self) -> Tuple[int, int, int, int]: return self.widget_window.get_geometry()
    def show_settings(self) -> None:
        if self.settings_window and self.settings_window.is_alive(): self.settings_window.focus(); return
        self.settings_window = SettingsWindow(self); self.settings_window.setup()
    def launch_pyblock(self) -> None:
        if not (command := self.app.config_manager.get("pyblock_command")): messagebox.showwarning("Brak Komendy", "Nie skonfigurowano komendy do uruchomienia PyBlock. Sprawdź ustawienia."); self.show_settings(); return
        PyBlockLauncher.launch(command)

class TimechainApp:
    """Główna klasa aplikacji, która łączy wszystkie komponenty."""
    def __init__(self, master: tk.Tk):
        self.master = master; set_dpi_awareness_windows(); self.config_manager = ConfigManager(); self.lang = LanguageManager(self, self.config_manager.get("language")); self.data_manager = DataManager(self); self.template_engine = TemplateEngine(self); self.ui_manager = UIManager(self); self.capture_manager = CaptureManager(self); self.color_analyzer = ColorAnalyzer(self)
        self._cancel_update = threading.Event(); self.executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="Worker"); self._ui_update_needed = threading.Event()
    def run(self) -> None:
        self.master.attributes('-topmost', self.config_manager.get('always_on_top', True)); self.ui_manager.setup_ui(); self.master.deiconify(); self.capture_manager.start_hotkey_listener(); self.color_analyzer.start(); self.master.protocol("WM_DELETE_WINDOW", self.close_app); self._data_fetch_loop(); self._update_loop()
    def request_ui_update(self) -> None:
        if self.master.winfo_exists() and not self._ui_update_needed.is_set(): self._ui_update_needed.set(); self.master.after_idle(self._refresh_display_if_needed)
    def _refresh_display_if_needed(self) -> None:
        if self._ui_update_needed.is_set(): self._refresh_display(); self._ui_update_needed.clear()
    def _refresh_display(self, config_override: Optional[Dict[str, Any]] = None) -> None:
        if self._cancel_update.is_set(): return
        self.ui_manager.update_widget(self.template_engine.render(config_override), self.color_analyzer.should_invert.is_set(), config_override)
    
    def _update_loop(self) -> None:
        if self._cancel_update.is_set():
            return
        self.request_ui_update()
        self.master.after(100, self._update_loop)

    def _data_fetch_loop(self) -> None:
        def fetch_and_wait():
            while not self._cancel_update.is_set():
                self.data_manager.fetch_all_data()
                self._cancel_update.wait(self.config_manager.get("data_fetch_interval_s"))
        threading.Thread(target=fetch_and_wait, name="DataFetchThread", daemon=True).start()
    def close_app(self) -> None:
        if not self._cancel_update.is_set():
            self._cancel_update.set(); self.capture_manager.stop_hotkey_listener(); self.color_analyzer.stop()
            if self.master.winfo_exists(): self.config_manager.set("last_position", self.master.geometry())
            self.config_manager.save(); self.executor.shutdown(wait=False, cancel_futures=True); self.master.destroy(); logging.info("Aplikacja zamknięta.")

if __name__ == "__main__":
    root = tk.Tk(); root.withdraw(); app = None
    try: app = TimechainApp(root); app.run(); root.mainloop()
    except (KeyboardInterrupt, SystemExit): logging.info("Aplikacja przerwana przez użytkownika.")
    except Exception as e:
        logging.critical(f"Wystąpił nieoczekiwany błąd krytyczny: {e}", exc_info=True)
        try:
            if tk._default_root and tk._default_root.winfo_exists(): messagebox.showerror("Błąd Krytyczny", f"Wystąpił błąd:\n\n{e}")
        except Exception: pass
    finally:
        if app and not app._cancel_update.is_set(): app.close_app()
        sys.exit(0)