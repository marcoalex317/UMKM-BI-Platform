"""
run_pipeline.py
===============
Orchestrator ETL end-to-end:
    1. generate_data  -> CSV synthetic dataset di data/raw/
    2. load_oltp      -> muat & bersihkan CSV ke database OLTP
    3. transform_dwh  -> bangun star schema data warehouse

Jalankan:
    python etl/run_pipeline.py            # full pipeline
    python etl/run_pipeline.py --skip-generate   # pakai CSV yang sudah ada

Database ditentukan oleh .env (DB_ENGINE=sqlite default, atau postgres).
"""
from __future__ import annotations

import argparse
import time

import config as cfg
import generate_data
import load_oltp
import transform_dwh


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL pipeline UMKM BI Platform")
    parser.add_argument("--skip-generate", action="store_true",
                        help="Lewati generate CSV, pakai data/raw yang ada")
    args = parser.parse_args()

    t0 = time.time()
    print("=" * 64)
    print(f"  ETL PIPELINE - {cfg.COMPANY_NAME}")
    print(f"  Target DB : {cfg.engine_label()}")
    print("=" * 64)

    if not args.skip_generate:
        print("\n[1/3] GENERATE synthetic data")
        generate_data.main()
    else:
        print("\n[1/3] GENERATE dilewati (--skip-generate)")

    print("\n[2/3] LOAD ke OLTP")
    load_oltp.load()

    print("\n[3/3] TRANSFORM ke Data Warehouse")
    transform_dwh.transform()

    print("\n" + "=" * 64)
    print(f"  PIPELINE SELESAI dalam {time.time() - t0:,.1f} detik.")
    print("  Jalankan dashboard: streamlit run dashboard/streamlit_app.py")
    print("=" * 64)


if __name__ == "__main__":
    main()
