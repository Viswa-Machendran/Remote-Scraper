import tkinter as tk
from tkinter import messagebox
import cloudscraper
from bs4 import BeautifulSoup
from openpyxl import Workbook
from datetime import datetime
import time
import threading
from tqdm import tqdm


# FIXED PARAMETERS
DELAY_PER_ISIN = 0.33
PAUSE_EVERY = 30
PAUSE_DURATION = 10


def scrape_funds_thread():
    btn_scrape.config(state=tk.DISABLED)

    input_text = entry_isins.get("1.0", "end").strip()
    if not input_text:
        messagebox.showwarning("Input needed", "Please enter one or more ISINs.")
        btn_scrape.config(state=tk.NORMAL)
        return

    raw_isins = input_text.replace(",", " ").split()
    target_isins = [isin.strip().upper() for isin in raw_isins if isin.strip()]

    variants = ["at", "de", "ch"]
    scraper = cloudscraper.create_scraper()
    results = {}

    print(f"\n🚀 Scraping {len(target_isins)} ISINs...\n")
    progress = tqdm(target_isins, desc="Scraping", unit="isin")

    for i, isin in enumerate(progress, 1):
        results[isin] = {}

        for variant in variants:
            fund_name = None
            url = f"https://www.fondsweb.com/{variant}/{isin}"

            try:
                response = scraper.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    h1 = soup.find("h1")
                    if h1:
                        text = h1.get_text(strip=True)
                        if "not available" not in text.lower():
                            fund_name = text

                results[isin][variant.upper()] = fund_name if fund_name else "Not found"

            except Exception as e:
                results[isin][variant.upper()] = f"Error: {e}"

        # Delay
        time.sleep(DELAY_PER_ISIN)

        # Controlled pause
        if i % PAUSE_EVERY == 0:
            print(f"⏸️ Pausing for {PAUSE_DURATION} sec after {i} ISINs...")
            time.sleep(PAUSE_DURATION)

    # Save to Excel
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Funds Data"

        ws.append(["ISIN", "AT Fund Name", "DE Fund Name", "CH Fund Name"])

        for isin in results:
            ws.append([
                isin,
                results[isin].get("AT", "Not found"),
                results[isin].get("DE", "Not found"),
                results[isin].get("CH", "Not found"),
            ])

        filename = f"fondsweb_fundnames_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(filename)

        messagebox.showinfo("Success", f"Saved: {filename}")

    except Exception as e:
        messagebox.showerror("Error", str(e))

    finally:
        btn_scrape.config(state=tk.NORMAL)


def scrape_funds():
    threading.Thread(target=scrape_funds_thread, daemon=True).start()


# ================= GUI =================
root = tk.Tk()
root.title("Fondsweb Scraper")
root.geometry("650x420")

# ISIN Input
tk.Label(root, text="Enter ISINs:").pack(pady=(10, 0))

entry_isins = tk.Text(root, height=10, width=70)
entry_isins.pack(pady=5)

# SETTINGS DISPLAY (FIXED)
frame_settings = tk.Frame(root)
frame_settings.pack(pady=10)

tk.Label(frame_settings, text="Delay per ISIN (sec):").grid(row=0, column=0, padx=10)
tk.Label(frame_settings, text=str(DELAY_PER_ISIN), fg="blue").grid(row=0, column=1)

tk.Label(frame_settings, text="Pause every (ISINs):").grid(row=0, column=2, padx=10)
tk.Label(frame_settings, text=str(PAUSE_EVERY), fg="blue").grid(row=0, column=3)

tk.Label(frame_settings, text="Pause duration (sec):").grid(row=0, column=4, padx=10)
tk.Label(frame_settings, text=str(PAUSE_DURATION), fg="blue").grid(row=0, column=5)

# Button
btn_scrape = tk.Button(root, text="Scrape Fund Names", command=scrape_funds)
btn_scrape.pack(pady=15)

root.mainloop()
