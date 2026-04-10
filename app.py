import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
from io import BytesIO

# ================= FIXED PARAMETERS =================
DELAY_PER_ISIN = 0.33
PAUSE_EVERY = 30
PAUSE_DURATION = 10

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Fondsweb Scraper", layout="wide")

st.title("Fondsweb Fund Name Scraper")

# ================= INPUT =================
isins_text = st.text_area(
    "Enter ISINs:",
    height=200,
    placeholder="LU1234567890\nIE00XXXXXXX\nCH0000000001"
)

# ================= SETTINGS =================
col1, col2, col3 = st.columns(3)
col1.metric("Delay", DELAY_PER_ISIN)
col2.metric("Pause Every", PAUSE_EVERY)
col3.metric("Pause Duration", PAUSE_DURATION)

st.divider()

# ================= SCRAPER =================
def scrape(isins):
    scraper = cloudscraper.create_scraper()
    variants = ["AT", "DE", "CH"]

    results = {}
    logs = []

    progress_bar = st.progress(0)
    status = st.empty()
    log_box = st.empty()

    total = len(isins)

    for i, isin in enumerate(isins, 1):
        results[isin] = {}
        log_line = f"🔍 {isin} → "

        for variant in variants:
            url = f"https://www.fondsweb.com/{variant.lower()}/{isin}"

            try:
                response = scraper.get(url)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    h1 = soup.find("h1")

                    if h1:
                        text = h1.get_text(strip=True)
                        if "not available" not in text.lower():
                            results[isin][variant] = text
                            continue

                results[isin][variant] = "Not found"

            except Exception as e:
                results[isin][variant] = f"Error: {str(e)}"

        log_line += f"AT | DE | CH done"
        logs.append(log_line)

        # UI updates
        progress_bar.progress(i / total)
        status.text(f"Processing {i}/{total}")

        log_box.text("\n".join(logs[-15:]))  # last 15 logs

        # Delay
        time.sleep(DELAY_PER_ISIN)

        # Pause logic
        if i % PAUSE_EVERY == 0:
            pause_msg = f"⏸️ Pausing {PAUSE_DURATION}s after {i} ISINs"
            logs.append(pause_msg)
            log_box.text("\n".join(logs[-15:]))
            status.text(pause_msg)
            time.sleep(PAUSE_DURATION)

    progress_bar.empty()
    status.empty()

    # Convert to DataFrame
    rows = []
    for isin in results:
        rows.append({
            "ISIN": isin,
            "AT": results[isin].get("AT", "Not found"),
            "DE": results[isin].get("DE", "Not found"),
            "CH": results[isin].get("CH", "Not found"),
        })

    return pd.DataFrame(rows), logs


# ================= RUN =================
if st.button("🚀 Run Scraper"):

    if not isins_text.strip():
        st.warning("Enter ISINs.")
    else:
        raw = isins_text.replace(",", " ").split()
        isins = [x.strip().upper() for x in raw if x.strip()]

        st.info(f"Processing {len(isins)} ISINs...")

        df, logs = scrape(isins)

        st.success("Done!")

        # ================= METRICS =================
        total = len(df)
        not_found = (df[["AT","DE","CH"]] == "Not found").sum().sum()
        errors = df.apply(lambda row: row.astype(str).str.contains("Error").any(), axis=1).sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Total ISINs", total)
        m2.metric("Errors", errors)
        m3.metric("Not Found Cells", not_found)

        # ================= DATA =================
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ================= DOWNLOAD =================
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            "⬇ Download Excel",
            data=output,
            file_name=f"fondsweb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # ================= FULL LOG =================
        with st.expander("📜 Full Logs"):
            st.text("\n".join(logs))
