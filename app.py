import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
from io import BytesIO  # ✅ REQUIRED FIX

# ================= FIXED PARAMETERS =================
DELAY_PER_ISIN = 0.33
PAUSE_EVERY = 30
PAUSE_DURATION = 10

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Fondsweb Scraper", layout="wide")

st.title("Fondsweb Fund Name Scraper")

# ================= INPUT =================
isins_text = st.text_area(
    "Enter ISINs (comma, space, or newline separated):",
    height=200,
    placeholder="LU1234567890\nIE00XXXXXXX\nCH0000000001"
)

# ================= SETTINGS DISPLAY =================
col1, col2, col3 = st.columns(3)
col1.metric("Delay per ISIN (sec)", DELAY_PER_ISIN)
col2.metric("Pause every (ISINs)", PAUSE_EVERY)
col3.metric("Pause duration (sec)", PAUSE_DURATION)

st.divider()

# ================= SCRAPER FUNCTION =================
def scrape(isins):
    scraper = cloudscraper.create_scraper()
    variants = ["at", "de", "ch"]

    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    total = len(isins)

    for i, isin in enumerate(isins, 1):
        row = {"ISIN": isin}

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

                row[variant.upper()] = fund_name if fund_name else "Not found"

            except Exception:
                row[variant.upper()] = "Error"

        results.append(row)

        # Progress UI
        progress_bar.progress(i / total)
        status_text.text(f"Processing {i}/{total} ISINs")

        # Delay
        time.sleep(DELAY_PER_ISIN)

        # Controlled pause
        if i % PAUSE_EVERY == 0:
            status_text.text(f"⏸️ Pausing for {PAUSE_DURATION} sec...")
            time.sleep(PAUSE_DURATION)

    progress_bar.empty()
    status_text.empty()

    return pd.DataFrame(results)


# ================= RUN BUTTON =================
if st.button("🚀 Run Scraper"):

    if not isins_text.strip():
        st.warning("Please enter ISINs.")
    else:
        raw = isins_text.replace(",", " ").split()
        isins = [x.strip().upper() for x in raw if x.strip()]

        st.info(f"Processing {len(isins)} ISINs...")

        df = scrape(isins)

        st.success("Scraping completed!")

        # ✅ Remove index from display
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ================= DOWNLOAD (FIXED) =================
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')  # ✅ NO INDEX
        output.seek(0)

        filename = f"fondsweb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        st.download_button(
            label="⬇ Download Excel",
            data=output,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # ✅ Optional CSV (fast + safe)
        st.download_button(
            label="⬇ Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="fondsweb.csv",
            mime="text/csv"
        )
