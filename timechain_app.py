# -*- coding: utf-8 -*-
# TimeChainAppv21.3.1 "Veritas Bridge + OTS + PSBT OP_RETURN"
# Bezpieczny anchoring przez PSBT (bez przechowywania kluczy)
# OpenTimestamps + Merkle Root + Bitcoin OP_RETURN anchoring
"""
Timechain Desktop Widget v21.3.0 "Veritas Bridge + OTS + OP_RETURN"

Cel główny:
W pełni wielojęzyczna, dopracowana i zoptymalizowana aplikacja desktopowa.
Wersja z elementami Veritas Protocol UI + integracja OpenTimestamps + OP_RETURN anchoring.

ZMIANY W WERSJI v21.3.0 (Veritas Bridge + OTS + OP_RETURN):
- FEAT: Pełny mechanizm OP_RETURN anchoring (raw tx, broadcast, payload).
- FEAT: Placeholder %opreturn% w szablonach.
- FEAT: Veritas Seal Info z danymi OP_RETURN + przyciski Generate/Broadcast.
- FEAT: Sekcja 'OP_RETURN Anchoring' w zakładce Veritas.
- FEAT: Metoda generate_opreturn_tx() + broadcast via custom node.
- FEAT: Zapis .opreturn.txt obok każdego capture.
- FEAT: Pełna integracja OpenTimestamps (OTS) + Merkle Root.
- FEAT: Checkbox 'Always include Veritas Seal in every watermark'.
- FEAT: Przycisk 'Copy as OP_RETURN hex' w oknie Veritas Seal Info.
- FEAT: Sekcja Auto-Update w zakładce 'O programie'.
- FIX: QR Code + auto-scale.
- FIX: Tiled watermark przy dużych kątach.
- FIX: ColorAnalyzer na multi-monitor.
- FIX: PyBlock Launcher Wayland + Plasma.
- FIX: Walidacja glyph_seed (limit 128 znaków).
- FIX: Memory leak GIF/video.
- FIX: Centrowanie SettingsWindow na multi-monitor + DPI.
- OPT: Walidacja konfiguracji w Apply.
"""
from __future__ import annotations

# --- Standard Library Imports ---
import datetime
import hashlib
import json
import base64
import io
import struct
import tempfile
try:
    import pikepdf
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    pass
import locale
import logging
import os
import platform
import math
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple

# --- Veritas Engine (Thermodynamic Alignment Core) ---
try:
    import veritas_engine as ve
except ImportError:
    ve = None  # Fallback: engine functions used inline

# --- GUI Library Imports (Tkinter) ---
import tkinter as tk
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
except ImportError:
    pass
from tkinter import filedialog, messagebox, colorchooser, font as tkfont, ttk

# --- Metadata ---
APP_VERSION = "21.4.0"
APP_CODENAME = "Thermodynamic Alignment"
CONFIG_FILENAME = "timechain_config_v15.json"

# --- Veritas Protocol Visual Identity ---
VERITAS_PROTOCOL_VERSION = ve.VERITAS_PROTOCOL_VERSION if ve else "v10.3"
VERITAS_COLORS = {
    "gold": "#F5A623",       # Truth / Prawda
    "deep_blue": "#1A2332",  # Timechain / Depth
    "cyan": "#00D4FF",       # Verification / Weryfikacja
    "dark_bg": "#0D1117",    # Dark mode background
    "green_ok": "#2ECC71",   # Valid / Zweryfikowane
    "red_alert": "#E74C3C",  # Invalid / Alert
    "purple": "#8B5CF6",     # Governance / VoicePower
}
VERITAS_PHASES = [
    ("Α", "Stabilization", "Stabilizacja", 80),
    ("Β", "P2P Network", "Sieć P2P", 15),
    ("Γ", "Bitcoin L1/L2", "Bitcoin L1/L2", 5),
    ("Δ", "Binohash/ZK", "Binohash/ZK", 0),
    ("Ε", "Testnet", "Testnet", 0),
    ("Ζ", "Mainnet", "Mainnet", 0),
]
VERITAS_STATUS_ITEMS = [
    ("logic_engine", "XYZW Friction Engine", "Silnik XYZW Friction", "green_ok", "90%", "READY"),
    ("ai_safety", "AI Safety Pipeline", "Pipeline AI Safety", "green_ok", "95%", "B+"),
    ("governance", "Governance (VP/Slash)", "Governance (VP/Slash)", "gold", "40%", "OFF-CHAIN"),
    ("bitcoin", "Bitcoin L1/L2", "Bitcoin L1/L2", "red_alert", "10%", "PROTOTYPE"),
    ("p2p", "P2P Network", "Sieć P2P", "red_alert", "0%", "NOT IMPL."),
    ("binohash", "Binohash / BitVM", "Binohash / BitVM", "red_alert", "0%", "NOT IMPL."),
]

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- Dependency Availability Management ---
try:
    from PIL import (Image, ImageGrab, ImageDraw, ImageFont, ImageTk)
except ImportError:
    logging.critical("Krytyczny błąd: Brak modułu Pillow (PIL). Aplikacja nie może działać.")
    messagebox.showerror("Błąd krytyczny", "Nie znaleziono biblioteki Pillow (PIL).\nZainstaluj ją komendą: pip install Pillow")
    sys.exit(1)

_OPTIONAL_DEPENDENCIES: Dict[str, bool] = {
    'requests': False,
    'mss': False,
    'cv2': False,
    'numpy': False,
    'pynput': False,
    'pyperclip': False,
    'screeninfo': False,
    'qrcode': False
}

try:
    import requests
    _OPTIONAL_DEPENDENCIES['requests'] = True
except ImportError:
    logging.warning("Brak 'requests'. Pobieranie danych z publicznych API będzie niemożliwe.")
try:
    import mss
    _OPTIONAL_DEPENDENCIES['mss'] = True
except ImportError:
    logging.warning("Brak 'mss'. Przechwytywanie ekranu będzie wolniejsze lub niemożliwe dla wideo.")
try:
    import cv2
    _OPTIONAL_DEPENDENCIES['cv2'] = True
except ImportError:
    logging.warning("Brak 'opencv-python'. Nagrywanie wideo niedostępne.")
try:
    import numpy as np
    _OPTIONAL_DEPENDENCIES['numpy'] = True
except ImportError:
    logging.warning("Brak 'numpy'. Nagrywanie wideo i zaawansowana analiza obrazu niedostępne.")
try:
    from pynput import keyboard
    _OPTIONAL_DEPENDENCIES['pynput'] = True
except ImportError:
    logging.warning("Brak 'pynput'. Globalne skróty klawiszowe niedostępne.")
try:
    import pyperclip
    _OPTIONAL_DEPENDENCIES['pyperclip'] = True
except ImportError:
    logging.warning("Brak 'pyperclip'. Kopiowanie do schowka niedostępne.")
try:
    from screeninfo import get_monitors
    _OPTIONAL_DEPENDENCIES['screeninfo'] = True
except ImportError:
    logging.warning("Brak 'screeninfo'. Wybór monitora ograniczony.")
try:
    import qrcode
    _OPTIONAL_DEPENDENCIES['qrcode'] = True
except ImportError:
    logging.warning("Brak 'qrcode'. Dynamiczny kod QR niedostępny. Zainstaluj: pip install qrcode[pil]")

_OPTIONAL_DEPENDENCIES['opentimestamps'] = False
try:
    import opentimestamps
    from opentimestamps.core.timestamp import DetachedTimestampFile
    from opentimestamps.core.op import OpSHA256
    _OPTIONAL_DEPENDENCIES['opentimestamps'] = True
except ImportError:
    logging.warning("Brak 'opentimestamps'. Integracja OTS niedostępna. Zainstaluj: pip install opentimestamps")

_OPTIONAL_DEPENDENCIES['bitcoinlib'] = False
try:
    from bitcoinlib.transactions import Transaction, Output, Input
    from bitcoinlib.keys import Key
    _OPTIONAL_DEPENDENCIES['bitcoinlib'] = True
except ImportError:
    logging.warning("Brak 'bitcoinlib'. Generowanie OP_RETURN tx niedostępne. Zainstaluj: pip install bitcoinlib")


# --- Global Constants & Helper Functions ---
REQUESTS_TIMEOUT = ve.REQUESTS_TIMEOUT_S if ve else 10

def _is_windows() -> bool:
    return platform.system() == "Windows"

def set_dpi_awareness_windows() -> None:
    if _is_windows():
        try:
            from ctypes import windll, c_void_p
            awareness_context = c_void_p(-4)  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
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
                "lang_name": "Polski", "settings_title": "Ustawienia - Timechain Widget v{version}", "apply_button": "Zastosuj", "close_button": "Zamknij", "apply_success": "Ustawienia zapisane.", "lang_changed_title": "Zmiana języka", "lang_changed_msg": "Język został zmieniony. Interfejs ustawień zostanie odświeżony.", "tab_template": "Szablon i Wygląd", "tab_capture": "Przechwytywanie", "tab_data": "Dane i Integracje", "tab_about": "O programie", "tab_veritas": "Veritas", "ctx_copy": "Kopiuj tekst", "ctx_pyblock": "Uruchom PyBlock (w konsoli)...", "ctx_settings": "Ustawienia...", "ctx_stamp": "Zapisz stempel...", "ctx_close": "Zamknij", "ctx_quick_png": "⚡ Szybki zrzut (PNG)", "ctx_quick_gif": "🎬 Szybki zapis (GIF, 5s)", "ctx_veritas_seal": "🔱 Veritas Seal Info...", "general_lang_label": "Język:", "template_creator_title": "Kreator Szablonu", "samples_btn": "Przykłady...", "date_btn": "Data...", "time_btn": "Czas...", "separator_btn": "Separator...", "special_btn": "Specjalne...", "reset_btn": "Reset", "appearance_title": "Wygląd i Opcje", "font_label": "Czcionka:", "size_label": "Rozmiar:", "bold_chk": "Pogrubienie", "italic_chk": "Kursywa", "color_text_btn": "Kolor tekstu", "color_shadow_btn": "Kolor cienia", "use_shadow_chk": "Użyj cienia", "thickness_label": "Grubość:", "style_label": "Styl:", "direction_label": "Kierunek:", "style_outline": "Obrys", "style_3d": "Cień 3D", "dir_dr": "Prawy-Dół", "dir_dl": "Lewy-Dół", "dir_ur": "Prawy-Góra", "dir_ul": "Lewy-Góra", "gen_glyph_chk": "Generuj glif:", "insert_glyph_btn": "Wstaw", "full_hash_chk": "Wyświetlaj pełny hash bloku", "lock_position_chk": "Zablokuj pozycję", "always_on_top_chk": "Zawsze na wierzchu", "hotkeys_title": "Skróty Klawiszowe", "hotkeys_desc": "Cały ekran (PNG/MP4/GIF): Ctrl + Shift + 1 / 2 / 3\nZaznaczony obszar (PNG/MP4/GIF): Ctrl + Alt + 1 / 2 / 3", "capture_options_title": "Opcje Przechwytywania", "capture_monitor_label": "Przechwytywany monitor:", "capture_all_screens": "Wszystkie ekrany", "primary_monitor_tag": " (Główny)", "hide_widget_chk": "Ukryj widget podczas przechwytywania", "recording_options_title": "Opcje Nagrywania", "video_duration_label": "Długość wideo (s):", "gif_duration_label": "Długość GIF (s):", "path_title": "Lokalizacja i Nazwa Plików", "change_btn": "Zmień...", "prefix_chk": "Używaj prefiksu w nazwie pliku:", "prefix_template_creator_title": "Kreator Szablonu Prefiksu", "watermark_title": "Znak Wodny (Odcisk Widgeta)", "line_1_chk": "Linia 1", "line_2_chk": "Linia 2", "line_3_chk": "Linia 3", "opacity_label": "Krycie (%):", "angle_label": "Kąt (°):", "watermark_style_label": "Styl:", "watermark_style_tiled": "Kafelki", "watermark_style_arranged": "Aranżowany", "watermark_style_single": "Pojedynczy (skalowany)", "watermark_style_vertical": "Wyrównany w pionie", "watermark_style_qrcode": "Kod QR", "watermark_count_label": "Liczba:", "watermark_use_shadow_chk": "Użyj cienia", "watermark_auto_scale_chk": "Skaluj automatycznie (rozmiar, kąt)", "watermark_qr_size_label": "Rozmiar QR Kodu:", "watermark_qr_position_label": "Pozycja QR Kodu:", "pos_center": "Środek", "pos_tl": "Górny-Lewy", "pos_tr": "Górny-Prawy", "pos_bl": "Dolny-Lewy", "pos_br": "Dolny-Prawy", "glyph_mech_title": "Mechanizm Glifów", "glyph_desc": "Glif to unikalny, stylizowany identyfikator wizualny, który reprezentuje podany przez Ciebie tekst (np. nazwę projektu, pseudonim lub hasło). Działa jak cyfrowy 'symbol' lub 'sigil' – jest zawsze taki sam dla tego samego tekstu, ale zupełnie inny nawet po drobnej zmianie.\n\n**Instrukcja:**\n1. Wpisz swoje słowa-klucze w polu 'Generuj glif' w zakładce 'Szablon i Wygląd'.\n2. Użyj przycisku 'Wstaw' obok pola, aby dodać znacznik `%glyph%` w wybranym miejscu szablonu.", "node_title": "Własny Węzeł ₿itcoina", "use_node_chk": "Użyj własnego węzła", "rpc_url_label": "RPC URL:", "user_label": "Użytkownik:", "pass_label": "Hasło:", "pyblock_title": "Integracja z PyBlock", "pyblock_cmd_label": "Komenda uruchamiająca PyBlock:", "about_info_title": "Informacje", "about_author": "Autor: Wojciech 'adepthus' Durmaj", "about_desc": "Narzędzie służące do trwałego osadzania dowodu istnienia danych w czasie (timestamping) poprzez powiązanie ich z publicznym timechainem ₿itcoina. Aplikacja wyświetla aktualne informacje o ostatnim bloku i pozwala na tworzenie cyfrowych 'stempli' oraz wizualnych znaków wodnych, które mogą służyć jako kryptograficzny dowód, że dane istniały w określonym momencie.", "about_instruction_title": "Do Czego Służy Timechain Widget?", "about_instruction_desc": "Timechain Widget to \"cyfrowa pieczęć notarialna\", która pozwala na błyskawiczne tworzenie niepodważalnych, datowanych dowodów cyfrowych. Jego zadaniem jest walka z dezinformacją i \"przedawnieniem\" prawdy poprzez trwałe \"zapieczętowywanie\" dowolnego fragmentu Twojego ekranu w czasie.\n\nJak Działa?\nZa pomocą prostego skrótu klawiszowego, program robi zrzut ekranu (lub nagranie wideo/GIF), pobiera w czasie rzeczywistym dane z publicznego blockchaina Bitcoina (numer i hash ostatniego bloku), a następnie nakłada te informacje na obraz w formie spersonalizowanego znaku wodnego (\"watermarka\"). Zapisany w ten sposób plik staje się \"pieczęcią czasu\" – artefaktem, którego istnienia w danym momencie nie da się podważyć, ponieważ jest on kryptograficznie powiązany z globalnym, zdecentralizowanym zegarem, jakim jest Bitcoin.", "about_glyph_title": "Czym Jest i Jak Działa 'Glif'?", "about_glyph_desc": "Funkcja Glifu:\n\"Glif\" (%glyph%) to Twoja osobista, unikalna sygnatura cyfrowa wpleciona w pieczęć czasu. Nie jest to losowy ciąg znaków. Jest to wizualny \"odcisk palca\" dowolnego tekstu, który wpiszesz – czy to Twojego pseudonimu, nazwy projektu, czy tajnego hasła.\n\nDlaczego to Działa (Mechanizm):\nGlif działa w oparciu o kryptograficzną funkcję skrótu (hash), w tym przypadku SHA-256 (poprzednio SHA-1).\n\n- Wejście: Bierze dowolny tekst, który podasz (np. \"adepthus-was-here\").\n- Przetwarzanie: Przekształca ten tekst w długi, unikalny ciąg znaków (hash).\n- Wizualizacja: Bierze fragment tego hasha (np. pierwsze 8 znaków) i stylizuje go (np. AbCd12Ef), tworząc charakterystyczny, powtarzalny, ale trudny do odgadnięcia \"glif\".\n\nKluczowa Właściwość:\nDzięki właściwościom funkcji skrótu, nawet najmniejsza zmiana w tekście wejściowym (np. dodanie kropki) spowoduje wygenerowanie całkowicie innego glifu. Jednocześnie, ten sam tekst wejściowy zawsze wygeneruje ten sam glif.\n\nW Rezultacie:\nGlif jest Twoim osobistym, tajnym podpisem. Tylko Ty, znając oryginalny tekst (\"ziarno\"), jesteś w stanie odtworzyć ten sam, unikalny wzorzec. Dla reszty świata jest to enigmatyczny, ale konsekwentny znak, który potwierdza Twoje autorstwo na przestrzeni wielu różnych dowodów.", "about_deps_title": "Status zależności", "about_qr_options_title": "Opcje kodu QR", "about_show_qr_chk": "Pokaż kod QR", "about_qr_size_label": "Rozmiar obrazów:", "dep_found": "Znaleziono", "dep_missing": "Brak",
                "veritas_epistemic_title": "Status Epistemiczny Protokołu", "veritas_watermark_title": "Veritas Watermark", "veritas_include_seal_chk": "Dołącz Veritas Epistemic Seal do watermarku", "veritas_epistemic_tag_label": "Epistemic Tag:", "veritas_readiness_title": "Gotowość Protokołu (v10.3)", "veritas_philosophy_title": "Filozofia Timechain", "veritas_philosophy_quote": "Veritas est Fundamentum. Bitcoin est Tempus.", "veritas_philosophy_pillars": "TRUTH as PATTERN → IDENTITY as INTENTION → TIME as EVOLUTION", "veritas_roadmap_title": "Droga do Sovereign Mainnet", "veritas_seal_dialog_title": "Veritas Seal Info", "veritas_seal_copy_json": "Kopiuj jako JSON", "veritas_protocol_label": "Protokół Veritas", "veritas_bar_color_title": "Kolor paska statusu", "veritas_bar_ok_label": "Połączenie OK:", "veritas_bar_err_label": "Błąd połączenia:", "error_missing_video_deps": "Nagrywanie wideo wymaga 'mss', 'opencv-python' i 'numpy'.", "error_missing_gif_deps": "Nagrywanie GIF wymaga 'mss'.", "error_missing_deps_title": "Brak bibliotek", "pyblock_no_command_title": "Brak Komendy", "pyblock_no_command_msg": "Nie skonfigurowano komendy do uruchomienia PyBlock. Sprawdź ustawienia.", "error_capture_folder_invalid": "Folder do zapisu przechwytywań nie istnieje lub nie jest zapisywalny.", "error_node_url_invalid": "Adres URL węzła Bitcoin jest nieprawidłowy.",
                "veritas_always_seal_chk": "Zawsze dołączaj Veritas Seal do każdego watermarku", "veritas_copy_opreturn": "Kopiuj jako OP_RETURN hex", "auto_update_title": "Auto-Update", "auto_update_chk": "Sprawdzaj aktualizacje automatycznie", "auto_update_check_btn": "Sprawdź teraz", "auto_update_available": "Nowa wersja dostępna: {version}!", "auto_update_up_to_date": "Masz najnowszą wersję.", "auto_update_error": "Nie udało się sprawdzić aktualizacji.", "glyph_seed_warning": "Ziarno glifu nie może przekraczać 128 znaków.", "ots_title": "Integracja OpenTimestamps", "ots_enabled_chk": "Włącz OpenTimestamps (OTS)", "ots_calendar_label": "URL kalendarza OTS:", "ots_auto_submit_chk": "Automatycznie wysyłaj do kalendarza po przechwyceniu", "ots_merkle_root_label": "Merkle Root:", "ots_proof_label": "OTS Proof:", "ots_verify_btn": "Zweryfikuj OTS", "ots_submit_btn": "Wyślij do OTS teraz", "ots_pending": "OTS oczekuje", "ots_verified": "OTS zweryfikowane", "ots_submit_success": "Przesłano do kalendarza OTS.", "ots_submit_error": "Błąd przesyłania do OTS.", "ots_verify_ok": "Plik OTS poprawny.", "ots_verify_fail": "Weryfikacja OTS nie powiodła się.", "ots_missing_deps": "Integracja OTS wymaga biblioteki 'opentimestamps' lub 'requests'.",
                "opreturn_title": "OP_RETURN Anchoring (PSBT)", "opreturn_enabled_chk": "Włącz OP_RETURN (PSBT)", "opreturn_prefix_label": "Prefix payloadu:", "opreturn_use_node_chk": "Użyj Bitcoin Core (watch-only)", "opreturn_fee_label": "Fee (sat/vB):", "opreturn_broadcast_chk": "Automatyczny broadcast (wymaga privkey)", "opreturn_broadcast_warning": "⚠️ UWAGA: Podajesz prywatny klucz — używaj tylko z własnym node!", "opreturn_payload_label": "OP_RETURN Payload:", "opreturn_generate_btn": "Generate PSBT", "opreturn_open_psbt_btn": "Open in Sparrow/Electrum", "opreturn_broadcast_core_btn": "Broadcast via Core", "opreturn_broadcast_btn": "Broadcast now", "opreturn_ready": "PSBT ready", "opreturn_saved": "Zapisano plik .opreturn.txt", "opreturn_tx_generated": "Raw TX wygenerowane.", "opreturn_broadcast_ok": "Transakcja wysłana pomyślnie.", "opreturn_broadcast_error": "Błąd broadcastu transakcji.", "opreturn_missing_deps": "Generowanie OP_RETURN wymaga 'bitcoinlib'.", "batch_seal_title_dlg": "Masowe stemplowanie", "batch_seal_msg_dlg": "Przeciągnięto folder zawierający {total} wspieranych plików ({img_count} obrazów, {pdf_count} PDF).\n\nCzy chcesz rozpocząć masowe stemplowanie całego katalogu?",
                "days_full": ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"], "days_abbr": ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"], "months_full": ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"], "months_abbr": ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze", "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"],
            },
            'en': {"lang_name": "English", "settings_title": "Settings - Timechain Widget v{version}", "apply_button": "Apply", "close_button": "Close", "apply_success": "Settings saved.", "lang_changed_title": "Language Change", "lang_changed_msg": "Language has been changed. The settings interface will now refresh.", "tab_template": "Template & Appearance", "tab_capture": "Capture", "tab_data": "Data & Integrations", "tab_about": "About", "tab_veritas": "Veritas", "ctx_copy": "Copy text", "ctx_pyblock": "Run PyBlock (in console)...", "ctx_settings": "Settings...", "ctx_stamp": "Save stamp...", "ctx_close": "Close", "ctx_quick_png": "⚡ Quick Capture (PNG)", "ctx_quick_gif": "🎬 Quick Record (GIF, 5s)", "ctx_veritas_seal": "🔱 Veritas Seal Info...", "general_lang_label": "Language:", "template_creator_title": "Template Creator", "samples_btn": "Samples...", "date_btn": "Date...", "time_btn": "Time...", "separator_btn": "Separator...", "special_btn": "Special...", "reset_btn": "Reset", "appearance_title": "Appearance & Options", "font_label": "Font:", "size_label": "Size:", "bold_chk": "Bold", "italic_chk": "Italic", "color_text_btn": "Text color", "color_shadow_btn": "Shadow color", "use_shadow_chk": "Use shadow", "thickness_label": "Thickness:", "style_label": "Style:", "direction_label": "Direction:", "style_outline": "Outline", "style_3d": "3D Shadow", "dir_dr": "Down-Right", "dir_dl": "Down-Left", "dir_ur": "Up-Right", "dir_ul": "Up-Left", "gen_glyph_chk": "Generate glyph:", "insert_glyph_btn": "Insert", "full_hash_chk": "Display full block hash", "lock_position_chk": "Lock position", "always_on_top_chk": "Always on top", "hotkeys_title": "Hotkeys", "hotkeys_desc": "Full Screen (PNG/MP4/GIF): Ctrl + Shift + 1 / 2 / 3\nSelected Region (PNG/MP4/GIF): Ctrl + Alt + 1 / 2 / 3", "capture_options_title": "Capture Options", "capture_monitor_label": "Capture monitor:", "capture_all_screens": "All screens", "primary_monitor_tag": " (Primary)", "hide_widget_chk": "Hide widget on capture", "recording_options_title": "Recording Options", "video_duration_label": "Video duration (s):", "gif_duration_label": "GIF duration (s):", "path_title": "File Location & Naming", "change_btn": "Change...", "prefix_chk": "Use prefix in filename:", "prefix_template_creator_title": "Prefix Template Creator", "watermark_title": "Watermark (Widget Imprint)", "line_1_chk": "Line 1", "line_2_chk": "Line 2", "line_3_chk": "Line 3", "opacity_label": "Opacity (%):", "angle_label": "Angle (°):", "watermark_style_label": "Style:", "watermark_style_tiled": "Tiled", "watermark_style_arranged": "Arranged", "watermark_style_single": "Single (scaled)", "watermark_style_vertical": "Vertical Stack", "watermark_style_qrcode": "QR Code", "watermark_count_label": "Count:", "watermark_use_shadow_chk": "Use shadow", "watermark_auto_scale_chk": "Auto-scale (size, angle)", "watermark_qr_size_label": "QR Code Size:", "watermark_qr_position_label": "QR Code Position:", "pos_center": "Center", "pos_tl": "Top-Left", "pos_tr": "Top-Right", "pos_bl": "Bottom-Left", "pos_br": "Bottom-Right", "glyph_mech_title": "Glyph Mechanism", "glyph_desc": "A glyph is a unique, stylized visual identifier that represents the text you provide (e.g., a project name, nickname, or phrase). It acts like a digital 'symbol' or 'sigil'—it's always the same for the same text but completely different after even a minor change.\n\n**Instructions:**\n1. Enter your keywords in the 'Generate glyph' field in the 'Template & Appearance' tab.\n2. Use the 'Insert' button next to the field to add the `%glyph%` placeholder to your desired template location.", "node_title": "Custom ₿itcoin Node", "use_node_chk": "Use custom node", "rpc_url_label": "RPC URL:", "user_label": "User:", "pass_label": "Password:", "pyblock_title": "PyBlock Integration", "pyblock_cmd_label": "Command to run PyBlock:", "about_info_title": "Information", "about_author": "Author: Wojciech 'adepthus' Durmaj", "about_desc": "A tool for permanently timestamping data by linking it to the public ₿itcoin timechain. The application displays current information about the latest block and allows for the creation of digital 'stamps' and visual watermarks, which can serve as cryptographic proof that the data existed at a specific moment in time.", "about_instruction_title": "What is the Timechain Widget for?", "about_instruction_desc": "The Timechain Widget is a 'digital notary seal' for creating undeniable, dated digital evidence. Its purpose is to combat disinformation by 'sealing' a fragment of your screen in time. Using a keyboard shortcut, the program takes a screenshot, fetches data from the Bitcoin blockchain (block number and hash), and overlays it as a personalized watermark. The saved file becomes a 'timestamp'—an artifact cryptographically linked to the global, decentralized clock that is Bitcoin.", "about_glyph_title": "What is a 'Glyph' and How Does It Work?", "about_glyph_desc": "The 'Glyph' (%glyph%) is your unique digital signature, a visual 'fingerprint' of any text (nickname, project name). It's based on the SHA-256 hash function (formerly SHA-1): it takes text, converts it into a unique hash, and then stylizes a fragment of it (e.g., AbCd12Ef). Even a minor change in the input text creates a completely different glyph, but the same text always yields the same result. It's your personal, secret signature, confirming authorship.", "about_deps_title": "Dependency Status", "about_qr_options_title": "QR Code Options", "about_show_qr_chk": "Show QR Code", "about_qr_size_label": "Image Size:", "dep_found": "Found", "dep_missing": "Missing",
                "veritas_epistemic_title": "Protocol Epistemic Status", "veritas_watermark_title": "Veritas Watermark", "veritas_include_seal_chk": "Include Veritas Epistemic Seal in watermark", "veritas_epistemic_tag_label": "Epistemic Tag:", "veritas_readiness_title": "Protocol Readiness (v10.3)", "veritas_philosophy_title": "Timechain Philosophy", "veritas_philosophy_quote": "Veritas est Fundamentum. Bitcoin est Tempus.", "veritas_philosophy_pillars": "TRUTH as PATTERN → IDENTITY as INTENTION → TIME as EVOLUTION", "veritas_roadmap_title": "Road to Sovereign Mainnet", "veritas_seal_dialog_title": "Veritas Seal Info", "veritas_seal_copy_json": "Copy as JSON", "veritas_protocol_label": "Veritas Protocol", "veritas_bar_color_title": "Status Bar Color", "veritas_bar_ok_label": "Connection OK:", "veritas_bar_err_label": "Connection Error:", "error_missing_video_deps": "Video recording requires 'mss', 'opencv-python' and 'numpy'.", "error_missing_gif_deps": "GIF recording requires 'mss'.", "error_missing_deps_title": "Missing Libraries", "pyblock_no_command_title": "No Command", "pyblock_no_command_msg": "No PyBlock command configured. Check settings.", "error_capture_folder_invalid": "Capture folder does not exist or is not writable.", "error_node_url_invalid": "Bitcoin node URL is invalid.",
                "veritas_always_seal_chk": "Always include Veritas Seal in every watermark", "veritas_copy_opreturn": "Copy as OP_RETURN hex", "auto_update_title": "Auto-Update", "auto_update_chk": "Check for updates automatically", "auto_update_check_btn": "Check now", "auto_update_available": "New version available: {version}!", "auto_update_up_to_date": "You are running the latest version.", "auto_update_error": "Could not check for updates.", "glyph_seed_warning": "Glyph seed must not exceed 128 characters.", "ots_title": "OpenTimestamps Integration", "ots_enabled_chk": "Enable OpenTimestamps (OTS)", "ots_calendar_label": "OTS Calendar URL:", "ots_auto_submit_chk": "Auto-submit to calendar after capture", "ots_merkle_root_label": "Merkle Root:", "ots_proof_label": "OTS Proof:", "ots_verify_btn": "Verify OTS", "ots_submit_btn": "Submit to OTS now", "ots_pending": "OTS pending", "ots_verified": "OTS verified", "ots_submit_success": "Submitted to OTS calendar.", "ots_submit_error": "Error submitting to OTS.", "ots_verify_ok": "OTS file is valid.", "ots_verify_fail": "OTS verification failed.", "ots_missing_deps": "OTS integration requires 'opentimestamps' or 'requests' library.",
                "opreturn_title": "OP_RETURN Anchoring (PSBT)", "opreturn_enabled_chk": "Enable OP_RETURN (PSBT)", "opreturn_prefix_label": "Payload prefix:", "opreturn_use_node_chk": "Use Bitcoin Core (watch-only)", "opreturn_fee_label": "Fee (sat/vB):", "opreturn_broadcast_chk": "Auto-broadcast (requires privkey)", "opreturn_broadcast_warning": "⚠️ WARNING: You are providing a private key — use only with your own node!", "opreturn_payload_label": "OP_RETURN Payload:", "opreturn_generate_btn": "Generate PSBT", "opreturn_open_psbt_btn": "Open in Sparrow/Electrum", "opreturn_broadcast_core_btn": "Broadcast via Core", "opreturn_broadcast_btn": "Broadcast now", "opreturn_ready": "PSBT ready", "opreturn_saved": "Saved .opreturn.txt file", "opreturn_tx_generated": "Raw TX generated.", "opreturn_broadcast_ok": "Transaction broadcast successfully.", "opreturn_broadcast_error": "Transaction broadcast error.", "opreturn_missing_deps": "OP_RETURN generation requires 'bitcoinlib'.", "batch_seal_title_dlg": "Batch Sealing", "batch_seal_msg_dlg": "Dropped a folder containing {total} supported files ({img_count} images, {pdf_count} PDFs).\n\nDo you want to start batch sealing the entire directory?",
                "days_full": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "days_abbr": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "months_full": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], "months_abbr": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]},
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
        self.config_path = self._get_config_path(filename)
        self._config_lock = threading.Lock()
        self.config = self._load()

    def _get_config_path(self, filename: str) -> str:
        try:
            base_path = (os.getenv('APPDATA') if _is_windows() else os.path.expanduser("~"))
            if not base_path:
                base_path = os.path.expanduser("~")
            app_dir = os.path.join(base_path, ".TimechainWidget")
            os.makedirs(app_dir, exist_ok=True)
            return os.path.join(app_dir, filename)
        except OSError as e:
            logging.error(f"Nie można utworzyć katalogu konfiguracyjnego: {e}")
            return filename

    def get_default_config(self) -> Dict[str, Any]:
        # Auto-detect system language
        try:
            import locale
            sys_lang = locale.getlocale()[0] or "en"
            default_lang = "pl" if sys_lang.startswith("pl") else "en"
        except Exception:
            default_lang = "en"
        return {
            "version": APP_VERSION, "language": default_lang, "line_1_enabled": True, "prompt_line_1": "'adepthus-was-here' '@' 'timechains'", "line_2_enabled": True, "prompt_line_2": "d MMMM yyyy HH:mm | '₿eattime' @ | 'Block:' %blockheight%", "line_3_enabled": True, "prompt_line_3": "'Hash:' %hash%", "generate_glyphs": True, "glyph_seed": "adepthus-was-here", "font_family": "Segoe UI", "base_font_size": 15, "font_weight": "bold", "font_slant": "roman", "text_color": "white", "use_outline": True, "outline_color": "#333333", "outline_thickness": 2, "shadow_style": "outline", "shadow_direction": "down-right", "line_1_align": "left", "line_2_align": "left", "line_3_align": "left", "lock_position": False, "always_on_top": True, "display_full_hash": False, "capture_folder": os.path.join(os.path.expanduser("~"), "Timechain_Captures"), "capture_filename_prefix": "timechain_capture_%blockheight%_", "use_capture_filename_prefix": True, "hide_widget_on_capture": True, "capture_screen": "Wszystkie ekrany", "watermark_style": "tiled", "watermark_arranged_count": 5, "watermark_opacity": 30, "watermark_angle": 30, "watermark_use_shadow": False, "watermark_auto_scale": True, "watermark_qr_code_size": 150, "watermark_qr_position": "center", "video_duration": 10, "gif_duration": 7, "auto_color_inversion": False, "brightness_threshold": 128, "data_fetch_interval_s": 60, "use_custom_node": False, "custom_node_url": "http://127.0.0.1:8332", "custom_node_user": "", "custom_node_pass": "", "pyblock_command": "python -m pyblock" if _is_windows() else "pyblock", "last_position": "+100+100", "about_show_qr_code": True, "about_qr_code_size": 120, "veritas_include_seal": False, "veritas_epistemic_tag": "", "status_bar_color_ok": "#F5A623", "status_bar_color_err": "#E74C3C", "veritas_always_seal": False, "auto_update_check": False, "ots_enabled": False, "ots_calendar_url": "https://a.pool.opentimestamps.org", "ots_auto_submit": True, "opreturn_enabled": False, "opreturn_payload_prefix": "VERITAS:", "opreturn_use_bitcoin_core": False, "bitcoin_core_rpc_url": "http://127.0.0.1:8332", "bitcoin_core_rpc_user": "", "bitcoin_core_rpc_pass": "", "opreturn_fee_sat_per_vb": 15
        }

    def _load(self) -> Dict[str, Any]:
        defaults = self.get_default_config()
        if not os.path.exists(self.config_path):
            self.save(defaults)
            return defaults
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            updated = False
            for key, value in defaults.items():
                if key not in loaded_config:
                    loaded_config[key] = value
                    updated = True
            if updated:
                self.save(loaded_config)
            return loaded_config
        except (json.JSONDecodeError, TypeError, IOError) as e:
            logging.error(f"Błąd odczytu konfiguracji: {e}. Przywracanie domyślnych.")
            self.save(defaults)
            return defaults

    def get(self, key: str, default: Any = None) -> Any:
        with self._config_lock:
            return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._config_lock:
            self.config[key] = value

    def save(self, config_data: Optional[Dict[str, Any]] = None) -> None:
        with self._config_lock:
            data_to_save = config_data if config_data is not None else self.config
            try:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            except IOError as e:
                logging.error(f"Nie udało się zapisać konfiguracji: {e}")

