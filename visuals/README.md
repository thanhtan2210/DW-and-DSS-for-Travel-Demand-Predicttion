# Report Visuals

Curated diagrams and screenshots that accompany the project report.

## Layout

```
visuals/
├── architecture_diagram.png        # Hybrid ETL/ELT data-flow diagram
├── star_schema_erd.png             # Data Warehouse Star Schema (ERD)
├── ml_pipeline_diagram.png         # End-to-end ML pipeline diagram
├── null_clusters_heatmap.png       # EDA null-cluster diagnostic
├── diagrams/                       # Reserved for additional diagrams
├── eda/                            # Reserved for additional EDA exports
├── screenshots/                    # Streamlit / Power BI screenshots
└── sources/                        # Editable source files
    ├── architecture_diagram.mmd
    ├── star_schema_erd.mmd
    ├── ml_pipeline_diagram.mmd
    ├── generate_null_heatmap.py
    └── puppeteer-config.json
```

## Regenerating the diagrams

The three structural diagrams (`architecture`, `star_schema_erd`,
`ml_pipeline`) are authored as Mermaid (`*.mmd`) files and rendered with
[`@mermaid-js/mermaid-cli`](https://github.com/mermaid-js/mermaid-cli):

```bash
npm install -g @mermaid-js/mermaid-cli   # one-off

mmdc -i visuals/sources/architecture_diagram.mmd \
     -o visuals/architecture_diagram.png \
     -b white -w 1800 -s 2 \
     -p visuals/sources/puppeteer-config.json

mmdc -i visuals/sources/star_schema_erd.mmd \
     -o visuals/star_schema_erd.png \
     -b white -w 1800 -s 2 \
     -p visuals/sources/puppeteer-config.json

mmdc -i visuals/sources/ml_pipeline_diagram.mmd \
     -o visuals/ml_pipeline_diagram.png \
     -b white -w 2200 -s 2 \
     -p visuals/sources/puppeteer-config.json
```

`puppeteer-config.json` passes `--no-sandbox` to make rendering work inside
sandboxed Linux environments (CI, containers, dev VMs).

## Regenerating the null-cluster heatmap

```bash
pip install -r requirements.txt          # matplotlib, seaborn, pandas, polars
python visuals/sources/generate_null_heatmap.py
```

The generator first looks for raw parquet files under
`dataset/Trip_Record/<category>/`. When the raw data is unavailable, it falls
back to the **documented** null rates from `docs/EDA_Report.md` so the figure
remains reproducible from a clean clone.

The same logic is also exposed inside
[`notebooks/01_eda_raw_data.ipynb`](../notebooks/01_eda_raw_data.ipynb) so the
heatmap can be inspected interactively next to the rest of the EDA.

## Streamlit screenshots

Screenshots of the Streamlit DSS (`OLAP Dashboard`, `ML Predictor`,
`Model Performance`) belong under `visuals/screenshots/`. They require live
BigQuery credentials (`BQ_PROJECT_ID`, `BQ_DATASET_ID`, GCP application
default credentials) because the OLAP page reads `Fact_Demand_Hourly` on load.
After populating `.env`, run:

```bash
streamlit run app/main.py
```

…and capture the relevant tabs into `visuals/screenshots/`.
