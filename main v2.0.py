import os
import subprocess
import sys

# Funktion, um fehlende Pakete zu installieren
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

    # Zusätzliche Installation für geckodriver_autoinstaller
    try:
        import geckodriver_autoinstaller
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "geckodriver-autoinstaller"])

install_missing_packages()

import tkinter as tk
from tkinter import messagebox, scrolledtext
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

# Logging konfigurieren
logging.basicConfig(filename='website_opener.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Funktion, um Geckodriver zu installieren
def ensure_geckodriver():
    driver_path = GeckoDriverManager().install()
    return driver_path

# Funktion, um den Webdriver mit Proxy zu starten
def start_with_proxy(proxy, url, proxy_display):
    try:
        prox = Proxy()
        prox.proxy_type = ProxyType.MANUAL
        prox.http_proxy = proxy
        prox.ssl_proxy = proxy

        # Geckodriver installieren
        driver_path = ensure_geckodriver()

        # Firefox-Optionen mit Proxy
        options = webdriver.FirefoxOptions()
        options.proxy = prox

        # Webdriver mit Proxy starten
        driver = webdriver.Firefox(options=options)
        URL = url
        driver.get(URL)
    except Exception as e:
            print(f"Fehler beim Zugriff auf die URL: {e}")
            driver.quit()

# Funktion, um die Proxy-Liste zu lesen
def proxy_list():
    proxies = []
    try:
        with open("proxies.txt", "r") as proxiesfile:
            for aline in proxiesfile.readlines():
                proxies.append(aline.strip())  # Zeilenumbruch entfernen und zur Liste hinzufügen
        if not proxies:
            raise ValueError("Die Proxy-Liste ist leer.")
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Proxy-Liste: {e}")
        messagebox.showerror("Fehler", f"Fehler beim Lesen der Proxy-Liste: {e}")
    return proxies

# Funktion, um die Proxies zu laden und Threads zu starten
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

# Funktion, um das Browsing in einem separaten Thread zu starten
def on_start_thread(url, count, proxy_display):
    threading.Thread(target=start_browsing, args=(url, count, proxy_display)).start()

# URL-Validierung
def validate_url(url):
    pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// oder https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # lokalhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...oder IPv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...oder IPv6
        r'(?::\d+)?'  # optionaler Port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(pattern, url) is not None

# Proxy-Validierung
def validate_proxies(proxy_display, start_button):
    def proxy_check():
        proxies = proxy_list()
        if len(proxies) == 0:
            messagebox.showerror("Fehler", "Die Proxy-Liste ist leer.")
            return

        proxy_display.insert(tk.END, "Überprüfung der Proxies gestartet...\n")
        proxy_display.see(tk.END)
        valid_proxies = []

        def check_proxy(proxy):
            try:
                response = requests.get('http://www.google.com', proxies={'http': proxy, 'https': proxy}, timeout=5)
                if response.status_code == 200:
                    valid_proxies.append(proxy)
                    proxy_display.insert(tk.END, f"Proxy gültig: {proxy}\n")
                    proxy_display.see(tk.END)
                    logging.info(f"Proxy gültig: {proxy}")
                else:
                    proxy_display.insert(tk.END, f"Proxy ungültig: {proxy}\n")
                    proxy_display.see(tk.END)
                    logging.warning(f"Proxy ungültig: {proxy}")
            except Exception as e:
                proxy_display.insert(tk.END, f"Proxy ungültig: {proxy} - Fehler: {e}\n")
                proxy_display.see(tk.END)
                logging.error(f"Proxy ungültig: {proxy} - Fehler: {e}")

        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(check_proxy, proxies)

        if not valid_proxies:
            proxy_display.insert(tk.END, "Keine gültigen Proxies gefunden.\n")
            proxy_display.see(tk.END)
        else:
            with open("valid_proxies.txt", "w") as file:
                for proxy in valid_proxies:
                    file.write(proxy + "\n")
            proxy_display.insert(tk.END, f"{len(valid_proxies)} gültige Proxies gefunden.\n")
            proxy_display.see(tk.END)
        
        messagebox.showinfo("Proxy-Überprüfung abgeschlossen", f"{len(valid_proxies)} gültige Proxies gefunden.")
        start_button.config(state=tk.NORMAL)  # Aktiviert den Start-Button

    threading.Thread(target=proxy_check).start()

# GUI erstellen
def create_gui():
    def on_start():
        url = url_entry.get()
        if not validate_url(url):
            messagebox.showerror("Fehler", "Bitte geben Sie eine gültige URL ein.")
            return
        
        try:
            count = int(count_entry.get())
            if count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Fehler", "Bitte geben Sie eine gültige Anzahl an.")
            return

        proxy_display.delete(1.0, tk.END)  # Clear the proxy display box
        messagebox.showinfo("Hinweis", "Das Öffnen der Browser-Fenster kann etwas dauern. Bitte haben Sie Geduld.")
        on_start_thread(url, count, proxy_display)
    
    def on_validate_proxies():
        proxy_display.delete(1.0, tk.END)  # Clear the proxy display box
        validate_proxies(proxy_display, start_button)

    root = tk.Tk()
    root.title("Website Opener + Proxy")

    tk.Label(root, text="URL (Format: https://www.example.com):").grid(row=0, column=0, padx=10, pady=5)
    url_entry = tk.Entry(root, width=50)
    url_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(root, text="Anzahl der Wiederholungen:").grid(row=1, column=0, padx=10, pady=5)
    count_entry = tk.Entry(root, width=10)
    count_entry.grid(row=1, column=1, padx=10, pady=5)

    proxy_display = scrolledtext.ScrolledText(root, width=80, height=20)
    proxy_display.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    validate_button = tk.Button(root, text="Proxies überprüfen", command=on_validate_proxies)
    validate_button.grid(row=3, column=0, padx=10, pady=10)

    start_button = tk.Button(root, text="Starten", command=on_start)
    start_button.grid(row=3, column=1, padx=10, pady=10)

    root.mainloop()

# Start der GUI
create_gui()