class DataManager:
    """Zarządza pobieraniem i buforowaniem danych z blockchaina."""
    def __init__(self, app: "TimechainApp"):
        self.app = app
        self.config = app.config_manager
        self._data_cache: Dict[str, Any] = {"blockheight": "Ładowanie...", "hash_full": "...", "hash_short": "..."}
        self._data_lock = threading.Lock()
        self._transient: Dict[str, Any] = {}  # Thread-safe transient store for UI state
        self._transient_lock = threading.Lock()

    def set_transient(self, key: str, value: Any) -> None:
        """Store transient UI state (e.g. latest_psbt_path). Thread-safe."""
        with self._transient_lock:
            self._transient[key] = value

    def get_transient(self, key: str, default: Any = None) -> Any:
        """Retrieve transient UI state. Thread-safe."""
        with self._transient_lock:
            return self._transient.get(key, default)

    def fetch_all_data(self) -> None:
        if not _OPTIONAL_DEPENDENCIES['requests'] and not self.config.get("use_custom_node"):
            logging.error("Brak biblioteki 'requests' uniemożliwia pobieranie danych z publicznych API.")
            with self._data_lock:
                self._data_cache["error"] = "Brak 'requests'"
            self.app.request_ui_update()
            return
        try:
            success = False
            if self.config.get("use_custom_node"):
                success = self._fetch_from_custom_node(requests)
            if not success and _OPTIONAL_DEPENDENCIES['requests']:
                success = self._fetch_from_combined_api(requests)
            if not success and _OPTIONAL_DEPENDENCIES['requests']:
                self._fetch_from_separate_apis(requests)

            with self._data_lock:
                if isinstance(self._data_cache.get("blockheight"), int):
                    self._data_cache.pop("error", None)
                else:
                    self._data_cache["error"] = "Błąd pobierania danych"
        except Exception as e:
            logging.error(f"Nieoczekiwany błąd podczas pobierania danych: {e}")
            with self._data_lock:
                self._data_cache["error"] = "Błąd sieci"
        finally:
            self.app.request_ui_update()

    def _fetch_from_custom_node(self, requests_lib) -> bool:
        url = self.config.get("custom_node_url")
        auth = (self.config.get("custom_node_user"), self.config.get("custom_node_pass"))
        if not url:
            return False
        try:
            def rpc_call(method):
                payload = {'jsonrpc': '1.0', 'id': 'tc', 'method': method}
                resp = requests_lib.post(url, json=payload, auth=auth, timeout=REQUESTS_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            height, hash_val = rpc_call('getblockcount').get('result'), rpc_call('getbestblockhash').get('result')
            if isinstance(height, int) and isinstance(hash_val, str):
                self._update_cache(height, hash_val)
                return True
        except requests_lib.RequestException as e:
            logging.error(f"Błąd połączenia z węzłem ({url}): {e}")
        return False

    def _fetch_from_combined_api(self, requests_lib) -> bool:
        url = "https://blockchain.info/latestblock"
        try:
            response = requests_lib.get(url, timeout=REQUESTS_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            height, hash_val = data.get('height'), data.get('hash')
            if isinstance(height, int) and isinstance(hash_val, str):
                self._update_cache(height, hash_val)
                return True
        except requests_lib.RequestException as e:
            logging.error(f"Błąd pobierania danych z {url}: {e}")
        return False

    def _fetch_from_separate_apis(self, requests_lib) -> None:
        apis = {"height": ["https://blockstream.info/api/blocks/tip/height"], "hash": ["https://blockstream.info/api/blocks/tip/hash"]}
        height_str = self._fetch_parallel(requests_lib, apis["height"])
        if height_str and height_str.isdigit():
            with self._data_lock:
                self._data_cache["blockheight"] = int(height_str)
        if (hash_val := self._fetch_parallel(requests_lib, apis["hash"])) and len(hash_val) == 64:
            if isinstance(current_height := self.get_data_snapshot().get("blockheight", 0), int):
                self._update_cache(current_height, hash_val)

    def _fetch_parallel(self, requests_lib, urls: List[str]) -> Optional[str]:
        with ThreadPoolExecutor(max_workers=len(urls)) as executor:
            futures = {executor.submit(requests_lib.get, url, timeout=5) for url in urls}
            for future in as_completed(futures):
                try:
                    response = future.result()
                    response.raise_for_status()
                    return response.text.strip()
                except requests_lib.RequestException:
                    continue
        return None

    def _update_cache(self, height: int, hash_val: str) -> None:
        with self._data_lock:
            if self._data_cache.get("blockheight") != height:
                self._data_cache["last_block_time_local"] = time.time()
            self._data_cache["blockheight"] = height
            self._data_cache["hash_full"] = hash_val
            self._data_cache["hash_short"] = f"{hash_val[:6]}...{hash_val[-4:]}"
            logging.info(f"Data updated: Block {height}")

    def get_data_snapshot(self) -> Dict[str, Any]:
        with self._data_lock:
            return self._data_cache.copy()

class TemplateEngine:
    """Odpowiada za renderowanie tekstu widgeta na podstawie szablonów i danych."""
    def __init__(self, app: "TimechainApp"):
        self.app, self.config, self.data_manager, self.lang = app, app.config_manager, app.data_manager, app.lang
        self.special_placeholder_regex = re.compile("(%glyph%|%blockheight%|%hash%|%veritas%|%seal%|%protocol_status%|%ots%|%opreturn%|@|'[^']*')")
        self.FORMAT_CODE_MAP: Dict = {}
        self.dt_format_regex = re.compile('a^')
        self.on_language_change()

    def on_language_change(self):
        self.FORMAT_CODE_MAP = {'yyyy': '%Y', 'yy': '%y', 'MMMM': self.lang.get_date_names("months_full"), 'MMM': self.lang.get_date_names("months_abbr"), 'MM': '%m', 'M': lambda dt: str(dt.month), 'dddd': self.lang.get_date_names("days_full"), 'ddd': self.lang.get_date_names("days_abbr"), 'dd': '%d', 'd': lambda dt: str(dt.day), 'HH': '%H', 'H': lambda dt: str(dt.hour), 'hh': '%I', 'h': lambda dt: str(int(dt.strftime('%I'))), 'mm': '%M', 'm': lambda dt: str(dt.minute), 'ss': '%S', 's': lambda dt: str(dt.second), 'SSS': lambda dt: f"{dt.microsecond // 1000:03d}", 'SS': lambda dt: f"{dt.microsecond // 10000:02d}", 'S': lambda dt: f"{dt.microsecond // 100000:d}", 'tt': '%p', 't': lambda dt: dt.strftime('%p')[0] if dt.strftime('%p') else ''}
        self.dt_format_regex = re.compile('(' + '|'.join(map(re.escape, sorted(self.FORMAT_CODE_MAP.keys(), key=len, reverse=True))) + ')')
        logging.info(f"Zaktualizowano formaty daty dla języka: {self.lang.current_lang_code}")

    @staticmethod
    def _get_swatch_internet_time() -> str:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        biel_time = now_utc + datetime.timedelta(hours=1)
        return f"@{int((biel_time.hour * 3600 + biel_time.minute * 60 + biel_time.second) / 86.4):03d}"

    def render(self, config_override: Optional[Dict[str, Any]] = None) -> str:
        data = self.data_manager.get_data_snapshot()
        cfg = config_override or self.config.config
        if "error" in data:
            return f"Timechain Widget\n{data['error']}\nSprawdź połączenie..."
        now = datetime.datetime.now()
        seal_id = self._generate_seal_id(data, now)
        replacements = {'@': self._get_swatch_internet_time(), '%blockheight%': str(data.get("blockheight", "...")), '%hash%': data.get("hash_full", "...") if cfg.get("display_full_hash") else data.get("hash_short", "..."), '%glyph%': self._generate_glyph(cfg.get("glyph_seed", "")) if cfg.get("generate_glyphs") else "", '%veritas%': f"Veritas {VERITAS_PROTOCOL_VERSION}", '%seal%': seal_id, '%protocol_status%': "Bridge", '%ots%': self.app.lang.get("ots_pending") if self.config.get("ots_enabled") else "", '%opreturn%': self.app.lang.get("opreturn_ready") if self.config.get("opreturn_enabled") else ""}
        return '\n'.join([self._render_line(cfg.get(f"prompt_line_{i}", ""), now, replacements) for i in range(1, 4) if cfg.get(f"line_{i}_enabled")])

    def _generate_seal_id(self, data: Dict, now: datetime.datetime = None) -> str:
        """Generate a deterministic Veritas Seal ID from block data + glyph.
        
        Changed in v21.4: Seal is now deterministic (no datetime dependency).
        Same block + same glyph = same Seal ID (reproducible verification).
        Ref: THERMODYNAMIC_ALIGNMENT_PAPER_v10_3 §4.1 Epistemic Mass
        """
        glyph = self._generate_glyph(self.config.config.get("glyph_seed", ""))
        tag = self.config.config.get("veritas_epistemic_tag", "")
        if ve:
            return ve.generate_deterministic_seal_id(
                data.get('blockheight', ''),
                data.get('hash_full', ''),
                glyph, tag
            )
        # Fallback without veritas_engine
        raw = f"{data.get('blockheight', '')}:{data.get('hash_full', '')}:{glyph}:{tag}"
        return f"0x{hashlib.sha256(raw.encode()).hexdigest()[:16]}"

    def _render_line(self, template: str, now: datetime.datetime, replacements: Dict) -> str:
        parts = self.special_placeholder_regex.split(template)
        final_string = ""
        for i, part in enumerate(parts):
            if i % 2 == 1:
                final_string += part[1:-1] if part.startswith("'") and part.endswith("'") else replacements.get(part, part)
            else:
                final_string += self._format_datetime_in_string(part, now)
        return final_string

    def _format_datetime_in_string(self, text: str, now: datetime.datetime) -> str:
        parts = self.dt_format_regex.split(text)
        result = ""
        for i, part in enumerate(parts):
            if i % 2 == 1:
                if isinstance(code_map := self.FORMAT_CODE_MAP.get(part), list):
                    result += code_map[now.month - 1 if 'M' in part else now.weekday()]
                elif callable(code_map):
                    result += code_map(now)
                elif code_map:
                    result += now.strftime(code_map)
                else:
                    result += part
            else:
                result += part
        return result

    def _generate_glyph(self, seed: str) -> str:
        if not (norm := unicodedata.normalize('NFKD', seed).encode('ascii', 'ignore').decode('ascii')):
            return "........"
        sha = hashlib.sha256(norm.encode()).hexdigest()[:8]
        return "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(sha))

class WidgetWindow:
    """Główne okno widgeta, odpowiedzialne za wyświetlanie tekstu i interakcje."""
    def __init__(self, ui_manager: "UIManager"):
        self.ui = ui_manager
        self.app = ui_manager.app
        self.master = ui_manager.app.master
        self.config = ui_manager.app.config_manager
        self.lang = ui_manager.app.lang
        self.last_click_pos = (0, 0)
        self._tk_font: Optional[tkfont.Font] = None
        self._current_text: str = ""
        self.canvas: Optional[tk.Canvas] = None
        self._tooltip_win: Optional[tk.Toplevel] = None
        self._tooltip_after_id: Optional[str] = None
        self._pulse_phase: float = 0.0
        self._pulse_dir: float = 1.0
        self._pulse_after_id: Optional[str] = None

    def setup(self) -> None:
        self.master.overrideredirect(True)
        self.master.attributes('-topmost', self.config.get("always_on_top"))
        self.master.config(bg='#f0f0f0')
        self.master.wm_attributes('-transparentcolor', '#f0f0f0')
        self.canvas = tk.Canvas(self.master, bg='#f0f0f0', highlightthickness=0)
        self.canvas.pack()
        self._update_font()
        self._bind_events()
        self.master.geometry(self.config.get("last_position", "+100+100"))
        self._pulse_loop()
        
        try:
            self.master.drop_target_register(DND_FILES)
            self.master.dnd_bind('<<Drop>>', lambda e: self.app.capture_manager.stamp_file(e.data))
        except Exception as e:
            logging.warning(f"Drag and drop not fully supported: {e}")

    def _update_font(self, font_config: Optional[Dict] = None) -> None:
        cfg = font_config or self.config.config
        self._tk_font = tkfont.Font(family=cfg.get('font_family'), size=cfg.get('base_font_size'), weight=cfg.get('font_weight'), slant=cfg.get('font_slant'))

    def _bind_events(self) -> None:
        if self.canvas:
            self.canvas.tag_bind("drag_handle", "<ButtonPress-1>", self._on_drag_start)
            self.canvas.tag_bind("drag_handle", "<B1-Motion>", self._on_drag_motion)
            self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
            self.canvas.bind("<B1-Motion>", self._on_drag_motion)
            self.canvas.bind("<Button-3>", self._show_context_menu)
            self.canvas.bind("<Enter>", self._schedule_tooltip)
            self.canvas.bind("<Leave>", self._on_leave)
            self.canvas.bind("<Motion>", self._on_hologram_tilt)

    def update_display(self, text: str, is_inverted: bool, config_override: Optional[Dict] = None) -> None:
        if not self.master.winfo_exists() or not self.canvas or not self._tk_font:
            return
        self._current_text = text
        cfg = {**self.config.config, **(config_override or {})}
        self._update_font(cfg)
        self.canvas.delete("all")
        
        text_color, outline_color = (cfg.get("outline_color"), cfg.get("text_color")) if cfg.get("auto_color_inversion") and is_inverted else (cfg.get("text_color"), cfg.get("outline_color"))
        thickness = cfg.get("outline_thickness", 1)
        lines = text.split('\n')
        line_height = self._tk_font.metrics("linespace")
        padding = 5
        canvas_width = max((self._tk_font.measure(line) for line in lines), default=0) + 2 * padding
        canvas_height = line_height * len(lines) + 2 * padding
        
        self.canvas.create_rectangle(0, 0, 80, line_height + 2 * padding, tags="drag_handle", fill="", outline="")
        y_pos = padding
        for i, line in enumerate(lines):
            align = cfg.get(f"line_{i+1}_align", "left")
            anchor = {"left": "nw", "center": "n", "right": "ne"}.get(align, "nw")
            x_pos = padding if align == "left" else canvas_width / 2 if align == "center" else canvas_width - padding
            
            if cfg.get("use_outline") and thickness > 0:
                if cfg.get("shadow_style") == "3d_offset":
                    direction = cfg.get("shadow_direction", "down-right")
                    ox, oy = (thickness, thickness) if direction == "down-right" else (-thickness, thickness) if direction == "down-left" else (thickness, -thickness) if direction == "up-right" else (-thickness, -thickness)
                    self.canvas.create_text(x_pos + ox, y_pos + oy, text=line, font=self._tk_font, fill=outline_color, anchor=anchor, tags=("parallax_shadow",))
                else:
                    for dx, dy in [(dx, dy) for dx in range(-thickness, thickness + 1) for dy in range(-thickness, thickness + 1) if dx or dy]:
                        self.canvas.create_text(x_pos + dx, y_pos + dy, text=line, font=self._tk_font, fill=outline_color, anchor=anchor, tags=("parallax_shadow",))
            self.canvas.create_text(x_pos, y_pos, text=line, font=self._tk_font, fill=text_color, anchor=anchor, tags=("parallax_text",))
            y_pos += line_height
        # --- ECM & Veritas Status Indicator Bar ---
        data = self.app.data_manager.get_data_snapshot()
        has_data = isinstance(data.get("blockheight"), int)
        bar_color = cfg.get("status_bar_color_ok", VERITAS_COLORS["gold"]) if has_data else cfg.get("status_bar_color_err", VERITAS_COLORS["red_alert"])
        
        ecm_val = self._calculate_ecm()
        ecm_text = f"ECM: {ecm_val}%"
        ecm_font = ('Consolas', 8, 'bold')
        self._tk_font_ecm = tkfont.Font(family='Consolas', size=8, weight='bold')
        ecm_width = self._tk_font_ecm.measure(ecm_text)
        
        if ecm_val >= 85: ecm_color = VERITAS_COLORS["cyan"] 
        elif ecm_val >= 50: ecm_color = VERITAS_COLORS["gold"]
        else: ecm_color = VERITAS_COLORS["red_alert"]

        bar_height = 2
        ecm_height = 14
        canvas_width = max(canvas_width, ecm_width + 30)
        canvas_height_with_bar = canvas_height + ecm_height + bar_height
        
        # Tekst i cień ECM
        self.canvas.create_text(canvas_width - padding, canvas_height + 1, text=ecm_text, font=ecm_font, fill=outline_color, anchor="ne", tags="parallax_shadow")
        self.canvas.create_text(canvas_width - padding, canvas_height + 1, text=ecm_text, font=ecm_font, fill=text_color, anchor="ne", tags="ecm_text")
        # Dioda (kropka)
        self.canvas.create_text(canvas_width - padding - ecm_width - 8, canvas_height + 1, text="●", font=ecm_font, fill=outline_color, anchor="ne", tags="parallax_shadow")
        self.canvas.create_text(canvas_width - padding - ecm_width - 8, canvas_height + 1, text="●", font=ecm_font, fill=ecm_color, anchor="ne", tags="ecm_dot")

        # Pasek statusu u dołu
        self.canvas.create_rectangle(0, canvas_height + ecm_height, canvas_width, canvas_height_with_bar, fill=bar_color, outline=bar_color, tags="status_bar")
        
        
        self.canvas.config(width=canvas_width, height=canvas_height_with_bar)
        try:
            _, x, y = self.master.geometry().split('+')
            self.master.geometry(f"{int(canvas_width)}x{int(canvas_height_with_bar)}+{x}+{y}")
        except (IndexError, ValueError, tk.TclError):
            self.master.geometry(f"{int(canvas_width)}x{int(canvas_height_with_bar)}+100+100")
            
        # Wyzeruj bazowe wpisy po przebudowaniu
        self._original_coords = {}

    def _calculate_ecm(self) -> int:
        """Epistemic Confidence Meter — delegated to veritas_engine."""
        data = self.app.data_manager.get_data_snapshot()
        has_data = isinstance(data.get("blockheight"), int)
        if ve:
            return ve.compute_ecm_confidence(
                has_data=has_data,
                use_custom_node=self.config.get("use_custom_node", False),
                ots_enabled=self.config.get("ots_enabled", False),
                opreturn_enabled=self.config.get("opreturn_enabled", False),
            )
        # Fallback
        if not has_data:
            return 0
        score = 50
        if self.config.get("use_custom_node"): score += 20
        if self.config.get("ots_enabled"): score += 15
        if self.config.get("opreturn_enabled"): score += 15
        return score

    def _pulse_loop(self) -> None:
        if not self.master.winfo_exists() or not self.canvas:
            return

        data = self.app.data_manager.get_data_snapshot()
        has_data = isinstance(data.get("blockheight"), int)
        
        cfg = self.config.config
        base_color = cfg.get("status_bar_color_ok", VERITAS_COLORS["gold"]) if has_data else cfg.get("status_bar_color_err", VERITAS_COLORS["red_alert"])

        if has_data:
            last_time = data.get("last_block_time_local", time.time())
            time_since_last = time.time() - last_time
            # Pulse cycle duration: starts at 4s, goes down to 0.8s near 10 mins (600s)
            cycle_duration = max(0.8, 4.0 - 3.2 * (time_since_last / 600.0))
        else:
            # Offline: sleep mode, very slow pulse
            cycle_duration = 5.0

        # Update phase
        # 50ms interval = 0.05s
        step = 0.05 / (cycle_duration / 2.0)
        self._pulse_phase += self._pulse_dir * step
        if self._pulse_phase >= 1.0:
            self._pulse_phase = 1.0
            self._pulse_dir = -1.0
        elif self._pulse_phase <= 0.0:
            self._pulse_phase = 0.0
            self._pulse_dir = 1.0

        # Calculate color
        hx = base_color.lstrip('#')
        # Some colors might be simple names, but config defaults are #HEX
        try:
            if len(hx) == 6:
                r, g, b = tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))
            else:
                r, g, b = 245, 166, 35 # default gold
        except ValueError:
            r, g, b = 245, 166, 35 # fallback

        darken_factor = 0.6 if has_data else 0.8
        r = int(r * (1.0 - self._pulse_phase * darken_factor))
        g = int(g * (1.0 - self._pulse_phase * darken_factor))
        b = int(b * (1.0 - self._pulse_phase * darken_factor))
        pulsed_color = f"#{r:02X}{g:02X}{b:02X}"
        
        ecm_val = self._calculate_ecm()
        ecm_color_key = ve.ecm_color_key(ecm_val) if ve else ("cyan" if ecm_val >= 85 else "gold" if ecm_val >= 50 else "red_alert")
        ecm_base = VERITAS_COLORS[ecm_color_key]
        # B3-FIX: renamed from re,ge,be to r_ecm,g_ecm,b_ecm to avoid shadowing the `re` module
        r_ecm, g_ecm, b_ecm = ve.parse_hex_color(ecm_base) if ve else (245, 166, 35)
        if not ve:
            hx_e = ecm_base.lstrip('#')
            try: r_ecm, g_ecm, b_ecm = tuple(int(hx_e[i:i+2], 16) for i in (0, 2, 4))
            except ValueError: pass
        pulsed_ecm = ve.darken_color(r_ecm, g_ecm, b_ecm, self._pulse_phase, darken_factor) if ve else f"#{int(r_ecm*(1.0-self._pulse_phase*darken_factor)):02X}{int(g_ecm*(1.0-self._pulse_phase*darken_factor)):02X}{int(b_ecm*(1.0-self._pulse_phase*darken_factor)):02X}"
        
        if self.canvas.find_withtag("status_bar"):
            self.canvas.itemconfig("status_bar", fill=pulsed_color, outline=pulsed_color)
        if self.canvas.find_withtag("ecm_dot"):
            self.canvas.itemconfig("ecm_dot", fill=pulsed_ecm)
            
        self._pulse_after_id = self.master.after(50, self._pulse_loop)

    def _on_leave(self, event: tk.Event) -> None:
        self._hide_tooltip(event)
        self._reset_parallax()

    def _reset_parallax(self) -> None:
        if not self.canvas: return
        try:
            for item in self.canvas.find_withtag("parallax_text"):
                self.canvas.coords(item, self._original_coords[item])
            for item in self.canvas.find_withtag("parallax_shadow"):
                self.canvas.coords(item, self._original_coords[item])
        except (AttributeError, KeyError):
            pass

    def _on_hologram_tilt(self, event: tk.Event) -> None:
        if not self.canvas: return
        w = self.master.winfo_width()
        h = self.master.winfo_height()
        if w == 0 or h == 0: return

        # Zachowaj bazowe koordynaty przy pierwszym ticku
        if not hasattr(self, '_original_coords'):
            self._original_coords = {}
            for item in self.canvas.find_withtag("parallax_text") + self.canvas.find_withtag("parallax_shadow"):
                self._original_coords[item] = self.canvas.coords(item)

        cx, cy = w / 2, h / 2
        # Odległość kursora od środka (od -1.0 do 1.0)
        dx = (event.x - cx) / cx
        dy = (event.y - cy) / cy

        # Maksymalne przesunięcie w pikselach
        max_tilt_shadow = 3.0
        max_tilt_text = 1.0

        for item in self.canvas.find_withtag("parallax_shadow"):
            orig = self._original_coords.get(item)
            if orig:
                self.canvas.coords(item, orig[0] - (dx * max_tilt_shadow), orig[1] - (dy * max_tilt_shadow))
        
        for item in self.canvas.find_withtag("parallax_text"):
            orig = self._original_coords.get(item)
            if orig:
                self.canvas.coords(item, orig[0] + (dx * max_tilt_text), orig[1] + (dy * max_tilt_text))

    def _show_context_menu(self, event: tk.Event) -> None:
        popup = tk.Menu(self.master, tearoff=0)
        popup.add_command(label=self.lang.get("ctx_copy"), command=self._copy_text, state="normal" if _OPTIONAL_DEPENDENCIES['pyperclip'] else "disabled")
        popup.add_separator()
        popup.add_command(label=self.lang.get("ctx_quick_png"), command=lambda: self.app.capture_manager.capture_screenshot())
        popup.add_command(label=self.lang.get("ctx_quick_gif"), command=lambda: self.app.capture_manager.capture_gif())
        popup.add_command(label=(self.lang.get("ctx_stamp_file") or "Ostempluj plik z dysku..."), command=self._select_and_stamp_file)
        popup.add_command(label="Generuj sam ładunek OP_RETURN...", command=self._standalone_opreturn_dialog)
        popup.add_command(label="Ustawienia stempla PDF...", command=self._pdf_settings_dialog)
        popup.add_separator()
        popup.add_command(label=self.lang.get("ctx_veritas_seal"), command=self._show_veritas_seal)
        popup.add_command(label=self.lang.get("ctx_pyblock"), command=self.ui.launch_pyblock)
        popup.add_command(label=self.lang.get("ctx_settings"), command=self.ui.show_settings)
        popup.add_command(label=self.lang.get("ctx_stamp"), command=self._save_stamp)
        popup.add_separator()
        popup.add_command(label=self.lang.get("ctx_close"), command=self.app.close_app)
        popup.tk_popup(event.x_root, event.y_root)

    def _select_and_stamp_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Wybierz plik do ostemplowania",
            filetypes=[("Obsługiwane pliki", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.mp4;*.pdf"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            self.app.capture_manager.stamp_file(file_path)

    def _standalone_opreturn_dialog(self) -> None:
        # S4-FIX: guard pyperclip import behind dependency check
        if not _OPTIONAL_DEPENDENCIES.get('pyperclip'):
            messagebox.showwarning("Missing Dependency", "pyperclip is required for this feature.")
            return
        import pyperclip  # Safe: guarded by dependency check above
        
        dlg = tk.Toplevel(self.master)
        dlg.title("Standalone OP_RETURN Payload")
        dlg.geometry("450x220")
        dlg.attributes("-topmost", True)
        dlg.configure(bg="#1A2332")
        
        tk.Label(dlg, text="Wiadomość OP_RETURN:", bg="#1A2332", fg="white", font=("Segoe UI", 10)).pack(pady=(10, 2))
        msg_var = tk.StringVar(value="[Własna wiadomość Veritas]")
        tk.Entry(dlg, textvariable=msg_var, width=50, font=("Consolas", 10)).pack(pady=2)
        
        tk.Label(dlg, text="Maksymalny limit bajtów (np. 80, 83, 100):", bg="#1A2332", fg="white", font=("Segoe UI", 10)).pack(pady=(10, 2))
        limit_var = tk.IntVar(value=self.config.get("opreturn_max_bytes", 83))
        tk.Entry(dlg, textvariable=limit_var, width=10, font=("Consolas", 10), justify="center").pack(pady=2)
        
        def _generate():
            limit = limit_var.get()
            self.config.set("opreturn_max_bytes", limit)
            msg = msg_var.get()
            
            # Wymuś obcięcie do zadeklarowanego limitu bajtów (przez weryfikację długości binarnej)
            payload_bytes = msg.encode('utf-8')[:limit]
            payload_decoded = payload_bytes.decode('utf-8', errors='ignore')
            
            res = self.app.capture_manager.generate_opreturn_psbt(payload_decoded)
            psbt = res.get("psbt_b64", "")
            if psbt:
                pyperclip.copy(psbt)
                messagebox.showinfo("OP_RETURN Ready", f"Wygenerowano Czysty Payload:\n{payload_decoded}\nRozmiar: {len(payload_bytes)} bajtów\nZadeklarowany Limit: {limit}\n\nSUKCES: Kod transpondera PSBT został bezpiecznie skopiowany do układu schowka. Możesz wkleić go w Sparrow Wallet.")
                dlg.destroy()
                self.flash("cyan")
                
        tk.Button(dlg, text="Generuj Raw PSBT", command=_generate, bg="#00D4FF", fg="#1A2332", font=("Segoe UI", 9, "bold"), cursor="hand2").pack(pady=15)

    def _pdf_settings_dialog(self) -> None:
        import tkinter as tk
        from tkinter import messagebox, colorchooser
        
        dlg = tk.Toplevel(self.master)
        dlg.title("Ustawienia stempla PDF")
        dlg.geometry("320x280")
        dlg.attributes("-topmost", True)
        dlg.configure(bg="#1A2332")
        
        tk.Label(dlg, text="Rozmiar czcionki (np. 10):", bg="#1A2332", fg="white", font=("Segoe UI", 10)).pack(pady=(15, 2))
        size_var = tk.IntVar(value=self.config.get("pdf_font_size", 10))
        tk.Entry(dlg, textvariable=size_var, justify="center", font=("Consolas", 11)).pack(pady=5)
        
        tk.Label(dlg, text="Kolor czcionki (HEX):", bg="#1A2332", fg="white", font=("Segoe UI", 10)).pack(pady=(10, 2))
        color_var = tk.StringVar(value=self.config.get("pdf_font_color", "#F2A900"))
        color_entry = tk.Entry(dlg, textvariable=color_var, justify="center", font=("Consolas", 11))
        color_entry.pack(pady=5)
        
        def _pick_color():
            c = colorchooser.askcolor(title="Wybierz kolor znaku PDF", color=color_var.get())[1]
            if c:
                color_var.set(c)
                color_entry.config(fg=c)
                
        tk.Button(dlg, text="Wybierz z palety", command=_pick_color, bg="#334055", fg="white").pack(pady=5)
        
        def _save():
            try:
                self.config.set("pdf_font_size", size_var.get())
                self.config.set("pdf_font_color", color_var.get())
                messagebox.showinfo("Zapisano", "Ustawienia stemplowania PDF zostały zaktualizowane! Następny upuszczony PDF użyje nowej czcionki i koloru.")
                dlg.destroy()
                self.flash("green")
            except Exception as e:
                messagebox.showerror("Błąd", str(e))
            
        tk.Button(dlg, text="Zapisz parametry", command=_save, bg="#00D4FF", fg="#1A2332", font=("Segoe UI", 9, "bold"), cursor="hand2").pack(pady=15)

    def get_current_text(self) -> str:
        return self._current_text

    def _copy_text(self) -> None:
        if _OPTIONAL_DEPENDENCIES['pyperclip'] and (text := self.get_current_text()):
            pyperclip.copy(text)
            self.flash("blue")

    def _on_drag_start(self, event: tk.Event) -> None:
        if not self.config.get("lock_position"):
            self.last_click_pos = (event.x, event.y)

    def _on_drag_motion(self, event: tk.Event) -> None:
        if not self.config.get("lock_position"):
            x, y = event.x_root - self.last_click_pos[0], event.y_root - self.last_click_pos[1]
            self.master.geometry(f"+{x}+{y}")

    def flash(self, color: str, duration_ms: int = 200) -> None:
        if self.master.winfo_exists() and self.canvas:
            self.canvas.config(bg=color)
            self.master.after(duration_ms, lambda: self.canvas and self.canvas.config(bg='#f0f0f0'))

    def get_geometry(self) -> Tuple[int, int, int, int]:
        self.master.update_idletasks()
        return self.master.winfo_x(), self.master.winfo_y(), self.master.winfo_width(), self.master.winfo_height()

    def _save_stamp(self):
        data = self.app.data_manager.get_data_snapshot()
        content = (f"Timechain Stamp v{self.config.get('version')}\nTimestamp: {datetime.datetime.now().isoformat()}\nBlock: {data.get('blockheight', 'N/A')}\nHash: {data.get('hash_full', 'N/A')}\n")
        if file_path := filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")], initialfile=f"stamp_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt"):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.flash("green")

    def _schedule_tooltip(self, event: tk.Event) -> None:
        self._hide_tooltip()
        self._tooltip_after_id = self.master.after(800, lambda: self._show_tooltip(event))

    def _show_tooltip(self, event: tk.Event) -> None:
        if self._tooltip_win:
            return
        data = self.app.data_manager.get_data_snapshot()
        block = data.get('blockheight', '...')
        has_data = isinstance(block, int)
        status = "Bridge" if has_data else "Offline"
        tip_text = f"Block: {block} | Veritas: {status}"
        self._tooltip_win = tw = tk.Toplevel(self.master)
        tw.wm_overrideredirect(True)
        tw.wm_attributes('-topmost', True)
        tw.configure(bg=VERITAS_COLORS['deep_blue'])
        lbl = tk.Label(tw, text=tip_text, bg=VERITAS_COLORS['deep_blue'], fg=VERITAS_COLORS['gold'],
                       font=('Segoe UI', 9), padx=8, pady=4)
        lbl.pack()
        x = self.master.winfo_rootx() + 10
        y = self.master.winfo_rooty() + self.master.winfo_height() + 5
        tw.wm_geometry(f"+{x}+{y}")
        self.master.after(2500, self._hide_tooltip)

    def _hide_tooltip(self, event=None) -> None:
        if self._tooltip_after_id:
            self.master.after_cancel(self._tooltip_after_id)
            self._tooltip_after_id = None
        if self._tooltip_win:
            self._tooltip_win.destroy()
            self._tooltip_win = None

    def _show_veritas_seal(self) -> None:
        self._hide_tooltip()  # Kill any active tooltip
        data = self.app.data_manager.get_data_snapshot()
        now = datetime.datetime.now()
        seal_id = self.app.template_engine._generate_seal_id(data, now)
        glyph = self.app.template_engine._generate_glyph(self.config.get("glyph_seed", ""))

        dlg = tk.Toplevel(self.master)
        dlg.overrideredirect(True)  # Bypass Windows DPI scaling
        dlg.configure(bg=VERITAS_COLORS['deep_blue'])
        dlg.attributes('-topmost', True)

        # --- Custom title bar (drag handle + close) ---
        _drag = {'x': 0, 'y': 0}
        title_bar = tk.Frame(dlg, bg='#0D1B2A', height=28, cursor='fleur')
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text=f"🔱 {self.lang.get('veritas_seal_dialog_title')}",
                 bg='#0D1B2A', fg='#8899AA', font=('Segoe UI', 9), anchor='w').pack(side='left', padx=8)
        close_btn = tk.Label(title_bar, text='✕', bg='#0D1B2A', fg='#8899AA',
                             font=('Segoe UI', 11), cursor='hand2', padx=8)
        close_btn.pack(side='right')
        close_btn.bind('<Enter>', lambda e: close_btn.config(fg='#FF5555'))
        close_btn.bind('<Leave>', lambda e: close_btn.config(fg='#8899AA'))
        close_btn.bind('<Button-1>', lambda e: dlg.destroy())
        def _start_drag(e): _drag['x'], _drag['y'] = e.x, e.y
        def _do_drag(e): dlg.geometry(f"+{e.x_root - _drag['x']}+{e.y_root - _drag['y']}")
        title_bar.bind('<ButtonPress-1>', _start_drag)
        title_bar.bind('<B1-Motion>', _do_drag)

        # --- Content ---
        body = tk.Frame(dlg, bg=VERITAS_COLORS['deep_blue'])
        body.pack(fill='both', expand=True)

        # Header
        tk.Label(body, text=f"🔱 Veritas Seal {VERITAS_PROTOCOL_VERSION}", font=('Segoe UI', 14, 'bold'),
                 bg=VERITAS_COLORS['deep_blue'], fg=VERITAS_COLORS['gold']).pack(pady=(10, 3), padx=20)
        tk.Label(body, text=self.lang.get("veritas_philosophy_quote"), font=('Segoe UI', 8, 'italic'),
                 bg=VERITAS_COLORS['deep_blue'], fg='#8899AA').pack(pady=(0, 8))

        # Data rows
        info_frame = tk.Frame(body, bg=VERITAS_COLORS['deep_blue'])
        info_frame.pack(padx=20, pady=5, fill='x')
        full_hash = data.get('hash_full', 'N/A')
        short_hash = full_hash[:16] + '...' if len(full_hash) > 16 else full_hash
        show_full = [self.config.get("display_full_hash", False)]
        ecm_val = self._calculate_ecm()
        rows = [
            ("Block Height:", str(data.get('blockheight', 'N/A'))),
            ("Block Hash:", None),  # handled separately
            ("Timestamp:", now.isoformat()),
            ("Seal ID:", seal_id),
            ("Glyph:", glyph),
            ("Epistemic Conf.:", f"{ecm_val}%"),
            ("Protocol Status:", "Bridge Mode"),
        ]
        hash_lbl = None
        for i, (label, value) in enumerate(rows):
            tk.Label(info_frame, text=label, font=('Segoe UI', 9, 'bold'), anchor='w',
                     bg=VERITAS_COLORS['deep_blue'], fg='#8899AA').grid(row=i, column=0, sticky='w', pady=1)
            if value is None:
                # Block Hash — clickable toggle
                hash_lbl = tk.Label(info_frame, text=full_hash if show_full[0] else short_hash,
                                    font=('Consolas', 7 if show_full[0] else 9), anchor='w',
                                    bg=VERITAS_COLORS['deep_blue'], fg='#E0E0E0', cursor='hand2')
                hash_lbl.grid(row=i, column=1, sticky='w', padx=(10, 0), pady=1)
                def _toggle_hash(e, lbl=hash_lbl):
                    show_full[0] = not show_full[0]
                    lbl.config(text=full_hash if show_full[0] else short_hash,
                               font=('Consolas', 7 if show_full[0] else 9))
                    dlg.update_idletasks()
                    w, h = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
                    dlg.geometry(f"{w}x{h}")
                hash_lbl.bind('<Button-1>', _toggle_hash)
            else:
                tk.Label(info_frame, text=value, font=('Consolas', 9), anchor='w',
                         bg=VERITAS_COLORS['deep_blue'], fg='#E0E0E0').grid(row=i, column=1, sticky='w', padx=(10, 0), pady=1)

        # Copy as JSON button
        def copy_json():
            seal_data = {"veritas_version": VERITAS_PROTOCOL_VERSION, "block_height": data.get('blockheight'), "block_hash": data.get('hash_full', ''), "timestamp": now.isoformat(), "seal_id": seal_id, "glyph": glyph, "ecm_confidence": f"{ecm_val}%", "status": "Bridge"}
            if _OPTIONAL_DEPENDENCIES['pyperclip']:
                pyperclip.copy(json.dumps(seal_data, indent=2))
                self.flash("blue")

        # Copy as OP_RETURN hex button
        def copy_opreturn():
            block_h = str(data.get('blockheight', '0'))
            block_hash = data.get('hash_full', '')[:16]
            ts = now.strftime('%Y%m%d%H%M%S')
            raw = f"veritas:{seal_id}:block:{block_h}:{block_hash}:{ts}"
            hex_data = raw.encode('utf-8').hex()
            # OP_RETURN limit: 80 bytes = 160 hex chars
            hex_data = hex_data[:160]
            if _OPTIONAL_DEPENDENCIES['pyperclip']:
                pyperclip.copy(hex_data)
                self.flash("blue")

        # --- OTS Info Rows ---
        ots_row = len(rows)
        if self.config.get("ots_enabled"):
            tk.Label(info_frame, text=self.lang.get("ots_merkle_root_label"), font=('Segoe UI', 9, 'bold'), anchor='w',
                     bg=VERITAS_COLORS['deep_blue'], fg='#8899AA').grid(row=ots_row, column=0, sticky='w', pady=1)
            merkle = hashlib.sha256(f"{data.get('hash_full','')}{seal_id}".encode()).hexdigest()[:16] + '...'
            tk.Label(info_frame, text=merkle, font=('Consolas', 9), anchor='w',
                     bg=VERITAS_COLORS['deep_blue'], fg='#E0E0E0').grid(row=ots_row, column=1, sticky='w', padx=(10, 0), pady=1)
            tk.Label(info_frame, text=self.lang.get("ots_proof_label"), font=('Segoe UI', 9, 'bold'), anchor='w',
                     bg=VERITAS_COLORS['deep_blue'], fg='#8899AA').grid(row=ots_row+1, column=0, sticky='w', pady=1)
            tk.Label(info_frame, text=self.lang.get("ots_pending"), font=('Consolas', 9), anchor='w',
                     bg=VERITAS_COLORS['deep_blue'], fg=VERITAS_COLORS['gold']).grid(row=ots_row+1, column=1, sticky='w', padx=(10, 0), pady=1)
            ots_row += 2

        # --- OP_RETURN Info Row ---
        if self.config.get("opreturn_enabled"):
            prefix = self.config.get("opreturn_payload_prefix", "VERITAS:")
            merkle_short = hashlib.sha256(f"{data.get('hash_full','')}{seal_id}".encode()).hexdigest()[:16]
            ots_commitment = hashlib.sha256(seal_id.encode()).hexdigest()[:16]
            opreturn_payload = f"{prefix}{seal_id}:{merkle_short}:{ots_commitment}"
            opreturn_payload = opreturn_payload[:self.config.get('opreturn_max_bytes', 83)]

            tk.Label(info_frame, text=self.lang.get("opreturn_payload_label"), font=('Segoe UI', 9, 'bold'), anchor='w',
                     bg=VERITAS_COLORS['deep_blue'], fg='#8899AA').grid(row=ots_row, column=0, sticky='w', pady=1)
            payload_lbl = tk.Label(info_frame, text=opreturn_payload[:40] + '...', font=('Consolas', 8), anchor='w',
                     bg=VERITAS_COLORS['deep_blue'], fg=VERITAS_COLORS['cyan'], cursor='hand2')
            payload_lbl.grid(row=ots_row, column=1, sticky='w', padx=(10, 0), pady=1)
            def _copy_payload(p=opreturn_payload):
                if _OPTIONAL_DEPENDENCIES['pyperclip']:
                    pyperclip.copy(p)
                    self.flash("blue")
            payload_lbl.bind('<Button-1>', lambda e: _copy_payload())

        btn_frame = tk.Frame(body, bg=VERITAS_COLORS['deep_blue'])
        btn_frame.pack(pady=(10, 15))
        tk.Button(btn_frame, text=self.lang.get("veritas_seal_copy_json"), command=copy_json,
                  bg=VERITAS_COLORS['gold'], fg=VERITAS_COLORS['deep_blue'], font=('Segoe UI', 9, 'bold'),
                  relief='flat', padx=15, pady=5, cursor='hand2').pack(side='left', padx=5)
        tk.Button(btn_frame, text=self.lang.get("veritas_copy_opreturn"), command=copy_opreturn,
                  bg=VERITAS_COLORS['cyan'], fg=VERITAS_COLORS['deep_blue'], font=('Segoe UI', 9, 'bold'),
                  relief='flat', padx=15, pady=5, cursor='hand2').pack(side='left', padx=5)

        # OP_RETURN Generate PSBT button
        if self.config.get("opreturn_enabled"):
            def _gen_opreturn_psbt():
                prefix = self.config.get("opreturn_payload_prefix", "VERITAS:")
                merkle_short = hashlib.sha256(f"{data.get('hash_full','')}{seal_id}".encode()).hexdigest()[:16]
                ots_c = hashlib.sha256(seal_id.encode()).hexdigest()[:16]
                payload = f"{prefix}{seal_id}:{merkle_short}:{ots_c}"[:self.config.get("opreturn_max_bytes", 83)]
                result = self.app.capture_manager.generate_opreturn_psbt(payload)
                if result and _OPTIONAL_DEPENDENCIES['pyperclip']:
                    pyperclip.copy(result.get('psbt_b64', ''))
                    self.flash("blue")
                
                # Save to a temp file for Sparrow/Electrum
                temp_psbt_path = os.path.join(tempfile.gettempdir(), f"veritas_anchor_{seal_id[:8]}.psbt")
                try:
                    with open(temp_psbt_path, 'w', encoding='ascii') as f:
                        f.write(result.get('psbt_b64', ''))
                    self.app.data_manager.set_transient("latest_psbt_path", temp_psbt_path)
                except Exception as e:
                    logging.error(f"Cannot write temp PSBT: {e}")

            tk.Button(btn_frame, text=self.lang.get("opreturn_generate_btn"), command=_gen_opreturn_psbt,
                      bg=VERITAS_COLORS['purple'], fg='white', font=('Segoe UI', 9, 'bold'),
                      relief='flat', padx=10, pady=5, cursor='hand2').pack(side='left', padx=5)

            def _open_psbt():
                path = self.app.data_manager.get_transient("latest_psbt_path")
                if not path or not os.path.exists(path):
                    _gen_opreturn_psbt()
                    path = self.app.data_manager.get_transient("latest_psbt_path")
                # S2-FIX: validate path is a .psbt file before os.startfile
                if path and os.path.exists(path) and path.endswith('.psbt') and _is_windows():
                    os.startfile(path)

            tk.Button(btn_frame, text=self.lang.get("opreturn_open_psbt_btn"), command=_open_psbt,
                      bg=VERITAS_COLORS['cyan'], fg=VERITAS_COLORS['deep_blue'], font=('Segoe UI', 9, 'bold'),
                      relief='flat', padx=10, pady=5, cursor='hand2').pack(side='left', padx=5)

            if self.config.get("opreturn_use_bitcoin_core"):
                def _broadcast_psbt():
                    path = self.app.data_manager.get_transient("latest_psbt_path")
                    if not path or not os.path.exists(path):
                        _gen_opreturn_psbt()
                        path = self.app.data_manager.get_transient("latest_psbt_path")
                    if path and os.path.exists(path):
                        with open(path, 'r', encoding='ascii') as f:
                            b64 = f.read().strip()
                        if self.app.capture_manager._broadcast_via_core(b64):
                            self.flash("green")
                        else:
                            self.flash("red")

                tk.Button(btn_frame, text=self.lang.get("opreturn_broadcast_core_btn"), command=_broadcast_psbt,
                          bg=VERITAS_COLORS['gold'], fg=VERITAS_COLORS['deep_blue'], font=('Segoe UI', 9, 'bold'),
                          relief='flat', padx=10, pady=5, cursor='hand2').pack(side='left', padx=5)

        tk.Button(btn_frame, text=self.lang.get("close_button"), command=dlg.destroy,
                  bg='#333333', fg='white', font=('Segoe UI', 9), relief='flat', padx=15, pady=5, cursor='hand2').pack(side='left', padx=5)

        # Position near widget
        dlg.update_idletasks()
        w, h = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
        x = self.master.winfo_rootx() + (self.master.winfo_width() - w) // 2
        y = self.master.winfo_rooty() - h - 10
        dlg.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        dlg.grab_set()
        dlg.focus_force()

class ColorAnalyzer(threading.Thread):
    """Wątek analizujący kolor tła pod widgetem w celu automatycznej inwersji kolorów."""
    def __init__(self, app: "TimechainApp"):
        super().__init__(name="ColorAnalyzer", daemon=True)
        self.app = app
        self.config = app.config_manager
        self.should_invert = threading.Event()
        self._stop_event = threading.Event()
        self._trigger_check_event = threading.Event()
        self.sct = mss.mss() if _OPTIONAL_DEPENDENCIES['mss'] else None

    def run(self) -> None:
        time.sleep(2)
        while not self._stop_event.is_set():
            if self._trigger_check_event.wait(timeout=3600) and self.config.get("auto_color_inversion"):
                if self._stop_event.is_set():
                    break
                self.check_background_brightness()
                self._trigger_check_event.clear()

    def trigger_check(self) -> None:
        if self.is_alive():
            self._trigger_check_event.set()

    def check_background_brightness(self) -> None:
        try:
            x, y, w, h = self.app.ui_manager.get_widget_geometry()
            bbox = {'top': y - 5, 'left': x - 5, 'width': w + 10, 'height': h + 10}
            
            # FIX: Multi-monitor — adjust bbox to correct monitor offset
            if self.sct:
                try:
                    monitors = self.sct.monitors
                    # Find the monitor containing the widget center
                    cx, cy = x + w // 2, y + h // 2
                    for mon in monitors[1:]:  # Skip index 0 (virtual screen)
                        if (mon['left'] <= cx < mon['left'] + mon['width'] and
                            mon['top'] <= cy < mon['top'] + mon['height']):
                            # Clamp bbox within this monitor
                            bbox['left'] = max(bbox['left'], mon['left'])
                            bbox['top'] = max(bbox['top'], mon['top'])
                            bbox['width'] = min(bbox['width'], mon['left'] + mon['width'] - bbox['left'])
                            bbox['height'] = min(bbox['height'], mon['top'] + mon['height'] - bbox['top'])
                            break
                    sct_img = self.sct.grab(bbox)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX").convert("L")
                except Exception:
                    img = ImageGrab.grab(bbox=(bbox['left'], bbox['top'], bbox['left']+bbox['width'], bbox['top']+bbox['height'])).convert("L")
            else:
                img = ImageGrab.grab(bbox=(bbox['left'], bbox['top'], bbox['left']+bbox['width'], bbox['top']+bbox['height'])).convert("L")
            
            avg_brightness = np.mean(np.array(img)) if _OPTIONAL_DEPENDENCIES['numpy'] else sum(img.getdata()) / (img.width * img.height)
            inversion_changed = False
            
            if avg_brightness > self.config.get("brightness_threshold", 128):
                if not self.should_invert.is_set():
                    self.should_invert.set()
                    inversion_changed = True
            elif self.should_invert.is_set():
                self.should_invert.clear()
                inversion_changed = True
            
            if inversion_changed:
                self.app.request_ui_update()
        except Exception as e:
            logging.warning(f"Błąd podczas sprawdzania jasności tła: {e}", exc_info=False)

    def stop(self) -> None:
        self._stop_event.set()
        self._trigger_check_event.set()
        if self.sct:
            self.sct.close()

class RegionSelector:
    def __init__(self, app_master: tk.Tk, callback: Callable[[Tuple[int, int, int, int]], None]):
        self.master, self.callback = app_master, callback
        self.start_x, self.start_y, self.rect = 0, 0, None
        self.window = tk.Toplevel(self.master)
        self.window.attributes("-alpha", 0.1)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        if _OPTIONAL_DEPENDENCIES['screeninfo']:
            monitors = get_monitors()
            self.window.geometry(f"{max(m.x + m.width for m in monitors) - min(m.x for m in monitors)}x{max(m.y + m.height for m in monitors) - min(m.y for m in monitors)}+{min(m.x for m in monitors)}+{min(m.y for m in monitors)}")
        else:
            self.window.geometry(f"{self.master.winfo_screenwidth()}x{self.master.winfo_screenheight()}+0+0")
        self.canvas = tk.Canvas(self.window, cursor="crosshair", bg="black")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def _on_press(self, event: tk.Event):
        self.start_x, self.start_y = event.x_root, event.y_root
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=1, fill=None)

    def _on_drag(self, event: tk.Event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x_root, event.y_root)

    def _on_release(self, event: tk.Event):
        x1, y1, x2, y2 = min(self.start_x, event.x_root), min(self.start_y, event.y_root), max(self.start_x, event.x_root), max(self.start_y, event.y_root)
        self.window.destroy()
        if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
            self.master.after(100, lambda: self.callback(region_bbox=(x1, y1, x2 - x1, y2 - y1)))

