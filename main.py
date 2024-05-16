import tkinter as tk
from tkinter import messagebox, scrolledtext
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import threading

# Funktion, um Geckodriver zu installieren
def ensure_geckodriver():
    driver_path = GeckoDriverManager().install()
    return driver_path

# Funktion, um den Webdriver mit Proxy zu starten
def start_with_proxy(proxy, url, proxy_display):
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
    service = Service(driver_path)
    driver = webdriver.Firefox(service=service, options=options)
    try:
        proxy_display.insert(tk.END, f"Verwende Proxy: {proxy}\n")
        proxy_display.see(tk.END)
        driver.get(url)
    except Exception as e:
        proxy_display.insert(tk.END, f"Fehler beim Zugriff auf die URL mit Proxy {proxy}: {e}\n")
        proxy_display.see(tk.END)
        driver.quit()

# Funktion, um die Proxy-Liste zu lesen
def proxy_list():
    proxies = []
    with open("proxies.txt", "r") as proxiesfile:
        for aline in proxiesfile.readlines():
            proxies.append(aline.strip())  # Zeilenumbruch entfernen und zur Liste hinzufügen
    return proxies

# Funktion, um die Proxies zu laden und Threads zu starten
def start_browsing(url, count, proxy_display):
    proxies = proxy_list()
    if len(proxies) == 0:
        messagebox.showerror("Fehler", "Die Proxy-Liste ist leer.")
        return

    threads = []
    for i in range(count):
        if i < len(proxies):
            proxy = proxies[i]
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

# GUI erstellen
def create_gui():
    def on_start():
        url = url_entry.get()
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

    root = tk.Tk()
    root.title("Website Opener + Proxy")

    tk.Label(root, text="URL (Format: https://www.example.com):").grid(row=0, column=0, padx=10, pady=5)
    url_entry = tk.Entry(root, width=50)
    url_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(root, text="Anzahl der Wiederholungen:").grid(row=1, column=0, padx=10, pady=5)
    count_entry = tk.Entry(root, width=10)
    count_entry.grid(row=1, column=1, padx=10, pady=5, sticky='w')

    start_button = tk.Button(root, text="Start", command=on_start)
    start_button.grid(row=2, columnspan=2, pady=10)

    proxy_display = scrolledtext.ScrolledText(root, width=80, height=20)
    proxy_display.grid(row=3, columnspan=2, padx=10, pady=10)

    root.mainloop()

# Starte die GUI
create_gui()
