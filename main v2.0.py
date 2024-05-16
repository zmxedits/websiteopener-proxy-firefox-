import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, Menu, Toplevel
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import requests
import threading
import logging
import re
import geckodriver_autoinstaller
from concurrent.futures import ThreadPoolExecutor
import time

def install_missing_packages():
    required_packages = [
        "selenium",
        "webdriver_manager",
        "requests",
        "tk",
    ]

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    try:
        import geckodriver_autoinstaller
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "geckodriver-autoinstaller"])

install_missing_packages()

logging.basicConfig(filename='website_opener.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def ensure_geckodriver():
    driver_path = GeckoDriverManager().install()
    return driver_path

def start_with_proxy(proxy, url, proxy_display):
    try:
        prox = Proxy()
        prox.proxy_type = ProxyType.MANUAL
        prox.http_proxy = proxy
        prox.ssl_proxy = proxy

        driver_path = ensure_geckodriver()
        options = webdriver.FirefoxOptions()
        options.proxy = prox

        driver = webdriver.Firefox(options=options)
        URL = url
        driver.get(URL)
    except Exception as e:
        print(f"Fehler beim Zugriff auf die URL: {e}")
    finally:
        driver.quit()

def proxy_list():
    proxies = []
    try:
        with open("proxies.txt", "r") as proxiesfile:
            for aline in proxiesfile.readlines():
                proxies.append(aline.strip())
        if not proxies:
            raise ValueError("Die Proxy-Liste ist leer.")
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Proxy-Liste: {e}")
        messagebox.showerror("Fehler", f"Fehler beim Lesen der Proxy-Liste: {e}")
    return proxies

def start_browsing(url, count, proxy_display):
    proxies = []
    try:
        with open("valid_proxies.txt", "r") as file:
            proxies = file.readlines()
    except FileNotFoundError:
        messagebox.showerror("Fehler", "Die Datei valid_proxies.txt wurde nicht gefunden.")
        return

    if len(proxies) == 0:
        messagebox.showerror("Fehler", "Die Proxy-Liste ist leer.")
        return

    threads = []
    for i in range(count):
        if i < len(proxies):
            proxy = proxies[i].strip()
            thread = threading.Thread(target=start_with_proxy, args=(proxy, url, proxy_display))
            threads.append(thread)
            thread.start()
        else:
            messagebox.showwarning("Warnung", "Nicht genügend Proxies in der Liste.")
            break

    for thread in threads:
        thread.join()

    messagebox.showinfo("Fertig", "Alle Browser-Fenster wurden geöffnet.")

def on_start_thread(url, count, proxy_display):
    threading.Thread(target=start_browsing, args=(url, count, proxy_display)).start()

def validate_url(url):
    pattern = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(pattern, url) is not None

def validate_proxies(url, proxy_display, start_button, language):
    def proxy_check():
        proxies = proxy_list()
        if len(proxies) == 0:
            messagebox.showerror("Error" if language == "EN" else "Fehler", "The proxy list is empty." if language == "EN" else "Die Proxy-Liste ist leer.")
            return

        proxy_display.insert(tk.END, "Starting proxy check...\n" if language == "EN" else "Überprüfung der Proxies gestartet...\n")
        proxy_display.see(tk.END)
        valid_proxies = []

        def check_proxy(proxy):
            try:
                response = requests.get(url, proxies={'http': proxy, 'https': proxy}, timeout=3)
                if response.status_code == 200:
                    valid_proxies.append(proxy)
                    proxy_display.insert(tk.END, f"Valid proxy: {proxy}\n" if language == "EN" else f"Proxy gültig: {proxy}\n")
                    proxy_display.see(tk.END)
                    logging.info(f"Valid proxy: {proxy}")
                else:
                    proxy_display.insert(tk.END, f"Invalid proxy: {proxy}\n" if language == "EN" else f"Proxy ungültig: {proxy}\n")
                    proxy_display.see(tk.END)
                    logging.warning(f"Invalid proxy: {proxy}")
            except Exception as e:
                proxy_display.insert(tk.END, f"Invalid proxy: {proxy} - Error: {e}\n" if language == "EN" else f"Proxy ungültig: {proxy} - Fehler: {e}\n")
                proxy_display.see(tk.END)
                logging.error(f"Invalid proxy: {proxy} - Error: {e}")

        with ThreadPoolExecutor(max_workers=100) as executor:
            executor.map(check_proxy, proxies)

        if not valid_proxies:
            proxy_display.insert(tk.END, "No valid proxies found.\n" if language == "EN" else "Keine gültigen Proxies gefunden.\n")
            proxy_display.see(tk.END)
        else:
            with open("valid_proxies.txt", "w") as file:
                for proxy in valid_proxies:
                    file.write(proxy + "\n")
            proxy_display.insert(tk.END, f"{len(valid_proxies)} valid proxies found.\n" if language == "EN" else f"{len(valid_proxies)} gültige Proxies gefunden.\n")
            proxy_display.see(tk.END)
        
        messagebox.showinfo("Proxy Check Completed" if language == "EN" else "Proxy-Überprüfung abgeschlossen", f"{len(valid_proxies)} valid proxies found." if language == "EN" else f"{len(valid_proxies)} gültige Proxies gefunden.")
        start_button.config(state=tk.NORMAL)

    threading.Thread(target=proxy_check).start()

def proxies_recently_checked():
    try:
        last_modified_time = os.path.getmtime("valid_proxies.txt")
        current_time = time.time()
        return (current_time - last_modified_time) < 300
    except FileNotFoundError:
        return False

def toggle_dark_mode(root, text_widgets, dark_mode):
    if dark_mode.get():
        root.config(bg='black')
        for widget in text_widgets:
            widget.config(bg='black', fg='white', insertbackground='white')
        for child in root.winfo_children():
            if isinstance(child, tk.Label) or isinstance(child, tk.Button) or isinstance(child, tk.Entry) or isinstance(child, Menu):
                child.config(bg='black', fg='white')
    else:
        root.config(bg='SystemButtonFace')
        for widget in text_widgets:
            widget.config(bg='white', fg='black', insertbackground='black')
        for child in root.winfo_children():
            if isinstance(child, tk.Label) or isinstance(child, tk.Button) or isinstance(child, tk.Entry) or isinstance(child, Menu):
                child.config(bg='SystemButtonFace', fg='black')

def create_gui():
    def on_start():
        url = url_entry.get()
        if not validate_url(url):
            messagebox.showerror("Error" if language.get() == "EN" else "Fehler", "Please enter a valid URL." if language.get() == "EN" else "Bitte geben Sie eine gültige URL ein.")
            return
        
        try:
            count = int(count_entry.get())
            on_start_thread(url, count, proxy_display)
        except ValueError:
            messagebox.showerror("Error" if language.get() == "EN" else "Fehler", "Please enter a valid number of windows." if language.get() == "EN" else "Bitte geben Sie eine gültige Anzahl von Fenstern ein.")
    
    def on_validate_proxies():
        url = url_entry.get()
        if not validate_url(url):
            messagebox.showerror("Error" if language.get() == "EN" else "Fehler", "Please enter a valid URL for proxy validation." if language.get() == "EN" else "Bitte geben Sie eine gültige URL zur Proxy-Überprüfung ein.")
            return
        start_button.config(state=tk.DISABLED)  # Deaktiviert den Start-Button
        validate_proxies(url, proxy_display, start_button, language.get())

    def open_proxies_file():
        subprocess.Popen(["notepad.exe", "proxies.txt"])

    def apply_settings():
        toggle_dark_mode(root, [proxy_display], dark_mode)
        messagebox.showinfo("Settings Applied" if language.get() == "EN" else "Einstellungen angewendet", "Settings have been applied." if language.get() == "EN" else "Die Einstellungen wurden angewendet.")

    # Einstellungen-Fenster
    def open_settings():
        settings_window = Toplevel(root)
        settings_window.title("Settings" if language.get() == "EN" else "Einstellungen")

        tk.Label(settings_window, text="Dark Mode:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        dark_mode_check = tk.Checkbutton(settings_window, variable=dark_mode)
        dark_mode_check.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        tk.Label(settings_window, text="Language:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        language_menu = tk.OptionMenu(settings_window, language, "EN", "DE")
        language_menu.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        save_button = tk.Button(settings_window, text="Save", command=apply_settings)
        save_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    root = tk.Tk()
    root.title("Proxy Browser Opener")

    dark_mode = tk.BooleanVar(value=False)
    language = tk.StringVar(value="DE")

    # Menüleiste hinzufügen
    menu_bar = Menu(root)
    settings_menu = Menu(menu_bar, tearoff=0)
    settings_menu.add_command(label="Open proxies.txt", command=open_proxies_file)
    settings_menu.add_command(label="Settings", command=open_settings)
    menu_bar.add_cascade(label="Options" if language.get() == "EN" else "Optionen", menu=settings_menu)
    root.config(menu=menu_bar)

    tk.Label(root, text="URL:").grid(row=0, column=0, padx=10, pady=5)
    url_entry = tk.Entry(root, width=50)
    url_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(root, text="Number of Windows:" if language.get() == "EN" else "Anzahl der Fenster:").grid(row=1, column=0, padx=10, pady=5)
    count_entry = tk.Entry(root, width=10)
    count_entry.grid(row=1, column=1, padx=10, pady=5)

    proxy_display = scrolledtext.ScrolledText(root, width=60, height=20)
    proxy_display.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    validate_button = tk.Button(root, text="Validate Proxies" if language.get() == "EN" else "Proxies Überprüfen", command=on_validate_proxies)
    validate_button.grid(row=3, column=0, padx=10, pady=10)

    start_button = tk.Button(root, text="Start", command=on_start, state=tk.DISABLED)
    start_button.grid(row=3, column=1, padx=10, pady=10)

    # Start-Button aktivieren, wenn Proxies in den letzten 5 Minuten überprüft wurden
    if proxies_recently_checked():
        start_button.config(state=tk.NORMAL)

    root.mainloop()

# Start der GUI
create_gui()