class PyBlockLauncher:
    @staticmethod
    def launch(command: str):
        try:
            args = shlex.split(command)
            if _is_windows():
                subprocess.Popen(['start', 'cmd', '/k'] + args, shell=True)
            elif platform.system() == "Darwin":
                subprocess.Popen(['osascript', '-e', f'''tell application "Terminal" to do script "{command}"'''])
            else:
                # FIX: Wayland + Plasma support — added kitty, alacritty, wezterm
                for term in ['gnome-terminal', 'konsole', 'kitty', 'alacritty', 'wezterm', 'xterm', 'lxterminal', 'mate-terminal']:
                    if shutil.which(term):
                        if term in ['gnome-terminal', 'konsole']:
                            subprocess.Popen([term, '--' if term == 'gnome-terminal' else '-e', 'bash', '-c', f'{command}; exec bash'])
                        elif term == 'kitty':
                            subprocess.Popen([term, 'bash', '-c', f'{command}; exec bash'])
                        elif term == 'alacritty':
                            subprocess.Popen([term, '-e', 'bash', '-c', f'{command}; exec bash'])
                        elif term == 'wezterm':
                            subprocess.Popen([term, 'start', '--', 'bash', '-c', f'{command}; exec bash'])
                        else:
                            subprocess.Popen([term, '-e', command])
                        return
                messagebox.showerror("Błąd", "Nie znaleziono obsługiwanego emulatora terminala (Linux/Wayland).")
            logging.info(f"Uruchomiono PyBlock komendą: {command}")
        except Exception as e:
            logging.error(f"Nie udało się uruchomić PyBlock: {e}")
            messagebox.showerror("Błąd Uruchamiania", f"Nie udało się uruchomić komendy:\n{command}\n\nBłąd: {e}")

