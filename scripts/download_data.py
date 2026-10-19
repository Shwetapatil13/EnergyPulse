"""
download_data.py
----------------
Downloads the UCI Individual Household Electric Power Consumption dataset.

Strategy (in order):
  1. Direct ZIP download from UCI ML Repository static URL
  2. ucimlrepo package (id=235)
  3. Print manual-download instructions

Usage:
    python scripts/download_data.py
"""

import os
import sys
import zipfile
import pathlib
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

RAW_DIR = pathlib.Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

ZIP_URL = (
    "https://archive.ics.uci.edu/static/public/235/"
    "individual+household+electric+power+consumption.zip"
)
ZIP_PATH = RAW_DIR / "household_power_consumption.zip"
EXPECTED_CSV = RAW_DIR / "household_power_consumption.txt"


def already_downloaded() -> bool:
    """Check if data is already present."""
    if EXPECTED_CSV.exists() and EXPECTED_CSV.stat().st_size > 1_000_000:
        log.info("Dataset already present at %s — skipping download.", EXPECTED_CSV)
        return True
    return False


def download_via_requests() -> bool:
    """Try downloading via requests with progress."""
    try:
        import requests  # type: ignore
    except ImportError:
        log.warning("requests not installed — skipping direct download.")
        return False

    log.info("Attempting direct download from UCI repository…")
    try:
        with requests.get(ZIP_URL, stream=True, timeout=120) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(ZIP_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r  {pct:5.1f}%  {downloaded/1e6:.1f} MB / {total/1e6:.1f} MB", end="")
        print()
        log.info("Download complete → %s", ZIP_PATH)
        return True
    except Exception as exc:
        log.warning("Direct download failed: %s", exc)
        if ZIP_PATH.exists():
            ZIP_PATH.unlink()
        return False


def download_via_urllib() -> bool:
    """Fallback using stdlib urllib."""
    import urllib.request

    log.info("Attempting urllib download…")
    try:
        def reporthook(count, block_size, total_size):
            if total_size > 0:
                pct = count * block_size / total_size * 100
                print(f"\r  {min(pct, 100):5.1f}%", end="")

        urllib.request.urlretrieve(ZIP_URL, ZIP_PATH, reporthook)
        print()
        log.info("urllib download complete.")
        return True
    except Exception as exc:
        log.warning("urllib download failed: %s", exc)
        if ZIP_PATH.exists():
            ZIP_PATH.unlink()
        return False


def download_via_ucimlrepo() -> bool:
    """Fallback: use ucimlrepo package."""
    try:
        from ucimlrepo import fetch_ucirepo  # type: ignore
    except ImportError:
        log.info("ucimlrepo not installed — trying pip install…")
        os.system(f"{sys.executable} -m pip install ucimlrepo -q")
        try:
            from ucimlrepo import fetch_ucirepo  # type: ignore
        except ImportError:
            log.error("Cannot install ucimlrepo.")
            return False

    log.info("Fetching dataset via ucimlrepo (id=235) — this may take several minutes…")
    try:
        dataset = fetch_ucirepo(id=235)
        import pandas as pd

        df_features = dataset.data.features
        df_targets = dataset.data.targets

        if df_targets is not None and not df_targets.empty:
            df = pd.concat([df_features, df_targets], axis=1)
        else:
            df = df_features

        out_path = RAW_DIR / "household_power_consumption.txt"
        df.to_csv(out_path, sep=";", index=False)
        log.info("Saved %d rows via ucimlrepo → %s", len(df), out_path)
        return True
    except Exception as exc:
        log.error("ucimlrepo fetch failed: %s", exc)
        return False


def unzip() -> bool:
    """Unzip the downloaded archive into data/raw/."""
    if not ZIP_PATH.exists():
        return False
    log.info("Unzipping %s …", ZIP_PATH)
    try:
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            zf.extractall(RAW_DIR)
        log.info("Extraction complete. Contents: %s", list(RAW_DIR.iterdir()))
        return True
    except zipfile.BadZipFile as exc:
        log.error("Bad zip file: %s", exc)
        return False


def print_manual_instructions():
    print("\n" + "=" * 60)
    print("MANUAL DOWNLOAD REQUIRED")
    print("=" * 60)
    print(
        "All automated download methods failed.\n"
        "Please:\n"
        "  1. Open in your browser:\n"
        "     https://archive.ics.uci.edu/dataset/235/\n"
        "         individual+household+electric+power+consumption\n"
        "  2. Click 'Download' to get the ZIP file.\n"
        "  3. Extract 'household_power_consumption.txt' into:\n"
        f"     {RAW_DIR.resolve()}\n"
        "  4. Re-run this script to verify."
    )
    print("=" * 60)


def verify() -> bool:
    """Verify the dataset file looks valid."""
    candidates = list(RAW_DIR.glob("*.txt")) + list(RAW_DIR.glob("*.csv"))
    if not candidates:
        return False
    for p in candidates:
        if p.stat().st_size > 1_000_000:
            log.info("✓ Dataset file found: %s (%.1f MB)", p.name, p.stat().st_size / 1e6)
            return True
    return False


def main():
    if already_downloaded():
        return

    success = (
        (download_via_requests() or download_via_urllib()) and unzip()
    ) or download_via_ucimlrepo()

    if not success or not verify():
        print_manual_instructions()
        sys.exit(1)

    log.info("✓ Dataset ready in %s", RAW_DIR.resolve())


if __name__ == "__main__":
    main()
