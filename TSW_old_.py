import os
import time
import requests
from tkinter import Tk, Label, Menu, simpledialog

def get_api_data(url, cache_time=60):
    """Pobiera dane z URL i przechowuje je w pamięci podręcznej przez określony czas."""
    cache_key = url.replace("/", "_").replace(":", "_")
    if cache_time > 0:
        try:
            with open(cache_key, 'r') as f:
                data = f.read()
                if time.time() - os.path.getmtime(cache_key) < cache_time:
                    return data
        except FileNotFoundError:
            pass
    response = requests.get(url)
    data = response.text
    with open(cache_key, 'w') as f:
        f.write(data)
    return data

def get_current_block():
    url = "https://blockstream.info/api/blocks/tip/height"
    return get_api_data(url)

def get_current_block_hash():
    url = "https://blockchain.info/q/latesthash"
    return get_api_data(url)

def get_swatch_internet_time():
    now = time.time() % 86400
    beats = int(now / 86.4)
    return f"@{beats:03}"

def create_watermark_text(prompt, lang='pl'):
    """Tworzy tekst znaku wodnego na podstawie monitu użytkownika i opcjonalnych informacji."""
    text = f"{prompt}@"
    if lang == 'pl':
        text += f"Obecny czas: {time.strftime('%H:%M:%S')} | ₿eatTime: {get_swatch_internet_time()} | Blok Timechain: {get_current_block()}"
        text += f"\nHash bloku: {get_current_block_hash()}"
    else:
        text += f"Current Time: {time.strftime('%H:%M:%S')} | ₿eatTime: {get_swatch_internet_time()} | Timechain Block: {get_current_block()}"
        text += f"\nBlock hash: {get_current_block_hash()}"
    return text

def create_widget(prompt, lang='pl'):
    def update_text():
        watermark_text = create_watermark_text(prompt, lang=lang)
        label_shadow.config(text=watermark_text)
        label_main.config(text=watermark_text)
        root.after(1000, update_text)  # Update every second

    def on_right_click(event):
        popup = Menu(root, tearoff=0)
        popup.add_command(label="Edit Widget", command=lambda: edit_widget(prompt, lang))
        popup.add_command(label="Close", command=root.destroy)
        popup.tk_popup(event.x_root, event.y_root)

    def on_left_click(event):
        global last_click_x, last_click_y
        last_click_x, last_click_y = event.x, event.y

    def on_drag(event):
        x, y = event.x_root - last_click_x, event.y_root - last_click_y
        root.geometry(f"+{x}+{y}")

    def edit_widget(prompt, lang):
        new_prompt = simpledialog.askstring("Edit Widget", "Enter new prompt:", initialvalue=prompt)
        if new_prompt:
            label_shadow.config(text=new_prompt)
            label_main.config(text=new_prompt)
            create_widget(new_prompt, lang)

    root = Tk()
    root.attributes('-topmost', True)
    root.overrideredirect(True)
    root.wm_attributes('-transparentcolor', root['bg'])
    root.antialias=(True)

    shadow_offset = 22  # Increased shadow offset for a stronger 3D effect
    font_size = 21  # Increased font size for better edge quality

    label_shadow = Label(root, text="", font=("Helvetica", font_size), fg="black", bg=root['bg'])
    label_shadow.pack()
    label_shadow.place(x=shadow_offset, y=shadow_offset)

    label_main = Label(root, text="", font=("Helvetica", font_size), fg="white", bg=root['bg'])
    label_main.pack()

    root.bind("<Button-3>", on_right_click)
    root.bind("<Button-1>", on_left_click)
    root.bind("<B1-Motion>", on_drag)

    update_text()

    root.geometry("+100+100")  # Set initial position
    root.mainloop()

if __name__ == "__main__":
    lang = input("Choose language (en/pl): ").strip().lower()
    lang = 'en' if lang == 'en' else 'pl'

    while True:
        prompt = input("Enter watermark prompt for timechain (or 'q' to quit): " if lang == 'en' else 
                       "Wprowadź tekst monitu znaku wodnego na timechain (lub 'q' aby zakończyć): ").strip()
        if prompt.lower() == 'q':
            break
        if prompt:
            break
        print("Prompt cannot be empty. Please enter a valid prompt." if lang == 'en' else 
              "Monit nie może być pusty. Wprowadź prawidłowy tekst monitu.")

    if prompt.lower() != 'q':
        print(f"You entered '{prompt}' as the watermark prompt." if lang == 'en' else f"Wprowadziłeś '{prompt}' jako monit znaku wodnego.")
        create_widget(prompt, lang)