class CaptureManager:
    """Zarządza przechwytywaniem ekranu, wideo i GIF-ów."""
    def __init__(self, app: "TimechainApp"):
        self.app = app
        self.ui_manager = app.ui_manager
        self.config = app.config_manager
        self._hotkey_listener: Optional[keyboard.GlobalHotKeys] = None
        self.region_selector: Optional[RegionSelector] = None
        self._capture_lock = threading.Lock()

    def start_hotkey_listener(self) -> None:
        if not _OPTIONAL_DEPENDENCIES['pynput']:
            return
        hotkeys = {'<ctrl>+<shift>+1': self.capture_screenshot, '<ctrl>+<shift>+2': self.capture_video, '<ctrl>+<shift>+3': self.capture_gif, '<ctrl>+<alt>+1': lambda: self._start_region_capture(self.capture_screenshot), '<ctrl>+<alt>+2': lambda: self._start_region_capture(self.capture_video), '<ctrl>+<alt>+3': lambda: self._start_region_capture(self.capture_gif)}
        try:
            self._hotkey_listener = keyboard.GlobalHotKeys(hotkeys)
            self._hotkey_listener.start()
            logging.info("Skróty aktywne: Ekran(Ctrl+Shift+1/2/3) | Region(Ctrl+Alt+1/2/3) dla PNG/MP4/GIF.")
        except Exception as e:
            logging.error(f"Nie udało się uruchomić nasłuchu skrótów: {e}")

    def _start_region_capture(self, callback: Callable):
        if self.region_selector and self.region_selector.window.winfo_exists():
            return
        self.region_selector = RegionSelector(self.app.master, callback)

    def stop_hotkey_listener(self) -> None:
        if self._hotkey_listener and self._hotkey_listener.is_alive():
            self._hotkey_listener.stop()

    def _get_capture_filename(self, extension: str) -> str:
        capture_dir = self.config.get("capture_folder")
        os.makedirs(capture_dir, exist_ok=True)
        now = datetime.datetime.now()
        prefix = ""
        if self.config.get("use_capture_filename_prefix"):
            prefix = self.app.template_engine.render(config_override={"prompt_line_1": self.config.get("capture_filename_prefix"), "line_1_enabled": True, "line_2_enabled": False, "line_3_enabled": False})
        return os.path.join(capture_dir, f"{prefix}{now.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.{extension}")

    def _get_capture_bbox(self) -> Optional[Dict[str, int]]:
        if not _OPTIONAL_DEPENDENCIES['mss']:
            return None
        choice = self.config.get("capture_screen")
        if choice == self.app.lang.get("capture_all_screens"):
            with mss.mss() as sct:
                return sct.monitors[0]
        if match := re.search(r'Monitor (\d+)x(\d+) @ \((\-?\d+),(\-?\d+)\)', choice):
            try:
                w, h, x, y = map(int, match.groups())
                return {'left': x, 'top': y, 'width': w, 'height': h}
            except (ValueError, IndexError):
                logging.error(f"Nie udało się sparsować geometrii monitora z: {choice}")
        logging.warning(f"Nie znaleziono dopasowania dla '{choice}', używanie monitora głównego jako domyślnego.")
        if _OPTIONAL_DEPENDENCIES['screeninfo']:
            try:
                for m in get_monitors():
                    if m.is_primary:
                        return {'left': m.x, 'top': m.y, 'width': m.width, 'height': m.height}
            except Exception as e:
                logging.error(f"Błąd przy szukaniu monitora głównego: {e}")
        
        with mss.mss() as sct:
            if len(sct.monitors) > 1:
                return sct.monitors[1]
            return sct.monitors[0]
    
    def _create_rotated_text_stamp(self, text: str, font, angle: float, color: Tuple[int, ...], shadow_config: Dict) -> Image.Image:
        """
        Tworzy przezroczysty obrazek ze stemplowanym tekstem, obrócony o zadany kąt.
        Zachowuje ostrość tekstu i cieni.
        """
        dummy_draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        bbox = dummy_draw.textbbox((0, 0), text, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        # Margines na cień i antyaliasing
        margin = int(max(text_w, text_h) * 0.5)
        canvas_size = (text_w + margin * 2, text_h + margin * 2)
        
        txt_img = Image.new('RGBA', canvas_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_img)
        
        # Rysowanie cienia
        if shadow_config.get('use'):
            sx, sy = (canvas_size[0] // 2 + shadow_config['offset'], canvas_size[1] // 2 + shadow_config['offset'])
            draw.text((sx, sy), text, font=font, fill=shadow_config['color'], anchor="mm")
            
        # Rysowanie tekstu
        draw.text((canvas_size[0] // 2, canvas_size[1] // 2), text, font=font, fill=color, anchor="mm")
        
        # Obrót
        rotated = txt_img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        return rotated.crop(rotated.getbbox())

    def _add_watermark(self, image: Image.Image, arranged_positions: Optional[List[Tuple[float, float]]] = None) -> Image.Image:
        """
        Nakłada znak wodny na obraz.
        Zmieniona logika: 
        - Tiled: Generuje duży canvas i obraca całość (unika pustych rogów).
        - Arranged/Single: Obraca tylko stempel tekstowy, zachowując pozycję punktu zaczepienia.
        """
        base = image.convert("RGBA")
        style = self.config.get("watermark_style")
        opacity = int(2.55 * self.config.get("watermark_opacity"))

        # Obsługa kodu QR
        if style == "qrcode":
            if not _OPTIONAL_DEPENDENCIES['qrcode']:
                logging.error("Styl 'Kod QR' wymaga biblioteki 'qrcode'.")
                return image.convert("RGB")
            
            current_config = self.app.config_manager.config.copy()
            for i in range(1, 4):
                key = f"prompt_line_{i}"
                if key in current_config:
                    current_config[key] = re.sub(r'\s*([|]|\b(ss|s|SSS|SS|S)\b)\s*', '', current_config[key]).strip()
            qr_content = self.app.template_engine.render(config_override=current_config)
            
            size = self.config.get("watermark_qr_code_size")
            # FIX: QR auto-scale support
            if self.config.get("watermark_auto_scale"):
                size = max(50, int(min(base.width, base.height) * 0.15))
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

        # Przygotowanie tekstu
        watermark_text = self.app.ui_manager.widget_window.get_current_text()
        active_lines = [line for i, line in enumerate(watermark_text.split('\n')) if self.config.get(f"watermark_include_line{i+1}") and line.strip()]
        if not active_lines:
            return image.convert("RGB")
        full_text = "\n".join(active_lines)

        # Konfiguracja parametrów (rozmiar, kąt, czcionka)
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

        # Wybór czcionki
        def get_font(size):
            font_names = ["arial.ttf", "Segoe UI.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf"]
            if platform.system() == "Darwin":
                font_names.insert(0, "Helvetica.ttc")
            for name in font_names:
                try: return ImageFont.truetype(name, size)
                except OSError: continue
            return ImageFont.load_default()
        
        font = get_font(font_size)

        # Konfiguracja cienia i koloru
        shadow_config = {'use': self.config.get("watermark_use_shadow"), 'offset': max(1, int(font_size / 20)), 'color': (0,0,0, opacity)}
        try:
            hex_color = self.config.get("outline_color").lstrip('#')
            rgb_shadow = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            shadow_config['color'] = (*rgb_shadow, opacity)
        except (ValueError, TypeError, AttributeError) as e:
            logging.debug(f"Watermark shadow color parse fallback: {e}")
        main_color = (200, 200, 200, opacity)

        # --- LOGIKA RYSOWANIA ---
        
        if style == "tiled":
            # Dla kafelków musimy wygenerować ogromny canvas, obrócić go i przyciąć
            # Obliczamy przekątną, aby nie było pustych rogów po obrocie
            hypotenuse = int((base.width**2 + base.height**2)**0.5)
            canvas_dim = hypotenuse + max(base.width, base.height)  # FIX: increased safety margin for large angles
            
            # Generujemy stempel tekstowy BEZ obrotu (obracamy cały canvas później)
            stamp = self._create_rotated_text_stamp(full_text, font, 0, main_color, shadow_config)
            
            tiled_layer = Image.new('RGBA', (canvas_dim, canvas_dim), (0,0,0,0))
            # Kafelkowanie od środka
            cx, cy = canvas_dim // 2, canvas_dim // 2
            
            # Wylicz ile kafelków w każdą stronę
            steps_x = (canvas_dim // 2) // spacing + 1
            steps_y = (canvas_dim // 2) // spacing + 1
            
            for dx in range(-steps_x, steps_x + 1):
                for dy in range(-steps_y, steps_y + 1):
                    px = cx + dx * spacing - stamp.width // 2
                    py = cy + dy * spacing - stamp.height // 2
                    tiled_layer.paste(stamp, (px, py), stamp)
            
            # Obracamy wielki canvas
            rotated_layer = tiled_layer.rotate(angle, resample=Image.Resampling.BICUBIC)
            
            # Wycinamy środek wielkości oryginalnego obrazu
            left = (rotated_layer.width - base.width) // 2
            top = (rotated_layer.height - base.height) // 2
            base.alpha_composite(rotated_layer, (0, 0), (left, top, left + base.width, top + base.height))

        else:
            # Dla Single/Arranged/Vertical: Obracamy sam stempel, pozycje zostają stałe
            stamp = self._create_rotated_text_stamp(full_text, font, angle if style != "vertical" else 0, main_color, shadow_config)
            
            positions = [] # Lista (x, y) w pikselach
            
            if style == "single":
                # Recalculate font size for single if auto-scale
                if self.config.get("watermark_auto_scale"):
                    bbox = ImageDraw.Draw(Image.new('RGBA', (1,1))).textbbox((0,0), max(active_lines, key=len), font=font)
                    text_width = bbox[2] - bbox[0]
                    if text_width > 0:
                        scale_factor = (base.width * 0.9) / text_width
                        if scale_factor < 1:
                            font = get_font(int(font_size * scale_factor))
                            stamp = self._create_rotated_text_stamp(full_text, font, angle, main_color, shadow_config)
                
                positions.append(((base.width - stamp.width) // 2, (base.height - stamp.height) // 2))
            
            elif style == "vertical":
                count = self.config.get("watermark_arranged_count", 5)
                total_h = count * stamp.height + (count - 1) * (stamp.height * 0.5)
                start_y = (base.height - total_h) / 2
                center_x = (base.width - stamp.width) / 2
                for i in range(count):
                    positions.append((center_x, int(start_y + i * (stamp.height * 1.5))))

            elif style == "arranged":
                # Używamy znormalizowanych pozycji (0.0-1.0), jeśli przekazano, lub generujemy
                grid_map = {1: [4], 3: [0, 4, 8], 5: [0, 2, 4, 6, 8], 7: [0, 2, 3, 4, 5, 6, 8]}
                indices = grid_map.get(self.config.get("watermark_arranged_count", 5), [4])
                
                cell_w, cell_h = base.width / 3, base.height / 3
                for i in indices:
                    row, col = divmod(i, 3)
                    # Centrum komórki
                    cx = (col + 0.5) * cell_w
                    cy = (row + 0.5) * cell_h
                    # Pozycja lewego górnego rogu stempla
                    positions.append((int(cx - stamp.width / 2), int(cy - stamp.height / 2)))
            
            # Wklejanie stempli
            for x, y in positions:
                base.paste(stamp, (int(x), int(y)), stamp)

        return base.convert("RGB")

    def _submit_capture_task(self, task_func: Callable, *args) -> None:
        def task_wrapper():
            if not self._capture_lock.acquire(blocking=False):
                logging.warning("Przechwytywanie jest już w toku.")
                return
            should_hide = self.config.get("hide_widget_on_capture") and (not args or not args[0])
            try:
                if should_hide:
                    self.app.master.after(0, self.app.master.withdraw)
                    time.sleep(0.3)
                task_func(*args)
            finally:
                if should_hide:
                    self.app.master.after(200, self.app.master.deiconify)
                self._capture_lock.release()
        self.app.executor.submit(task_wrapper)

    def capture_screenshot(self, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> None:
        self._submit_capture_task(self._screenshot_worker, region_bbox)
    
    def capture_video(self, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> None:
        if not all(_OPTIONAL_DEPENDENCIES[k] for k in ['cv2', 'numpy', 'mss']):
            messagebox.showerror(self.app.lang.get("error_missing_deps_title"), self.app.lang.get("error_missing_video_deps"))
            return
        self._submit_capture_task(self._video_worker, region_bbox)
    
    def capture_gif(self, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> None:
        if not _OPTIONAL_DEPENDENCIES['mss']:
            messagebox.showerror(self.app.lang.get("error_missing_deps_title"), self.app.lang.get("error_missing_gif_deps"))
            return
        self._submit_capture_task(self._gif_worker, region_bbox)

    def stamp_file(self, dropped_path: str):
        self._submit_capture_task(self._stamp_file_routing, dropped_path)

    def _stamp_file_routing(self, dropped_path: str):
        try:
            import os
            path = dropped_path.strip('{}\'"')
            path = os.path.normpath(path)

            if not os.path.exists(path):
                logging.error(f"Nieprawidlowy plik/folder: {path}")
                return

            if os.path.isdir(path):
                images = []
                pdfs = []
                valid_img_exts = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']
                for root, _, files in os.walk(path):
                    for f in files:
                        ext = os.path.splitext(f)[1].lower()
                        full_path = os.path.join(root, f)
                        if ext in valid_img_exts: images.append(full_path)
                        elif ext == '.pdf': pdfs.append(full_path)
                if not images and not pdfs:
                    self.app.master.after(0, lambda: messagebox.showwarning("Pusty folder", "Brak wspieranych plików w folderze."))
                    return
                self.app.master.after(0, lambda: self._confirm_batch_directory(pdfs, images))
                return

            ext = os.path.splitext(path)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
                self._stamp_image(path)
            elif ext == '.pdf':
                self.app.master.after(0, lambda p=[path]: self.app.ui_manager.show_pdf_seal_configurator(p, []))
            else:
                self.app.master.after(0, lambda: messagebox.showwarning("Nieobsugiwany format", f"Otrzymano: {ext}"))
                return

        except Exception as e:
            logging.error(f"Blad routingu pliku: {e}")

    def _confirm_batch_directory(self, pdfs: list, images: list):
        total = len(pdfs) + len(images)
        title = self.app.lang.get("batch_seal_title_dlg")
        msg_text = self.app.lang.get("batch_seal_msg_dlg", total=total, img_count=len(images), pdf_count=len(pdfs))
        if messagebox.askyesno(title, msg_text):
            if pdfs:
                self.app.ui_manager.show_pdf_seal_configurator(pdfs, images)
            else:
                self._submit_capture_task(self._stamp_batch_mixed, [], images, "bottom-center")


    def _stamp_batch_mixed(self, pdfs: list, images: list, preset: str):
        total = len(pdfs) + len(images)
        if total == 0: return
        self.app.master.after(0, lambda: self.app.ui_manager.progress_manager.show(f"Batch Seal Factory ({total} plików)", total))
        
        current = 0
        for img_path in images:
            self._stamp_image(img_path, batch_mode=True)
            current += 1
            if current % 5 == 0 or total < 20:
                self.app.master.after(0, lambda c=current, t=total: self.app.ui_manager.progress_manager.update(c, f"Znakowanie zdjęć: {c}/{t}"))

        for pdf_path in pdfs:
            self._stamp_pdf(pdf_path, preset, batch_mode=True)
            current += 1
            self.app.master.after(0, lambda c=current, t=total: self.app.ui_manager.progress_manager.update(c, f"Znakowanie PDF: {os.path.basename(pdf_path)}"))
        
        self.app.master.after(0, lambda: self.app.ui_manager.progress_manager.close())
        self.app.master.after(0, lambda: messagebox.showinfo("Batch Seal Completed", f"Pomyślnie zopieczętowano {total} plików."))
        self.app.master.after(0, lambda: self.ui_manager.flash_widget("green"))

    def _stamp_image(self, original_path: str, batch_mode: bool = False) -> None:
        try:
            import os
            img = Image.open(original_path)
            img.verify()
            img = Image.open(original_path)
            
            base, ext = os.path.splitext(os.path.basename(original_path))
            new_filename = self._get_capture_filename(ext.strip('.').lower() or "png")
            
            self._add_watermark(img).save(new_filename)
            logging.info(f"Ostemplowano plik: {new_filename}")
            
            self._post_stamp_actions(new_filename, original_path)
            if not batch_mode:
                self.app.master.after(0, lambda: self.ui_manager.flash_widget("green"))
        except Exception as e:
            logging.error(f"Bad stemplowania obrazu: {e}")
            if not batch_mode:
                self.app.master.after(0, lambda: self.ui_manager.flash_widget("red"))

    def _stamp_pdf(self, pdf_path: str, preset: str = "bottom-center", batch_mode: bool = False):
        try:
            import pikepdf
            from reportlab.pdfgen import canvas
            from reportlab.lib import colors
            import io
            import datetime

            data = self.app.data_manager.get_data_snapshot()
            
            # Text formatting
            seal_lines = self.app.template_engine.render().replace('₿', 'B').split('\n')
            seal_id = self.app.template_engine._generate_seal_id(data, datetime.datetime.now())
            
            f_size = self.config.get("pdf_font_size", 10)
            f_color_hex = self.config.get("pdf_font_color", "#F2A900")
            line_height = f_size * 1.3
            bar_padding = f_size * 0.8
            bar_height = (len(seal_lines) + 1) * line_height + bar_padding * 2

            with pikepdf.Pdf.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                if not batch_mode:
                    self.app.master.after(0, lambda: self.app.ui_manager.progress_manager.show(f"Veritas Seal ({total_pages} str.)", total_pages))
                
                # We will cache overlays by page size (w, h) to speed up multi-page documents
                overlay_cache = {}
                overlay_pdfs = [] # Keep these alive!

                for i, page in enumerate(pdf.pages):
                    if not batch_mode:
                        if i % 2 == 0 or total_pages < 15:
                            self.app.master.after(0, lambda v=i+1, t=total_pages: self.app.ui_manager.progress_manager.update(v, f"Przetwarzanie: {v}/{t} stron"))
                        
                    # Get actual page dimensions
                    mb = page.mediabox
                    w, h = float(mb[2]) - float(mb[0]), float(mb[3]) - float(mb[1])
                    size_key = (round(w, 2), round(h, 2))

                    if size_key not in overlay_cache:
                        packet = io.BytesIO()
                        can = canvas.Canvas(packet, pagesize=(w, h))
                        
                        can.saveState()
                        if preset != "ghost-mode":
                            can.setFont("Helvetica-Bold", f_size)
                            can.setFillColor(colors.HexColor(f_color_hex))
                            can.setStrokeColor(colors.transparent)
                        else:
                            can.setFont("Helvetica-Bold", f_size)
                            can.setFillColor(colors.Color(0,0,0, alpha=0.01))
                            can.setStrokeColor(colors.transparent)
                            
                        if preset == "bottom-center" or preset == "ghost-mode":
                            y_start = (len(seal_lines) + 1) * line_height + 15
                            x_align = w / 2
                            anchor = "center"
                        elif preset == "top-left":
                            y_start = h - line_height - 5
                            x_align = 20
                            anchor = "left"
                        elif preset == "top-right":
                            y_start = h - line_height - 5
                            x_align = w - 20
                            anchor = "right"
                        elif preset == "bottom-left":
                            y_start = (len(seal_lines) + 1) * line_height + 15
                            x_align = 20
                            anchor = "left"
                        elif preset == "bottom-right":
                            y_start = (len(seal_lines) + 1) * line_height + 15
                            x_align = w - 20
                            anchor = "right"
                        else:
                            y_start = (len(seal_lines) + 1) * line_height + 15
                            x_align = w / 2
                            anchor = "center"
                            
                        y_pos = y_start
                        for line in seal_lines:
                            if line.strip():
                                if anchor == "center": can.drawCentredString(x_align, y_pos, line.strip())
                                elif anchor == "left": can.drawString(x_align, y_pos, line.strip())
                                else: can.drawRightString(x_align, y_pos, line.strip())
                                y_pos -= line_height
                        
                        can.setFont("Helvetica", max(6, f_size - 2))
                        if anchor == "center": can.drawCentredString(x_align, y_pos - (f_size * 0.2), f"Veritas Seal ID: {seal_id}")
                        elif anchor == "left": can.drawString(x_align, y_pos - (f_size * 0.2), f"Veritas Seal ID: {seal_id}")
                        else: can.drawRightString(x_align, y_pos - (f_size * 0.2), f"Veritas Seal ID: {seal_id}")
                        can.restoreState()
                        
                        can.save()
                        packet.seek(0)
                        
                        # Store PDF to keep it alive
                        o_pdf = pikepdf.Pdf.open(packet)
                        overlay_pdfs.append(o_pdf)
                        overlay_cache[size_key] = o_pdf.pages[0]

                    # FIX: QPDFPageObjectHelper::getFormXObjectForPage called with a direct object
                    # Ensure the target page is an indirect object.
                    # pikepdf uses .is_indirect instead of .is_direct
                    if not page.obj.is_indirect:
                        pdf.make_indirect(page.obj)

                    # Add the overlay to current page
                    page.add_overlay(overlay_cache[size_key])

                # Metadata Update - Fixed XMP structure
                xmp_data = (
                    f'<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>'
                    f'<x:xmpmeta xmlns:x="adobe:ns:meta/">'
                    f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
                    f'<rdf:Description rdf:about="" xmlns:veritas="https://veritas-protocol.network">'
                    f'<veritas:seal>{seal_id}</veritas:seal>'
                    f'<veritas:blockheight>{data.get("blockheight", "unknown")}</veritas:blockheight>'
                    f'<veritas:hash>{data.get("hash_full", "unknown")}</veritas:hash>'
                    f'</rdf:Description></rdf:RDF></x:xmpmeta>'
                    f'<?xpacket end="w"?>'
                ).encode('utf-8')
                pdf.Root.Metadata = pikepdf.Stream(pdf, xmp_data)

                stamped_path = os.path.splitext(pdf_path)[0] + "_Veritas_Stamped.pdf"
                pdf.save(stamped_path, min_version=('1', 7))

            if not batch_mode:
                self.app.master.after(0, lambda: self.app.ui_manager.progress_manager.close())
            self._post_stamp_actions(stamped_path, pdf_path)
            if not batch_mode:
                self.app.master.after(0, lambda: messagebox.showinfo("PDF stamped", f"Zapieczetowano (widok pelnoekranowy):\n{stamped_path}"))
                self.app.master.after(0, lambda: self.ui_manager.flash_widget("green"))

        except pikepdf.PasswordError:
            if not batch_mode:
                self.app.master.after(0, lambda: self.app.ui_manager.progress_manager.close())
            logging.error(f"PDF chroniony haslem: {pdf_path}")
            if not batch_mode:
                self.app.master.after(0, lambda: messagebox.showerror("Blad PDF", "PDF jest chroniony haslem - odblokuj go recznie przed ostemplowaniem."))
                self.app.master.after(0, lambda: self.ui_manager.flash_widget("red"))
        except Exception as e:
            if not batch_mode:
                self.app.master.after(0, lambda: self.app.ui_manager.progress_manager.close())
            logging.error(f"PDF stamping error: {e}")
            if not batch_mode:
                self.app.master.after(0, lambda: messagebox.showerror("Blad PDF", str(e)))
                self.app.master.after(0, lambda: self.ui_manager.flash_widget("red"))

    def _post_stamp_actions(self, stamped_path: str, original_path: str):
        if self.config.get("ots_enabled"):
            self._submit_ots_if_enabled(stamped_path)
        if self.config.get("opreturn_enabled"):
            self._generate_opreturn_if_enabled(stamped_path)
        logging.info(f"Veritas Seal created: {stamped_path}")

    def _screenshot_worker(self, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> None:
        try:
            file_path = self._get_capture_filename("png")
            bbox_mss = {'left': region_bbox[0], 'top': region_bbox[1], 'width': region_bbox[2], 'height': region_bbox[3]} if region_bbox else self._get_capture_bbox()
            if not bbox_mss:
                return
            
            if _OPTIONAL_DEPENDENCIES['mss']:
                sct_img = mss.mss().grab(bbox_mss)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            else:
                img = ImageGrab.grab(bbox=(region_bbox[0], region_bbox[1], region_bbox[0] + region_bbox[2], region_bbox[1] + region_bbox[3]) if region_bbox else None)
            
            self._add_watermark(img).save(file_path, "PNG")
            logging.info(f"Zapisano zrzut: {file_path}")
            self._submit_ots_if_enabled(file_path)
            self._generate_opreturn_if_enabled(file_path)
            self.app.master.after(0, lambda: self.ui_manager.flash_widget("green"))
        except Exception as e:
            logging.error(f"Błąd zrzutu ekranu: {e}")
            self.app.master.after(0, lambda: self.ui_manager.flash_widget("red"))

    def _video_worker(self, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> None:
        out = None
        try:
            file_path = self._get_capture_filename("mp4")
            bbox = {'left': region_bbox[0], 'top': region_bbox[1], 'width': region_bbox[2], 'height': region_bbox[3]} if region_bbox else self._get_capture_bbox()
            if not bbox:
                return

            FPS, FRAME_TIME = 20.0, 1.0 / 20.0
            out = cv2.VideoWriter(file_path, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (bbox['width'], bbox['height']))
            
            with mss.mss() as sct:
                end_time = time.time() + self.config.get("video_duration")
                while time.time() < end_time:
                    start_time = time.perf_counter()
                    sct_img = sct.grab(bbox)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    watermarked_frame = self._add_watermark(img)
                    out.write(cv2.cvtColor(np.array(watermarked_frame), cv2.COLOR_RGB2BGR))
                    if (sleep_time := FRAME_TIME - (time.perf_counter() - start_time)) > 0:
                        time.sleep(sleep_time)
            logging.info(f"Zapisano wideo: {file_path}")
            self._submit_ots_if_enabled(file_path)
            self._generate_opreturn_if_enabled(file_path)
            self.app.master.after(0, lambda: self.ui_manager.flash_widget("green"))
        except Exception as e:
            logging.error(f"Błąd nagrywania wideo: {e}")
            self.app.master.after(0, lambda: self.ui_manager.flash_widget("red"))
        finally:
            if out is not None:
                out.release()
            gc.collect()  # FIX: memory leak

    def _gif_worker(self, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> None:
        try:
            file_path = self._get_capture_filename("gif")
            bbox = {'left': region_bbox[0], 'top': region_bbox[1], 'width': region_bbox[2], 'height': region_bbox[3]} if region_bbox else self._get_capture_bbox()
            frames = []
            if not bbox:
                return

            with mss.mss() as sct:
                end_time = time.time() + self.config.get("gif_duration")
                while time.time() < end_time:
                    sct_img = sct.grab(bbox)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    watermarked_frame = self._add_watermark(img)
                    frames.append(watermarked_frame.convert('P', palette=Image.Palette.ADAPTIVE))
                    time.sleep(0.1)
            if frames:
                frames[0].save(file_path, save_all=True, append_images=frames[1:], duration=100, loop=0)
                logging.info(f"Zapisano GIF: {file_path}")
                self._submit_ots_if_enabled(file_path)
                self._generate_opreturn_if_enabled(file_path)
                self.app.master.after(0, lambda: self.ui_manager.flash_widget("green"))
        except Exception as e:
            logging.error(f"Błąd nagrywania GIF: {e}")
            self.app.master.after(0, lambda: self.ui_manager.flash_widget("red"))
        finally:
            frames.clear()  # FIX: memory leak
            gc.collect()

    # --- OTS Integration Methods ---
    @staticmethod
    def _compute_file_sha256(file_path: str) -> str:
        """Compute SHA-256 hash of a file (Merkle Root for single file)."""
        sha = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha.update(chunk)
        return sha.hexdigest()

    def _submit_ots_if_enabled(self, file_path: str) -> None:
        """Submit file to OTS calendar if enabled and auto-submit is on."""
        if not self.config.get("ots_enabled") or not self.config.get("ots_auto_submit"):
            return
        try:
            file_hash = self._compute_file_sha256(file_path)
            digest_bytes = bytes.fromhex(file_hash)
            calendar_url = self.config.get("ots_calendar_url", "https://a.pool.opentimestamps.org")

            if _OPTIONAL_DEPENDENCIES.get('opentimestamps'):
                # Use opentimestamps library
                import io
                with open(file_path, 'rb') as f:
                    detached = DetachedTimestampFile.from_fd(OpSHA256(), f)
                # Submit via calendar
                from opentimestamps.calendar import RemoteCalendar
                cal = RemoteCalendar(calendar_url)
                cal.submit(detached.timestamp.msg)
                ots_path = file_path + '.ots'
                with open(ots_path, 'wb') as ots_f:
                    ctx = opentimestamps.core.serialize.StreamSerializationContext(ots_f)
                    detached.serialize(ctx)
                logging.info(f"Zapisano OTS proof: {ots_path}")
            elif _OPTIONAL_DEPENDENCIES.get('requests'):
                # Fallback: direct HTTP POST to OTS calendar
                submit_url = f"{calendar_url}/digest"
                resp = requests.post(submit_url, data=digest_bytes,
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                     timeout=REQUESTS_TIMEOUT)
                if resp.status_code == 200:
                    ots_path = file_path + '.ots'
                    with open(ots_path, 'wb') as ots_f:
                        ots_f.write(resp.content)
                    logging.info(f"Zapisano OTS proof (HTTP): {ots_path}")
                else:
                    logging.warning(f"OTS calendar returned status {resp.status_code}")
            else:
                logging.warning("Brak bibliotek do przesylania OTS (opentimestamps lub requests).")
        except Exception as e:
            logging.error(f"Błąd przesyłania do OTS: {e}")

    @staticmethod
    def verify_ots_file(ots_path: str, file_path: str) -> Tuple[bool, str]:
        """Verify an OTS proof against a file. Returns (success, message)."""
        try:
            if not os.path.exists(ots_path) or not os.path.exists(file_path):
                return False, "File or OTS proof not found."
            if _OPTIONAL_DEPENDENCIES.get('opentimestamps'):
                with open(ots_path, 'rb') as ots_f:
                    ctx = opentimestamps.core.serialize.StreamDeserializationContext(ots_f)
                    detached = DetachedTimestampFile.deserialize(ctx)
                with open(file_path, 'rb') as f:
                    expected = DetachedTimestampFile.from_fd(OpSHA256(), f)
                if detached.file_hash_op == expected.file_hash_op:
                    return True, "OTS proof matches file hash."
                return False, "OTS proof hash mismatch."
            else:
                return False, "opentimestamps library required for verification."
        except Exception as e:
            return False, f"Verification error: {e}"

    # --- OP_RETURN Integration Methods ---
    def generate_opreturn_psbt(self, payload: str) -> dict:
        """Generate a raw PSBT wrapper for an OP_RETURN transaction from a payload string.
        Returns dict with psbt_b64, payload, fee_sat, txid_expected."""
        result = {"psbt_b64": "", "payload": payload, "fee_sat": 0, "txid_expected": ""}
        try:
            payload_bytes = payload.encode('utf-8')[:self.config.get('opreturn_max_bytes', 83)]
            fee_rate = self.config.get("opreturn_fee_sat_per_vb", 15)

            # Manual raw tx construction (minimal OP_RETURN)
            # Version (4 bytes LE)
            version = b'\x02\x00\x00\x00'
            # Input count
            input_count = b'\x01'
            # Dummy input: prev_txid (32 bytes zero) + prev_vout (4 bytes ffff) + script_len (0) + sequence
            prev_txid = b'\x00' * 32
            prev_vout = b'\xff\xff\xff\xff'
            script_sig = b''
            script_sig_len = bytes([len(script_sig)])
            sequence = b'\xff\xff\xff\xff'
            tx_input = prev_txid + prev_vout + script_sig_len + script_sig + sequence
            # Output count
            output_count = b'\x01'
            # OP_RETURN output: value=0, script = 6a + pushdata
            value = b'\x00' * 8
            op_return_script = bytes([0x6a, len(payload_bytes)]) + payload_bytes
            script_len = bytes([len(op_return_script)])
            tx_output = value + script_len + op_return_script
            # Locktime
            locktime = b'\x00\x00\x00\x00'
            raw_bytes = version + input_count + tx_input + output_count + tx_output + locktime
            estimated_vsize = len(raw_bytes)
            fee_sat = fee_rate * estimated_vsize
            txid = hashlib.sha256(hashlib.sha256(raw_bytes).digest()).digest()[::-1].hex()
            
            # Wrap in PSBT format
            def compact_size(n):
                if n < 253: return bytes([n])
                elif n <= 65535: return b'\xfd' + struct.pack("<H", n)
                elif n <= 0xffffffff: return b'\xfe' + struct.pack("<I", n)
                else: return b'\xff' + struct.pack("<Q", n)
            
            psbt_bytes = b"psbt\xff" + b"\x01\x00" + compact_size(len(raw_bytes)) + raw_bytes + b"\x00" + b"\x00" + b"\x00"
            psbt_b64 = base64.b64encode(psbt_bytes).decode('ascii')
            
            result.update({"psbt_b64": psbt_b64, "fee_sat": fee_sat, "txid_expected": txid})
            logging.info(f"Wygenerowano PSBT (manual wrapper): fee={fee_sat} sat")
        except Exception as e:
            logging.error(f"Bład generowania PSBT: {e}")
        return result

    def _generate_opreturn_if_enabled(self, file_path: str) -> None:
        """Generate OP_RETURN payload and save .opreturn.psbt alongside capture file."""
        if not self.config.get("opreturn_enabled"):
            return
        try:
            file_hash = self._compute_file_sha256(file_path)
            data = self.app.data_manager.get_data_snapshot()
            now = datetime.datetime.now()
            seal_id = self.app.template_engine._generate_seal_id(data, now)
            prefix = self.config.get("opreturn_payload_prefix", "VERITAS:")
            merkle_root = file_hash[:16]
            ots_commitment = hashlib.sha256(seal_id.encode()).hexdigest()[:16]
            payload = f"{prefix}{seal_id}:{merkle_root}:{ots_commitment}"[:self.config.get("opreturn_max_bytes", 83)]

            tx_result = self.generate_opreturn_psbt(payload)

            # Save .opreturn.psbt
            psbt_path = file_path + '.opreturn.psbt'
            with open(psbt_path, 'w', encoding='utf-8') as f:
                f.write(tx_result.get('psbt_b64', ''))
            
            # Save .opreturn.txt
            txt_path = file_path + '.opreturn.txt'
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"# OP_RETURN PSBT Anchor — Veritas Bridge v{APP_VERSION}\n")
                f.write(f"# Generated: {now.isoformat()}\n")
                f.write(f"payload: {payload}\n")
                f.write(f"fee_sat: {tx_result.get('fee_sat', 0)}\n")
                f.write(f"txid_expected: {tx_result.get('txid_expected', '')}\n")
                f.write(f"merkle_root: {file_hash}\n")
                f.write(f"seal_id: {seal_id}\n")
                
            logging.info(f"Zapisano PSBT do {psbt_path} i plik informacyjny {txt_path}")
            
            # Store the latest psbt path for UI access if needed
            self.app.data_manager.set_transient("latest_psbt_path", psbt_path)
            
        except Exception as e:
            logging.error(f"Bład generowania PSBT po capture: {e}")

    def _broadcast_via_core(self, psbt_b64: str) -> bool:
        """Broadcast PSBT via Bitcoin Core RPC (walletprocesspsbt -> finalizepsbt -> sendrawtransaction)."""
        if not psbt_b64:
            return False
        try:
            url = self.config.get("bitcoin_core_rpc_url")
            auth = (self.config.get("bitcoin_core_rpc_user"), self.config.get("bitcoin_core_rpc_pass"))
            if not url or not _OPTIONAL_DEPENDENCIES.get('requests'):
                logging.warning("Broadcast wymaga skonfigurowanego węzła i biblioteki requests.")
                return False
                
            # 1. walletprocesspsbt
            payload1 = {'jsonrpc': '1.0', 'id': 'opreturn', 'method': 'walletprocesspsbt', 'params': [psbt_b64]}
            r1 = requests.post(url, json=payload1, auth=auth, timeout=REQUESTS_TIMEOUT)
            r1.raise_for_status()
            res1 = r1.json().get('result', {})
            psbt_signed = res1.get('psbt')
            if not psbt_signed:
                logging.error("Node did not return signed psbt.")
                return False
                
            # 2. finalizepsbt
            payload2 = {'jsonrpc': '1.0', 'id': 'opreturn', 'method': 'finalizepsbt', 'params': [psbt_signed]}
            r2 = requests.post(url, json=payload2, auth=auth, timeout=REQUESTS_TIMEOUT)
            r2.raise_for_status()
            res2 = r2.json().get('result', {})
            raw_hex = res2.get('hex')
            if not raw_hex:
                logging.error("Node failed to finalize psbt.")
                return False
                
            # 3. sendrawtransaction
            payload3 = {'jsonrpc': '1.0', 'id': 'opreturn', 'method': 'sendrawtransaction', 'params': [raw_hex]}
            r3 = requests.post(url, json=payload3, auth=auth, timeout=REQUESTS_TIMEOUT)
            r3.raise_for_status()
            res3 = r3.json().get('result')
            
            if res3:
                logging.info(f"PSBT broadcast OK: {res3}")
                return True
        except Exception as e:
            logging.error(f"Bład broadcastu PSBT (via Core): {e}")
        return False

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
        # FIX: Pozwalamy na zmianę rozmiaru (ważne przy różnych DPI)
        self.master.resizable(True, True)
        
        notebook = ttk.Notebook(self.master)
        notebook.pack(padx=10, pady=10, fill="both", expand=True)
        
        tabs = {"tab_template": self._create_tab_main, "tab_capture": self._create_tab_capture, "tab_data": self._create_tab_data, "tab_veritas": self._create_tab_veritas, "tab_about": self._create_tab_about}
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
        self._center_on_screen()

    def _center_on_screen(self):
        """Centruje okno ustawień na monitorze, na którym znajduje się kursor myszy."""
        try:
            self.master.update_idletasks()
            width = self.master.winfo_reqwidth()
            height = self.master.winfo_reqheight()
            
            # Pobierz pozycję kursora
            mouse_x = self.master.winfo_pointerx()
            mouse_y = self.master.winfo_pointery()
            
            # FIX: Multi-monitor + DPI aware centering
            if _OPTIONAL_DEPENDENCIES['screeninfo']:
                monitors = get_monitors()
                for m in monitors:
                    if m.x <= mouse_x < m.x + m.width and m.y <= mouse_y < m.y + m.height:
                        # Account for DPI scaling via tkinter
                        try:
                            dpi_scale = self.master.winfo_fpixels('1i') / 72.0
                        except Exception:
                            dpi_scale = 1.0
                        scaled_w = int(width / dpi_scale) if dpi_scale > 1.5 else width
                        scaled_h = int(height / dpi_scale) if dpi_scale > 1.5 else height
                        x = m.x + (m.width - scaled_w) // 2
                        y = m.y + (m.height - scaled_h) // 2
                        self.master.geometry(f"+{x}+{y}")
                        return

            # Fallback: środek ekranu domyślnego
            screen_width = self.master.winfo_screenwidth()
            screen_height = self.master.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.master.geometry(f"+{x}+{y}")
        except Exception:
            pass  # Ignoruj błędy geometrii, system okienny poradzi sobie sam

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
        seed_entry = ttk.Entry(glyph_frame, textvariable=self._create_var("glyph_seed"))
        seed_entry.pack(side='left', fill='x', expand=True, padx=5)
        seed_entry.bind("<KeyRelease>", lambda e: self._update_resonance_chamber())
        ttk.Button(glyph_frame, text=self.lang.get("insert_glyph_btn"), command=lambda: self._insert_code('%glyph%')).pack(side='left')
        
        resonance_frame = tk.LabelFrame(lf_appearance, text="Glyph Resonance Chamber (Live Preview)", bg="#1A2332", fg="#8899AA", font=("Segoe UI", 9))
        resonance_frame.pack(fill='x', padx=5, pady=5)
        self.resonance_canvas = tk.Canvas(resonance_frame, height=130, bg="#0D1B2A", highlightthickness=0)
        self.resonance_canvas.pack(fill='x', padx=5, pady=5)
        self.master.after(200, self._update_resonance_chamber)
        
        misc_options_frame = ttk.Frame(options_frame)
        misc_options_frame.pack(fill='x', pady=(5,0))
        ttk.Checkbutton(misc_options_frame, text=self.lang.get("full_hash_chk"), variable=self._create_var("display_full_hash", tk.BooleanVar)).pack(side='left')
        ttk.Checkbutton(misc_options_frame, text=self.lang.get("lock_position_chk"), variable=self._create_var("lock_position", tk.BooleanVar)).pack(side='left', padx=10)
        ttk.Checkbutton(misc_options_frame, text=self.lang.get("always_on_top_chk"), variable=self._create_var("always_on_top", tk.BooleanVar)).pack(side='left')
        
        lf_glyph_info = ttk.LabelFrame(parent, text=self.lang.get("about_glyph_title"))
        lf_glyph_info.pack(fill='x', padx=5, pady=5)
        ttk.Label(lf_glyph_info, text=self.lang.get("about_glyph_desc"), wraplength=450, justify='left').pack(padx=5, pady=5)
        
        self.master.after(100, lambda: self.line_editors[0].focus_set() if self.line_editors else None)

    def _update_resonance_chamber(self):
        if not hasattr(self, 'resonance_canvas') or not self.resonance_canvas.winfo_exists():
            return
        
        self.resonance_canvas.delete("all")
        
        seed = self.vars.get("glyph_seed", tk.StringVar(value="")).get()
        glyph = self.app.template_engine._generate_glyph(seed)
        
        # update dimensions to get real width
        self.resonance_canvas.update_idletasks()
        w = max(self.resonance_canvas.winfo_width(), 450)
        h = max(self.resonance_canvas.winfo_height(), 130)
        
        if self.resonance_canvas.winfo_width() <= 1:
            self.master.after(100, self._update_resonance_chamber)
            return

        styles = [
            {"name": "Standard", "color": "#F2A900", "font_mod": ("Segoe UI", 22, "bold"), "offset": (0, 0)},
            {"name": "Outline", "color": "#FFFFFF", "font_mod": ("Consolas", 22), "offset": (2, 2)},
            {"name": "Neon", "color": "#00FFFF", "font_mod": ("Segoe UI", 22, "italic"), "offset": (-1, 1)},
            {"name": "Rune", "color": "#FF5555", "font_mod": ("Times New Roman", 24, "bold"), "offset": (0, 0)},
            {"name": "Ghost", "color": "#556677", "font_mod": ("Segoe UI", 22), "offset": (0, 0)}
        ]
        
        # Grid layout: Row 1 = 3 items, Row 2 = 2 items
        row1_spacing = w / 3
        row2_spacing = w / 2

        for i, style in enumerate(styles):
            if i < 3:
                # Top row
                x = (i * row1_spacing) + (row1_spacing / 2)
                y = 35
            else:
                # Bottom row
                x = ((i - 3) * row2_spacing) + (row2_spacing / 2)
                y = 95
            
            # Draw label
            self.resonance_canvas.create_text(x, y + 22, text=style["name"], fill="#6C757D", font=("Segoe UI", 9, "bold"))
            
            # Draw Glyph
            if style["name"] == "Outline":
                self.resonance_canvas.create_text(x + style["offset"][0], y + style["offset"][1], text=glyph, fill="#8899AA", font=style["font_mod"])
                self.resonance_canvas.create_text(x, y, text=glyph, fill="#1A2332", font=style["font_mod"])
            elif style["name"] == "Neon":
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                    self.resonance_canvas.create_text(x+dx, y+dy, text=glyph, fill="#005555", font=style["font_mod"])
                self.resonance_canvas.create_text(x, y, text=glyph, fill=style["color"], font=style["font_mod"])
            else:
                self.resonance_canvas.create_text(x, y, text=glyph, fill=style["color"], font=style["font_mod"])

    def _create_template_menus(self, parent: ttk.Frame):
        SAMPLES = [("Data i czas (krótki)", "d MMM yyyy HH:mm"), ("Data (długi)", "dddd, d MMMM yyyy"), ("Data i czas (pełny)", "yyyy-MM-dd HH:mm:ss")]
        DATE_CODES = [("Dzień (1)", 'd'), ("Dzień (01)", 'dd'), ("Nazwa dnia (Pon)", 'ddd'), ("Nazwa dnia (Poniedziałek)", 'dddd'), ("-", "-"), ("Miesiąc (7)", 'M'), ("Miesiąc (07)", 'MM'), ("Nazwa miesiąca (Lip)", 'MMM'), ("Nazwa miesiąca (Lipiec)", 'MMMM'), ("-", "-"), ("Rok (25)", 'yy'), ("Rok (2025)", 'yyyy')]
        TIME_CODES = [("Godzina (1-12)", 'h'), ("(01-12)", 'hh'), ("(0-23)", 'H'), ("(00-23)", 'HH'), ("-", "-"), ("Minuta (5)", 'm'), ("(05)", 'mm'), ("-", "-"), ("Sekunda (8)", 's'), ("(08)", 'ss'), ("-", "-"), ("Dzies. sek. (1)", 'S'), ("Set. sek. (12)", 'SS'), ("Tys. sek. (123)", 'SSS'), ("-", "-"), ("AM/PM", 'tt'), ("A/P", 't')]
        SEPARATOR_CODES = [("Spacja", ' '), ("Tekst dosłowny", "''"), ("Dwukropek", ':'), ("Przecinek", ','), ("Kropka", '.'), ("Myśnik", '-'), ("Ukośnik", '/'), ("Pion. kreska", ' | ')]
        SPECIAL_CODES = [("Glif", "%glyph%"), ("Swatch Time", '@'), ("Wysokość bloku", '%blockheight%'), ("Hash bloku", '%hash%'), ("-", "-"), ("Veritas Protocol", '%veritas%'), ("Seal ID", '%seal%'), ("Protocol Status", '%protocol_status%')]

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

    def _on_editor_focus(self, event: tk.Event):
        self.last_focused_editor = event.widget

    def _insert_code(self, code: str):
        if target := self.last_focused_editor:
            target.insert(tk.INSERT, "''" if code == "''" else code)
            if code == "''":
                target.icursor(target.index(tk.INSERT) - 1)
            target.focus_set()

    def _set_sample(self, s: str):
        self.vars["prompt_line_1"].set(s)
        self.vars["prompt_line_2"].set("")
        self.vars["prompt_line_3"].set("")

    def _reset_templates(self):
        d = self.config.get_default_config()
        self.vars["prompt_line_1"].set(d["prompt_line_1"])
        self.vars["prompt_line_2"].set(d["prompt_line_2"])
        self.vars["prompt_line_3"].set(d["prompt_line_3"])

    def _create_line_editor(self, p, i):
        f = ttk.Frame(p)
        f.pack(fill='x', padx=5, pady=2)
        ttk.Checkbutton(f, variable=self._create_var(f"line_{i}_enabled", tk.BooleanVar)).pack(side='left')
        e = ttk.Entry(f, textvariable=self._create_var(f"prompt_line_{i}"))
        e.pack(side='left', fill='x', expand=True, padx=5)
        e.bind("<FocusIn>", self._on_editor_focus)
        self.line_editors.append(e)
        ttk.Combobox(f, textvariable=self._create_var(f"line_{i}_align"), values=["left", "center", "right"], state="readonly", width=8).pack(side='left')

    def _create_font_section(self, p):
        f = ttk.Frame(p)
        f.pack(fill='x', padx=5, pady=5)
        ttk.Label(f, text=self.lang.get("font_label")).pack(side='left')
        ttk.Combobox(f, textvariable=self._create_var("font_family"), values=sorted(tkfont.families()), state='readonly').pack(side='left', expand=True, fill='x', padx=5)
        ttk.Label(f, text=self.lang.get("size_label")).pack(side='left')
        ttk.Combobox(f, textvariable=self._create_var("base_font_size", tk.IntVar), values=[8,10,12,14,16,18,24,36], width=5).pack(side='left')
        f_s = ttk.Frame(p)
        f_s.pack(fill='x', padx=5)
        ttk.Checkbutton(f_s, text=self.lang.get("bold_chk"), variable=self._create_var("font_weight", tk.StringVar), onvalue='bold', offvalue='normal').pack(side='left')
        ttk.Checkbutton(f_s, text=self.lang.get("italic_chk"), variable=self._create_var("font_slant", tk.StringVar), onvalue='italic', offvalue='roman').pack(side='left', padx=10)

    def _create_color_section(self, p):
        f = ttk.Frame(p)
        f.pack(fill='x', padx=5, pady=5)
        self._create_color_picker(f, "color_text_btn", 'text_color')
        self._create_color_picker(f, "color_shadow_btn", 'outline_color')
        f_o = ttk.Frame(p)
        f_o.pack(fill='x', padx=5, pady=(5,0))
        ttk.Checkbutton(f_o, text=self.lang.get("use_shadow_chk"), variable=self._create_var("use_outline", tk.BooleanVar)).pack(side='left', padx=(0,10))
        ttk.Label(f_o, text=self.lang.get("thickness_label")).pack(side='left')
        ttk.Spinbox(f_o, from_=0, to=10, width=5, textvariable=self._create_var("outline_thickness", tk.IntVar)).pack(side='left', padx=(0,10))
        
        s_map = {self.lang.get("style_outline"): "outline", self.lang.get("style_3d"): "3d_offset"}
        d_map = {self.lang.get("dir_dr"): "down-right", self.lang.get("dir_dl"): "down-left", self.lang.get("dir_ur"): "up-right", self.lang.get("dir_ul"): "up-left"}
        
        ttk.Label(f_o, text=self.lang.get("style_label")).pack(side='left')
        s_var = tk.StringVar(value=next((n for n,v in s_map.items() if v == self.config.get("shadow_style")), list(s_map.keys())[0]))
        s_combo = ttk.Combobox(f_o, textvariable=s_var, values=list(s_map.keys()), state="readonly", width=10)
        s_combo.pack(side='left', padx=(0,10))
        self.vars["shadow_style_display"] = s_var
        
        dir_lbl, d_var = ttk.Label(f_o, text=self.lang.get("direction_label")), tk.StringVar(value=next((n for n,v in d_map.items() if v == self.config.get("shadow_direction")), list(d_map.keys())[0]))
        dir_combo = ttk.Combobox(f_o, textvariable=d_var, values=list(d_map.keys()), state="readonly", width=12)
        self.vars["shadow_direction_display"] = d_var
        
        toggle = lambda e=None: [dir_lbl.pack(side='left'), dir_combo.pack(side='left')] if s_var.get() == self.lang.get("style_3d") else [dir_lbl.pack_forget(), dir_combo.pack_forget()]
        s_combo.bind("<<ComboboxSelected>>", toggle)
        toggle()

    def _create_color_picker(self, p, lbl, k):
        var = self._create_var(k)
        f = ttk.Frame(p)
        f.pack(side='left', padx=5)
        swatch = tk.Label(f, text="  ", bg=var.get(), relief="sunken")
        def pick():
            c = colorchooser.askcolor(parent=self.master, initialcolor=var.get())[1]
            if c:
                var.set(c)
                swatch.config(bg=c)
        ttk.Button(f, text=self.lang.get(lbl), command=pick).pack(side='left')
        swatch.pack(side='left', padx=5)
    
    def _create_prefix_template_creator(self, parent: ttk.Frame, target_entry: ttk.Entry, target_var: tk.StringVar):
        SAMPLES = [("Blok i Data", "capture_%blockheight%_yyyy-MM-dd"), ("Data i Czas", "yyyyMMdd_HHmmss_")]
        DATE_CODES = [("Rok (2025)", 'yyyy'), ("Miesiąc (07)", 'MM'), ("Dzień (01)", 'dd')]
        TIME_CODES = [("Godzina (00-23)", 'HH'), ("Minuta (05)", 'mm'), ("Sekunda (08)", 'ss')]
        SEPARATOR_CODES = [("Znak _", '_'), ("Myślnik", '-'), ("Kropka", '.')]
        SPECIAL_CODES = [("Glif", "%glyph%"), ("Wysokość bloku", '%blockheight%'), ("Hash bloku", '%hash%')]
        
        def _insert_code(code: str):
            target_entry.insert(tk.INSERT, code)
            target_entry.focus_set()
        def _set_sample(sample: str):
            target_var.set(sample)
            target_entry.focus_set()
        def _reset():
            target_var.set(self.app.config_manager.get_default_config()["capture_filename_prefix"])
        
        def create_menubutton(text_key, items, is_sample=False):
            mb = ttk.Menubutton(parent, text=self.lang.get(text_key))
            menu = tk.Menu(mb, tearoff=0)
            for label, code in items:
                if label == "-": menu.add_separator()
                else:
                    cmd = (lambda s=code: _set_sample(s)) if is_sample else (lambda c=code: _insert_code(c))
                    menu.add_command(label=f"{label} ({code})", command=cmd)
            mb.config(menu=menu)
            mb.pack(side='left')
            
        create_menubutton("samples_btn", SAMPLES, is_sample=True)
        create_menubutton("date_btn", DATE_CODES)
        create_menubutton("time_btn", TIME_CODES)
        create_menubutton("separator_btn", SEPARATOR_CODES)
        create_menubutton("special_btn", SPECIAL_CODES)
        ttk.Button(parent, text=self.lang.get("reset_btn"), command=_reset).pack(side='left', padx=(5,0))

    def _toggle_watermark_angle_control(self, var, scale_widget, label_widget):
        state = 'disabled' if var.get() else 'normal'
        scale_widget.config(state=state)
        label_widget.config(state=state)

    def _create_tab_capture(self, p):
        lf_h = ttk.LabelFrame(p, text=self.lang.get("hotkeys_title"))
        lf_h.pack(fill="x", padx=5, pady=5, ipady=5)
        ttk.Label(lf_h, text=self.lang.get("hotkeys_desc"), justify="left").pack(anchor="w", padx=5, pady=5)
        
        lf_o = ttk.LabelFrame(p, text=self.lang.get("capture_options_title"))
        lf_o.pack(fill="x", padx=5, pady=5, ipady=5)
        m_f = ttk.Frame(lf_o)
        m_f.pack(fill='x', padx=5, pady=5)
        ttk.Label(m_f, text=self.lang.get("capture_monitor_label")).pack(side='left', padx=(0,5))
        
        m_opts = [self.lang.get("capture_all_screens")]
        if _OPTIONAL_DEPENDENCIES['screeninfo']:
            for m in sorted(get_monitors(), key=lambda m: m.x):
                m_opts.append(f"Monitor {m.width}x{m.height} @ ({m.x},{m.y}){self.lang.get('primary_monitor_tag') if m.is_primary else ''}")
        
        var = self._create_var("capture_screen")
        var.set(var.get() if var.get() in m_opts else m_opts[0])
        ttk.Combobox(m_f, textvariable=var, values=m_opts, state="readonly").pack(fill='x')
        ttk.Checkbutton(lf_o, text=self.lang.get("hide_widget_chk"), variable=self._create_var("hide_widget_on_capture", tk.BooleanVar)).pack(anchor='w', padx=5)
        
        lf_r = ttk.LabelFrame(p, text=self.lang.get("recording_options_title"))
        lf_r.pack(fill="x", padx=5, pady=5)
        rec_f = ttk.Frame(lf_r)
        rec_f.pack(fill='x', padx=5, pady=5)
        r_state = "normal" if all(_OPTIONAL_DEPENDENCIES[k] for k in ['cv2', 'numpy', 'mss']) else "disabled"
        ttk.Label(rec_f, text=self.lang.get("video_duration_label")).pack(side='left')
        ttk.Spinbox(rec_f, from_=1, to=300, width=5, textvariable=self._create_var("video_duration", tk.IntVar), state=r_state).pack(side='left', padx=(5, 15))
        ttk.Label(rec_f, text=self.lang.get("gif_duration_label")).pack(side='left')
        ttk.Spinbox(rec_f, from_=1, to=60, width=5, textvariable=self._create_var("gif_duration", tk.IntVar), state=r_state).pack(side='left', padx=5)
        
        lf_path = ttk.LabelFrame(p, text=self.lang.get("path_title"))
        lf_path.pack(fill="x", padx=5, pady=5)
        path_f = ttk.Frame(lf_path)
        path_f.pack(fill='x', padx=5, pady=5)
        p_var = self._create_var("capture_folder")
        ttk.Entry(path_f, textvariable=p_var, state="readonly").pack(side="left", fill="x", expand=True)
        ttk.Button(path_f, text=self.lang.get("change_btn"), command=lambda v=p_var: v.set(filedialog.askdirectory(initialdir=v.get()) or v.get())).pack(side="left")
        
        pfx_f = ttk.Frame(lf_path)
        pfx_f.pack(fill='x', padx=5, pady=(0, 5))
        ttk.Checkbutton(pfx_f, text=self.lang.get("prefix_chk"), variable=self._create_var("use_capture_filename_prefix", tk.BooleanVar)).pack(side='left')
        pfx_var = self._create_var("capture_filename_prefix")
        pfx_entry = ttk.Entry(pfx_f, textvariable=self._create_var("capture_filename_prefix"))
        pfx_entry.pack(side='left', fill='x', expand=True)
        
        lf_pfx_c = ttk.LabelFrame(lf_path, text=self.lang.get("prefix_template_creator_title"))
        lf_pfx_c.pack(fill='x', padx=5, pady=(5,0))
        c_menu_f = ttk.Frame(lf_pfx_c)
        c_menu_f.pack(fill='x', padx=5, pady=5)
        self._create_prefix_template_creator(c_menu_f, pfx_entry, pfx_var)
        
        lf_w = ttk.LabelFrame(p, text=self.lang.get("watermark_title"))
        lf_w.pack(fill="x", padx=5, pady=5)
        
        style_map = {self.lang.get("watermark_style_tiled"): "tiled", self.lang.get("watermark_style_arranged"): "arranged", self.lang.get("watermark_style_single"): "single", self.lang.get("watermark_style_vertical"): "vertical"}
        if _OPTIONAL_DEPENDENCIES['qrcode']:
            style_map[self.lang.get("watermark_style_qrcode")] = "qrcode"
        
        style_f = ttk.Frame(lf_w)
        style_f.pack(fill='x', padx=5, pady=5)
        ttk.Label(style_f, text=self.lang.get("watermark_style_label")).pack(side='left')
        style_var = tk.StringVar(value=next((n for n, v in style_map.items() if v == self.config.get("watermark_style")), list(style_map.keys())[0]))
        style_combo = ttk.Combobox(style_f, textvariable=style_var, values=list(style_map.keys()), state="readonly", width=20)
        style_combo.pack(side='left')
        self.vars["watermark_style_display"] = style_var

        text_options_frame = ttk.Frame(lf_w)
        qr_options_frame = ttk.Frame(lf_w)
        
        chk_f = ttk.Frame(text_options_frame)
        chk_f.pack(fill='x', padx=5, pady=2)
        for i in range(1, 4):
            ttk.Checkbutton(chk_f, text=self.lang.get(f"line_{i}_chk"), variable=self._create_var(f"watermark_include_line{i}", tk.BooleanVar)).pack(side='left', padx=2)
        
        shadow_f = ttk.Frame(text_options_frame)
        shadow_f.pack(fill='x', padx=5, pady=2)
        ttk.Checkbutton(shadow_f, text=self.lang.get("watermark_use_shadow_chk"), variable=self._create_var("watermark_use_shadow", tk.BooleanVar)).pack(side='left')
        
        count_f = ttk.Frame(style_f)
        count_lbl = ttk.Label(count_f, text=self.lang.get("watermark_count_label"))
        count_combo = ttk.Combobox(count_f, textvariable=self._create_var("watermark_arranged_count", tk.IntVar), values=[1,3,5,7], state="readonly", width=5)
        auto_scale_f = ttk.Frame(text_options_frame)
        auto_scale_f.pack(fill='x', padx=5, pady=2)
        auto_scale_var = self._create_var("watermark_auto_scale", tk.BooleanVar)
        _, opacity_lbl = self._create_slider(text_options_frame, "opacity_label", "watermark_opacity", 0, 100)
        angle_scale, angle_lbl = self._create_slider(text_options_frame, "angle_label", "watermark_angle", 0, 90)
        ttk.Checkbutton(auto_scale_f, text=self.lang.get("watermark_auto_scale_chk"), variable=auto_scale_var, command=lambda: self._toggle_watermark_angle_control(auto_scale_var, angle_scale, angle_lbl)).pack(side='left')
        self._toggle_watermark_angle_control(auto_scale_var, angle_scale, angle_lbl)

        pos_map = {"center": self.lang.get("pos_center"), "top-left": self.lang.get("pos_tl"), "top-right": self.lang.get("pos_tr"), "bottom-left": self.lang.get("pos_bl"), "bottom-right": self.lang.get("pos_br")}
        qr_pos_f = ttk.Frame(qr_options_frame)
        qr_pos_f.pack(fill='x', padx=5, pady=2)
        ttk.Label(qr_pos_f, text=self.lang.get("watermark_qr_position_label"), width=15).pack(side='left')
        qr_pos_var = tk.StringVar(value=pos_map.get(self.config.get("watermark_qr_position"), pos_map["center"]))
        self.vars["watermark_qr_position_display"] = qr_pos_var
        ttk.Combobox(qr_pos_f, textvariable=qr_pos_var, values=list(pos_map.values()), state="readonly").pack(fill='x', expand=True)

        self._create_slider(qr_options_frame, "watermark_qr_size_label", "watermark_qr_code_size", 50, 250)
        self._create_slider(qr_options_frame, "opacity_label", "watermark_opacity", 0, 100)
        
        def _toggle_style_controls(e=None):
            is_qr = style_var.get() == self.lang.get("watermark_style_qrcode")
            is_countable = style_var.get() in [self.lang.get("watermark_style_arranged"), self.lang.get("watermark_style_vertical")]

            if is_qr:
                text_options_frame.pack_forget()
                qr_options_frame.pack(fill='x')
            else:
                qr_options_frame.pack_forget()
                text_options_frame.pack(fill='x')
            
            if is_countable:
                count_f.pack(side='left', padx=(10,5))
                count_lbl.pack(side='left')
                count_combo.pack(side='left')
            else:
                count_f.pack_forget()
        
        style_combo.bind("<<ComboboxSelected>>", _toggle_style_controls)
        _toggle_style_controls()

    def _create_slider(self, p, lbl_key, var_name, from_, to, command=None) -> Tuple[ttk.Scale, ttk.Label]:
        f = ttk.Frame(p)
        f.pack(fill='x', padx=5, pady=2)
        var = self._create_var(var_name, tk.IntVar)
        
        def on_slide(v):
            lbl.config(text=f"{self.lang.get(lbl_key)} {round(float(v))}")
            if command:
                command(v)

        lbl = ttk.Label(f, text=f"{self.lang.get(lbl_key)} {var.get()}", width=15)
        lbl.pack(side='left')
        scale = ttk.Scale(f, from_=from_, to=to, orient='horizontal', variable=var, command=on_slide)
        scale.pack(fill='x', expand=True)
        scale.set(var.get())
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
        if not self.celtic_label:
            return
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
            if self._qr_update_job:
                self.master.after_cancel(self._qr_update_job)
            return

        current_config = self.app.config_manager.config.copy()
        for i in range(1, 4):
            key = f"prompt_line_{i}"
            if key in current_config:
                current_config[key] = re.sub(r'\s*([|]|\b(ss|s|SSS|SS|S)\b)\s*', '', current_config[key]).strip()
        
        qr_content = self.app.template_engine.render(config_override=current_config)

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
    
    def _create_tab_veritas(self, p):
        """Zakładka Veritas Protocol — epistemic status dashboard (Two Columns)."""
        container = ttk.Frame(p)
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        left_col = ttk.Frame(container)
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        right_col = ttk.Frame(container)
        right_col.pack(side='right', fill='both', expand=True, padx=(10, 0))

        # ================= LEFT COLUMN =================
        # --- Philosophy Section ---
        lf_phil = ttk.LabelFrame(left_col, text=self.lang.get("veritas_philosophy_title"))
        lf_phil.pack(fill='x', pady=(0, 10))
        ttk.Label(lf_phil, text=self.lang.get("veritas_philosophy_quote"),
                  font=('Segoe UI', 11, 'bold italic'), foreground='#D4AF37').pack(pady=(10, 5))
        ttk.Label(lf_phil, text=self.lang.get("veritas_philosophy_pillars"),
                  font=('Consolas', 8), foreground='#6C757D').pack(pady=(0, 10))

        # --- Epistemic Status ---
        lf_status = ttk.LabelFrame(left_col, text=self.lang.get("veritas_epistemic_title"))
        lf_status.pack(fill='x', pady=10)

        is_pl = self.lang.current_lang_code == 'pl'
        for item_id, name_en, name_pl, color_key, pct, status_text in VERITAS_STATUS_ITEMS:
            row_frame = ttk.Frame(lf_status)
            row_frame.pack(fill='x', padx=10, pady=2)
            name = name_pl if is_pl else name_en
            color = VERITAS_COLORS.get(color_key, '#888')
            dot = tk.Canvas(row_frame, width=12, height=12, highlightthickness=0)
            dot.pack(side='left', padx=(0, 5))
            dot.create_oval(1, 1, 11, 11, fill=color, outline=color)
            ttk.Label(row_frame, text=name, width=28, anchor='w', font=('Segoe UI', 9)).pack(side='left')
            ttk.Label(row_frame, text=f"{pct}", width=5, anchor='center').pack(side='left')
            ttk.Label(row_frame, text=status_text, foreground=color, font=('Segoe UI', 9, 'bold')).pack(side='left', padx=5)

        # --- Roadmap Progress ---
        lf_road = ttk.LabelFrame(left_col, text=self.lang.get("veritas_roadmap_title"))
        lf_road.pack(fill='x', pady=10)

        for symbol, name_en, name_pl, progress in VERITAS_PHASES:
            phase_frame = ttk.Frame(lf_road)
            phase_frame.pack(fill='x', padx=10, pady=2)
            label_text = f"Phase {symbol}: {name_pl if is_pl else name_en}"
            ttk.Label(phase_frame, text=label_text, width=25, anchor='w', font=('Segoe UI', 9)).pack(side='left')
            pb = ttk.Progressbar(phase_frame, length=120, mode='determinate', value=progress)
            pb.pack(side='left', padx=5)
            pct_color = VERITAS_COLORS['green_ok'] if progress >= 50 else VERITAS_COLORS['gold'] if progress > 0 else VERITAS_COLORS['red_alert']
            ttk.Label(phase_frame, text=f"{progress}%", foreground=pct_color, width=5, font=('Segoe UI', 9, 'bold')).pack(side='left')

        # --- Status Bar Color Config ---
        lf_bar = ttk.LabelFrame(left_col, text=self.lang.get("veritas_bar_color_title"))
        lf_bar.pack(fill='x', pady=10)

        for cfg_key, label_key in [("status_bar_color_ok", "veritas_bar_ok_label"), ("status_bar_color_err", "veritas_bar_err_label")]:
            row = ttk.Frame(lf_bar)
            row.pack(fill='x', padx=10, pady=3)
            ttk.Label(row, text=self.lang.get(label_key)).pack(side='left')
            color_var = self._create_var(cfg_key)
            swatch = tk.Label(row, text='    ', bg=color_var.get() or '#FFFFFF', relief='solid', borderwidth=1, cursor='hand2')
            swatch.pack(side='left', padx=(8, 0))
            ttk.Label(row, text=color_var.get(), font=('Consolas', 8)).pack(side='left', padx=5)
            def _pick_bar_color(var=color_var, sw=swatch, r=row):
                result = colorchooser.askcolor(initialcolor=var.get(), title=self.lang.get("veritas_bar_color_title"))
                if result[1]:
                    var.set(result[1])
                    sw.configure(bg=result[1])
                    for child in r.winfo_children():
                        if isinstance(child, ttk.Label) and hasattr(child, 'cget'):
                            try:
                                if child.cget('font') == 'TkDefaultFont' or 'Consolas' in str(child.cget('font')):
                                    child.config(text=result[1])
                                    break
                            except Exception: pass
            swatch.bind('<Button-1>', lambda e, fn=_pick_bar_color: fn())

        # ================= RIGHT COLUMN =================

        # --- Live Protocol Metrics (Paper §4-§7) ---
        lf_metrics = ttk.LabelFrame(right_col, text="Live Protocol Metrics (§4-§7)")
        lf_metrics.pack(fill='x', pady=(0, 10))

        data = self.app.data_manager.get_data_snapshot()
        last_block_time = data.get("last_block_time_local", 0)

        if ve and last_block_time:
            t_mass = ve.compute_temporal_mass(last_block_time)
            ecm = ve.compute_ecm_confidence(
                has_data=isinstance(data.get("blockheight"), int),
                use_custom_node=self.config.get("use_custom_node", False),
                ots_enabled=self.config.get("ots_enabled", False),
                opreturn_enabled=self.config.get("opreturn_enabled", False),
            )
            # Simulated VoicePower (no real stake — demo values)
            demo_stake = 0.01  # researcher tier
            demo_lock_days = 30
            vp = ve.compute_voicepower(demo_stake, demo_lock_days)
            tier = ve.get_fidelity_bond_tier(demo_stake)

            # Simulated Q-Score
            q = ve.compute_q_score(
                friction=0.3, stake_btc=demo_stake,
                temporal_mass=t_mass, has_timechain=True,
                honesty_posterior=0.85
            )
            # Domain Friction Oracle
            dfo = ve.compute_domain_friction_posterior(slashed=0, accepted=0)
        else:
            t_mass, ecm, vp, tier, q, dfo = 0.0, 0, 0.0, "N/A", 0.0, 0.5

        metrics = [
            ("§4.2 Temporal Mass", f"{t_mass:.4f}", VERITAS_COLORS['cyan']),
            ("§4.1 ECM Confidence", f"{ecm}%", VERITAS_COLORS['gold'] if ecm < 85 else VERITAS_COLORS['green_ok']),
            ("§6.1 VoicePower (sim)", f"{vp:.2f}", VERITAS_COLORS['purple']),
            ("§6.2 Fidelity Bond", f"{tier}", VERITAS_COLORS['gold']),
            ("§7.6 Q-Score (sim)", f"{q:.4f}", VERITAS_COLORS['cyan']),
            ("§8 DomainFriction", f"{dfo:.3f}", VERITAS_COLORS['gold']),
        ]
        for metric_name, metric_val, metric_color in metrics:
            mrow = ttk.Frame(lf_metrics)
            mrow.pack(fill='x', padx=10, pady=1)
            ttk.Label(mrow, text=metric_name, width=22, anchor='w',
                      font=('Consolas', 8)).pack(side='left')
            ttk.Label(mrow, text=metric_val, foreground=metric_color,
                      font=('Consolas', 9, 'bold')).pack(side='left', padx=5)

        if not ve:
            ttk.Label(lf_metrics, text="⚠ veritas_engine.py not found — using fallback",
                      foreground=VERITAS_COLORS['red_alert'], font=('Segoe UI', 8)).pack(padx=10, pady=3)

        # --- Veritas Watermark Mode ---
        lf_wm = ttk.LabelFrame(right_col, text=self.lang.get("veritas_watermark_title"))
        lf_wm.pack(fill='x', pady=(0, 10))

        seal_var = self._create_var("veritas_include_seal", tk.BooleanVar)
        ttk.Checkbutton(lf_wm, text=self.lang.get("veritas_include_seal_chk"), variable=seal_var).pack(anchor='w', padx=10, pady=(5, 2))

        always_seal_var = self._create_var("veritas_always_seal", tk.BooleanVar)
        ttk.Checkbutton(lf_wm, text=self.lang.get("veritas_always_seal_chk"), variable=always_seal_var).pack(anchor='w', padx=10, pady=(2, 5))

        tag_frame = ttk.Frame(lf_wm)
        tag_frame.pack(fill='x', padx=10, pady=(2, 8))
        ttk.Label(tag_frame, text=self.lang.get("veritas_epistemic_tag_label"), font=('Segoe UI', 9, 'bold')).pack(side='left')
        tag_var = self._create_var("veritas_epistemic_tag")
        ttk.Entry(tag_frame, textvariable=tag_var, width=25).pack(side='left', padx=5, fill='x', expand=True)

        # --- OpenTimestamps Integration Section ---
        lf_ots = ttk.LabelFrame(right_col, text=self.lang.get("ots_title"))
        lf_ots.pack(fill='x', pady=10)

        ots_enabled_var = self._create_var("ots_enabled", tk.BooleanVar)
        ttk.Checkbutton(lf_ots, text=self.lang.get("ots_enabled_chk"), variable=ots_enabled_var).pack(anchor='w', padx=10, pady=(5, 2))

        ots_auto_var = self._create_var("ots_auto_submit", tk.BooleanVar)
        ttk.Checkbutton(lf_ots, text=self.lang.get("ots_auto_submit_chk"), variable=ots_auto_var).pack(anchor='w', padx=10, pady=(2, 5))

        ots_url_frame = ttk.Frame(lf_ots)
        ots_url_frame.pack(fill='x', padx=10, pady=(2, 8))
        ttk.Label(ots_url_frame, text=self.lang.get("ots_calendar_label"), font=('Segoe UI', 9)).pack(side='left')
        ttk.Entry(ots_url_frame, textvariable=self._create_var("ots_calendar_url"), width=25).pack(side='left', padx=5, fill='x', expand=True)

        # --- OP_RETURN Anchoring Section ---
        lf_opr = ttk.LabelFrame(right_col, text=self.lang.get("opreturn_title"))
        lf_opr.pack(fill='x', pady=10)

        opr_enabled_var = self._create_var("opreturn_enabled", tk.BooleanVar)
        ttk.Checkbutton(lf_opr, text=self.lang.get("opreturn_enabled_chk"), variable=opr_enabled_var).pack(anchor='w', padx=10, pady=(5, 5))

        opr_prefix_frame = ttk.Frame(lf_opr)
        opr_prefix_frame.pack(fill='x', padx=10, pady=(0, 5))
        ttk.Label(opr_prefix_frame, text=self.lang.get("opreturn_prefix_label"), font=('Segoe UI', 9, 'bold')).pack(side='left')
        ttk.Entry(opr_prefix_frame, textvariable=self._create_var("opreturn_payload_prefix"), width=20).pack(side='left', padx=5)

        opr_node_var = self._create_var("opreturn_use_bitcoin_core", tk.BooleanVar)
        ttk.Checkbutton(lf_opr, text=self.lang.get("opreturn_use_node_chk"), variable=opr_node_var).pack(anchor='w', padx=10, pady=(5, 5))

        opr_rpc_frame = tk.Frame(lf_opr, bg="#f0f0f0", bd=1, relief="ridge")
        opr_rpc_frame.pack(fill='x', padx=20, pady=(0, 5))
        ttk.Label(opr_rpc_frame, text="RPC URL:", background="#f0f0f0").grid(row=0, column=0, sticky='w', pady=2, padx=5)
        url_entry = ttk.Entry(opr_rpc_frame, textvariable=self._create_var("bitcoin_core_rpc_url"), width=25)
        url_entry.grid(row=0, column=1, sticky='we', padx=5, pady=2)
        ttk.Label(opr_rpc_frame, text="User:", background="#f0f0f0").grid(row=1, column=0, sticky='w', pady=2, padx=5)
        user_entry = ttk.Entry(opr_rpc_frame, textvariable=self._create_var("bitcoin_core_rpc_user"), width=15)
        user_entry.grid(row=1, column=1, sticky='w', padx=5, pady=2)
        ttk.Label(opr_rpc_frame, text="Pass:", background="#f0f0f0").grid(row=2, column=0, sticky='w', pady=2, padx=5)
        pass_entry = ttk.Entry(opr_rpc_frame, textvariable=self._create_var("bitcoin_core_rpc_pass"), show="*", width=15)
        pass_entry.grid(row=2, column=1, sticky='w', padx=5, pady=2)

        def toggle_rpc(*args):
            state = "normal" if opr_node_var.get() else "disabled"
            url_entry.config(state=state)
            user_entry.config(state=state)
            pass_entry.config(state=state)
        opr_node_var.trace_add("write", toggle_rpc)
        toggle_rpc()

        opr_fee_frame = ttk.Frame(lf_opr)
        opr_fee_frame.pack(fill='x', padx=10, pady=(5, 5))
        ttk.Label(opr_fee_frame, text=self.lang.get("opreturn_fee_label"), font=('Segoe UI', 9)).pack(side='left')
        ttk.Spinbox(opr_fee_frame, from_=1, to=500, textvariable=self._create_var("opreturn_fee_sat_per_vb", tk.IntVar), width=6).pack(side='left', padx=5)

    def _create_tab_about(self, p):
        m_f = ttk.Frame(p)
        m_f.pack(fill="both", expand=True, padx=5, pady=5)
        lf_i = ttk.LabelFrame(m_f, text=self.lang.get("about_info_title"))
        lf_i.pack(fill="x", pady=(0, 5))
        ttk.Label(lf_i, text="TimeChain Desktop Widget", font=("Segoe UI", 16, "bold")).pack(pady=(5, 0))
        ttk.Label(lf_i, text=f"Wersja: {APP_VERSION} \"{APP_CODENAME}\"").pack()
        ttk.Label(lf_i, text=f"🔱 {self.lang.get('veritas_protocol_label')} {VERITAS_PROTOCOL_VERSION}", font=("Segoe UI", 10, "bold"), foreground=VERITAS_COLORS['gold']).pack(pady=(2, 0))
        ttk.Label(lf_i, text=self.lang.get("veritas_philosophy_quote"), font=("Segoe UI", 8, "italic"), foreground=VERITAS_COLORS['cyan']).pack(pady=(0, 3))
        ttk.Label(lf_i, text=self.lang.get("about_author"), font=("Segoe UI", 9, "italic")).pack(pady=5)
        lang_f = ttk.Frame(lf_i)
        lang_f.pack(pady=5)
        ttk.Label(lang_f, text=self.lang.get("general_lang_label")).pack(side='left')
        lang_var = tk.StringVar(value=self.lang.get_lang_name_from_code(self.config.get("language")))
        self.vars["language_display"] = lang_var
        lang_combo = ttk.Combobox(lang_f, textvariable=lang_var, values=list(self.lang.get_lang_map().keys()), state="readonly")
        lang_combo.pack(side='left')
        lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)
        
        lf_d = ttk.LabelFrame(m_f, text=self.lang.get("about_instruction_title"))
        lf_d.pack(fill="x", pady=(0, 5))
        ttk.Label(lf_d, text=self.lang.get("about_instruction_desc"), wraplength=450, justify='left').pack(pady=5, padx=10)
        
        lf_deps = ttk.LabelFrame(m_f, text=self.lang.get("about_deps_title"))
        lf_deps.pack(fill="x", pady=5)
        
        deps_container = ttk.Frame(lf_deps)
        deps_container.pack(pady=10, fill="x", padx=10)
        deps_container.columnconfigure(0, weight=1)
        deps_container.columnconfigure(1, weight=1)
        deps_container.columnconfigure(2, weight=1)

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

        # --- Auto-Update Section ---
        lf_update = ttk.LabelFrame(m_f, text=self.lang.get("auto_update_title"))
        lf_update.pack(fill='x', pady=5)
        update_f = ttk.Frame(lf_update)
        update_f.pack(fill='x', padx=10, pady=5)
        ttk.Checkbutton(update_f, text=self.lang.get("auto_update_chk"), variable=self._create_var("auto_update_check", tk.BooleanVar)).pack(side='left')
        update_status = ttk.Label(update_f, text="")
        update_status.pack(side='left', padx=10)

        def _check_update():
            if not _OPTIONAL_DEPENDENCIES.get('requests'):
                update_status.config(text=self.lang.get("auto_update_error"), foreground='red')
                return
            def _do_check():
                try:
                    resp = requests.get("https://api.github.com/repos/adepthus/Timechain-Widget/releases/latest", timeout=10)
                    if resp.status_code == 200:
                        latest = resp.json().get('tag_name', '').lstrip('v')
                        if latest and latest != APP_VERSION:
                            self.master.after(0, lambda: update_status.config(
                                text=self.lang.get("auto_update_available", version=latest), foreground=VERITAS_COLORS['gold']))
                        else:
                            self.master.after(0, lambda: update_status.config(
                                text=self.lang.get("auto_update_up_to_date"), foreground='green'))
                    else:
                        self.master.after(0, lambda: update_status.config(
                            text=self.lang.get("auto_update_error"), foreground='red'))
                except Exception:
                    self.master.after(0, lambda: update_status.config(
                        text=self.lang.get("auto_update_error"), foreground='red'))
            threading.Thread(target=_do_check, daemon=True).start()

        ttk.Button(update_f, text=self.lang.get("auto_update_check_btn"), command=_check_update).pack(side='left')

    def _on_language_change(self, e=None):
        if (n_code := self.lang.get_lang_map().get(self.vars["language_display"].get(), "en")) != self.config.get("language"):
            self.config.set("language", n_code)
            self.config.save()
            self.app.lang.set_language(n_code)
            self._on_close()
            self.ui.show_settings()
            
    def _toggle_node_fields(self):
        state = 'normal' if self.vars.get("use_custom_node", tk.BooleanVar(value=False)).get() else 'disabled'
        [w.config(state=state) for w in self.node_widgets]
    
    def apply(self, status_lbl):
        # --- Validation ---
        # FIX: Glyph seed validation (128 char limit)
        glyph_seed = self.vars.get("glyph_seed", tk.StringVar(value="")).get()
        if len(glyph_seed) > 128:
            status_lbl.config(text=self.lang.get("glyph_seed_warning"), foreground="red")
            self.master.after(5000, lambda: status_lbl.config(text=""))
            return

        capture_folder = self.vars.get("capture_folder", tk.StringVar(value="")).get()
        if capture_folder and not os.path.isdir(capture_folder):
            try:
                os.makedirs(capture_folder, exist_ok=True)
            except OSError:
                status_lbl.config(text=self.lang.get("error_capture_folder_invalid"), foreground="red")
                self.master.after(5000, lambda: status_lbl.config(text=""))
                return
        if self.vars.get("use_custom_node", tk.BooleanVar(value=False)).get():
            node_url = self.vars.get("custom_node_url", tk.StringVar(value="")).get()
            if not node_url.startswith(("http://", "https://")):
                status_lbl.config(text=self.lang.get("error_node_url_invalid"), foreground="red")
                self.master.after(5000, lambda: status_lbl.config(text=""))
                return

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
    
    def is_alive(self) -> bool:
        return self.master.winfo_exists()

    def focus(self) -> None:
        self.master.lift()
        self.master.focus_force()

class PDFSealConfiguratorWindow:
    def __init__(self, ui_manager: "UIManager", pdf_paths: list, image_paths: list):
        self.ui = ui_manager
        self.app = ui_manager.app
        self.pdf_paths = pdf_paths
        self.image_paths = image_paths
        self.master = tk.Toplevel(self.app.master)
        self.master.title("Veritas Batch Factory & PDF Configurator")
        self.master.geometry("550x380")
        self.master.attributes("-topmost", True)
        self.master.configure(bg="#1A2332")
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)
        
        info_text = f"Batch Factory: {len(pdf_paths)} PDFów"
        if image_paths:
            info_text += f", {len(image_paths)} Obrazów"
        if len(pdf_paths) == 1 and not image_paths:
            info_text = f"Stempel PDF: {os.path.basename(pdf_paths[0])}"
            
        tk.Label(self.master, text=info_text, bg="#1A2332", fg="white", font=("Segoe UI", 12, "bold")).pack(pady=(15, 5))
        
        self.preset_var = tk.StringVar(value="bottom-center")
        presets_frame = tk.LabelFrame(self.master, text="Pozycja pieczęci dla PDF", bg="#1A2332", fg="#8899AA", font=("Segoe UI", 9))
        presets_frame.pack(fill="x", padx=20, pady=10)
        
        for p in ["top-left", "top-right", "bottom-left", "bottom-right", "bottom-center", "ghost-mode"]:
            tk.Radiobutton(presets_frame, text=p, variable=self.preset_var, value=p, bg="#1A2332", fg="white", selectcolor="#223344", activebackground="#1A2332", activeforeground="white", font=("Consolas", 9)).pack(side="left", padx=5, pady=5)
            
        settings_frame = tk.LabelFrame(self.master, text="Opcjone Stylu (Eksperymentalne)", bg="#1A2332", fg="#8899AA", font=("Segoe UI", 9))
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(settings_frame, text="Wybrany profil zaaplikuje powlekającą strukturę na wszystkie dokumenty PDF.\nPliki graficzne zostaną zapieczętowane domyślnie. Czekaj na sygnał sukcesu.", bg="#1A2332", fg="gray", font=("Segoe UI", 8)).pack(pady=5)

        tk.Button(self.master, text="Zastosuj stempel (Rozpocznij procesing masowy)", command=self._apply, bg="#00D4FF", fg="#1A2332", font=("Segoe UI", 10, "bold"), cursor="hand2", pady=5).pack(pady=20)
        
        self.master.update_idletasks()
        w = self.master.winfo_reqwidth()
        h = self.master.winfo_reqheight()
        x = (self.master.winfo_screenwidth() // 2) - (w // 2)
        y = (self.master.winfo_screenheight() // 2) - (h // 2)
        self.master.geometry(f"+{x}+{y}")
        self.master.grab_set()

    def _on_close(self):
        self.master.destroy()

    def _apply(self):
        preset = self.preset_var.get()
        self.app.capture_manager._submit_capture_task(self.app.capture_manager._stamp_batch_mixed, self.pdf_paths, self.image_paths, preset)
        self.master.destroy()

class GlobalProgressManager:
    def __init__(self, ui_manager: "UIManager"):
        self.ui = ui_manager
        self.window: Optional[tk.Toplevel] = None
        self.progress_var = tk.DoubleVar()
        self.label_var = tk.StringVar(value="Przetwarzanie...")

    def show(self, title="Przetwarzanie", max_val=100):
        if self.window and self.window.winfo_exists():
            self.window.destroy()
        self.window = tk.Toplevel(self.ui.app.master)
        self.window.title(title)
        self.window.geometry("400x120")
        self.window.attributes("-topmost", True)
        self.window.configure(bg="#1A2332")
        
        tk.Label(self.window, textvariable=self.label_var, bg="#1A2332", fg="white", font=("Segoe UI", 10)).pack(pady=(20, 5))
        from tkinter import ttk
        pb = ttk.Progressbar(self.window, variable=self.progress_var, maximum=max_val)
        pb.pack(fill="x", padx=20, pady=5)
        self.progress_var.set(0)
        
        self.window.update_idletasks()
        w = self.window.winfo_reqwidth()
        h = self.window.winfo_reqheight()
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"+{x}+{y}")
        
    def update(self, val, text=None):
        if self.window and self.window.winfo_exists():
            self.progress_var.set(val)
            if text:
                self.label_var.set(text)
            self.window.update()
            
    def close(self):
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None

class UIManager:
    """Zarządza wszystkimi oknami i elementami interfejsu użytkownika."""
    def __init__(self, app: "TimechainApp"):
        self.app = app
        self.widget_window = WidgetWindow(self)
        self.settings_window: Optional[SettingsWindow] = None
        self.progress_manager = GlobalProgressManager(self)
        self.pdf_configurator: Optional[PDFSealConfiguratorWindow] = None

    def show_pdf_seal_configurator(self, pdf_paths: list, image_paths: list = None):
        if self.pdf_configurator and self.pdf_configurator.master.winfo_exists():
            self.pdf_configurator.master.destroy()
        self.pdf_configurator = PDFSealConfiguratorWindow(self, pdf_paths, image_paths or [])

    def setup_ui(self) -> None:
        self.widget_window.setup()

    def update_widget(self, text: str, is_inverted: bool, config_override: Optional[Dict] = None) -> None:
        self.widget_window.update_display(text, is_inverted, config_override)

    def flash_widget(self, color: str = "green", duration_ms: int = 200) -> None:
        self.widget_window.flash(color, duration_ms)

    def get_widget_geometry(self) -> Tuple[int, int, int, int]:
        return self.widget_window.get_geometry()

    def show_settings(self) -> None:
        if self.settings_window and self.settings_window.is_alive():
            self.settings_window.focus()
            return
        self.settings_window = SettingsWindow(self)
        self.settings_window.setup()

    def launch_pyblock(self) -> None:
        if not (command := self.app.config_manager.get("pyblock_command")):
            messagebox.showwarning("Brak Komendy", "Nie skonfigurowano komendy do uruchomienia PyBlock. Sprawdź ustawienia.")
            self.show_settings()
            return
        PyBlockLauncher.launch(command)

class TimechainApp:
    """Główna klasa aplikacji, która łączy wszystkie komponenty."""
    def __init__(self, master: tk.Tk):
        self.master = master
        set_dpi_awareness_windows()
        self.config_manager = ConfigManager()
        self.lang = LanguageManager(self, self.config_manager.get("language"))
        self.data_manager = DataManager(self)
        self.template_engine = TemplateEngine(self)
        self.ui_manager = UIManager(self)
        self.capture_manager = CaptureManager(self)
        self.color_analyzer = ColorAnalyzer(self)
        self._cancel_update = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="Worker")
        self._ui_update_needed = threading.Event()

    def run(self) -> None:
        self.master.attributes('-topmost', self.config_manager.get('always_on_top', True))
        self.ui_manager.setup_ui()
        self.master.deiconify()
        self.capture_manager.start_hotkey_listener()
        self.color_analyzer.start()
        self.master.protocol("WM_DELETE_WINDOW", self.close_app)
        self._data_fetch_loop()
        self._update_loop()

    def request_ui_update(self) -> None:
        if self.master.winfo_exists() and not self._ui_update_needed.is_set():
            self._ui_update_needed.set()
            self.master.after_idle(self._refresh_display_if_needed)

    def _refresh_display_if_needed(self) -> None:
        if self._ui_update_needed.is_set():
            self._refresh_display()
            self._ui_update_needed.clear()

    def _refresh_display(self, config_override: Optional[Dict[str, Any]] = None) -> None:
        if self._cancel_update.is_set():
            return
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
            self._cancel_update.set()
            self.capture_manager.stop_hotkey_listener()
            self.color_analyzer.stop()
            if self.master.winfo_exists():
                self.config_manager.set("last_position", self.master.geometry())
            self.config_manager.save()
            self.executor.shutdown(wait=False, cancel_futures=True)
            self.master.destroy()
            logging.info("Aplikacja zamknięta.")

if __name__ == "__main__":
    try:
        root = TkinterDnD.Tk()
    except Exception:
        root = tk.Tk()
    root.withdraw()
    app = None
    try:
        app = TimechainApp(root)
        app.run()
        root.mainloop()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Aplikacja przerwana przez użytkownika.")
    except Exception as e:
        logging.critical(f"Wystąpił nieoczekiwany błąd krytyczny: {e}", exc_info=True)
        try:
            if tk._default_root and tk._default_root.winfo_exists():
                messagebox.showerror("Błąd Krytyczny", f"Wystąpił błąd:\n\n{e}")
        except Exception:
            pass
    finally:
        if app and not app._cancel_update.is_set():
            app.close_app()
        sys.exit(0)

# --- CHANGELOG v21.4.0 "Thermodynamic Alignment" ---
# NEW (v21.4.0):
#   - veritas_engine.py: New module implementing all formulas from Paper v10.3:
#     - §4.1 Epistemic Mass with exponential decay
#     - §4.2 Temporal Mass (Lindy Effect): tanh(ln(1+Δt)/10)
#     - §5.2 THI XYZW Four-Axis Friction calculation
#     - §6.1 VoicePower: √S × T² × e^(-γ·Δt_idle)
#     - §6.2 Fidelity Bond tier classification
#     - §7.6 Q-Score (Qualia Engine v2.8)
#     - §8   DomainFrictionOracle Bayesian posterior
#   - Live Protocol Metrics panel in Veritas Tab (right column)
#   - Deterministic Seal ID: no longer depends on datetime.now()
#     Same block + same glyph = reproducible seal (breaking change for seal format)
#   - ECM calculation delegated to veritas_engine (single source of truth)
#   - Protocol constants extracted from magic numbers
# BUGFIXES (v21.4.0):
#   - B1: Added missing `import struct` (crash in PSBT generation)
#   - B2: Added missing `import tempfile` (crash in temp file creation)
#   - B3: Fixed `re, ge, be` variable names shadowing the `re` module
#         (caused regex failures after pulse loop execution)
#   - B4+B5: Replaced unsafe `data_manager.data[...]` direct access with
#            thread-safe `set_transient()`/`get_transient()` methods
#   - B6: Replaced bare `except: pass` with typed exception handling + logging
# SECURITY (v21.4.0):
#   - S2: os.startfile() now validates path ends with '.psbt'
#   - S4: pyperclip import guarded behind _OPTIONAL_DEPENDENCIES check
# INHERITED (v21.3.1): See previous changelog below.
# ---

# --- CHANGELOG v21.3.0 "Veritas Bridge + OTS + OP_RETURN" ---
# NEW (v21.3.0):
#   - Pełny mechanizm OP_RETURN anchoring:
#     - generate_opreturn_tx() — raw tx via bitcoinlib lub manual fallback.
#     - _generate_opreturn_if_enabled() — auto-save .opreturn.txt po każdym capture.
#     - _broadcast_opreturn_tx() — broadcast via custom Bitcoin node RPC.
#     - Sekcja 'OP_RETURN Anchoring' w zakładce Veritas (checkbox, prefix, fee, broadcast).
#     - Wiersz OP_RETURN Payload + przycisk 'Generate OP_RETURN TX' w Veritas Seal Info.
#     - Placeholder %opreturn% w szablonach.
#   - Config keys: opreturn_enabled, opreturn_payload_prefix, opreturn_use_custom_node,
#     opreturn_fee_sat_per_vb, opreturn_broadcast_automatically.
#   - Zależność opcjonalna: bitcoinlib.
# INHERITED (v21.2.0):
#   - Pełna integracja OpenTimestamps (OTS) + Merkle Root.
#   - .ots proof files + verify_ots_file() + %ots% placeholder.
#   - "Always include Veritas Seal" + "Copy as OP_RETURN hex" + Auto-Update.
#   - 7 poprawek błędów (QR auto-scale, tiled watermark, ColorAnalyzer, PyBlock,
#     glyph_seed, memory leak, SettingsWindow center).
# ---
