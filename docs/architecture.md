# Architecture

Alur data end-to-end dari generasi data sintetis hingga dashboard BI.

```mermaid
flowchart LR
    subgraph GEN["1 · Data Generation"]
        A["generate_data.py<br/>Faker + logika bisnis"] --> B[("CSV<br/>data/raw/")]
    end

    subgraph OLTP["2 · OLTP Load + Cleaning"]
        B --> C["load_oltp.py<br/>dedup · fix tanggal · isi null"]
        C --> D[("Database OLTP<br/>SQLite / PostgreSQL")]
    end

    subgraph DWH["3 · Transform ke Warehouse"]
        D --> E["transform_dwh.py<br/>build dim & fact"]
        E --> F[("Star Schema DWH<br/>fact_sales · fact_inventory · dim_*")]
    end

    subgraph BI["4 · Analytics & Dashboard"]
        F --> G["SQL Analytics<br/>business_questions.sql"]
        F --> H["Streamlit + Plotly<br/>6 halaman dashboard"]
        F --> I["Power BI<br/>koneksi + DAX"]
    end

    G --> J["Insight Report<br/>10 insight + aksi"]
    H --> K["Owner / Manager<br/>Finance / Inventory"]
    I --> K
    J --> K
```

## Layer

| Layer | Tools | Output |
|-------|-------|--------|
| **Generation** | Python, Faker, NumPy | CSV realistis (Indonesia, fashion, musiman) |
| **OLTP** | pandas, SQLAlchemy | Database transaksional bersih |
| **Warehouse** | pandas, SQLAlchemy | Star schema siap analitik |
| **Analytics** | SQL | Jawaban 10 pertanyaan bisnis |
| **Dashboard** | Streamlit, Plotly, Power BI | 6 halaman interaktif |
| **Report** | Markdown | Insight + rekomendasi aksi |

## Orkestrasi
Seluruh pipeline dijalankan dengan satu perintah:
```bash
python etl/run_pipeline.py
```
yang menjalankan `generate_data`, `load_oltp`, lalu `transform_dwh` secara berurutan,
lengkap dengan log jumlah baris dan **rekonsiliasi revenue OLTP vs DWH**.
