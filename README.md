# ComicBase Collection Dashboard

A Power BI analytics dashboard built on top of a ComicBase Archive Edition 
database export, featuring a Python-based publisher enrichment pipeline.

## Overview

ComicBase is a long-standing comic book collection management system. While 
it includes built-in reporting, this project extends it with custom analytics 
using Power BI and a Python enrichment process to fill data gaps.

## Features

- Multi-page Power BI dashboard covering:
  - CGC/Graded book summary with values and cost analysis
  - Title and publisher analysis across 27,000+ issues
  - Selling research with value trend tracking
  - Year-over-year price change analysis
- Python pipeline to classify and enrich publisher data
- Handles ~28,000 comic records
- Dynamic visuals with slicers for Grade, Publisher, Title Group, GN Flag, and Value Trend

## Tech Stack

- **ComicBase Archive Edition 2026** — source data
- **Python** — publisher classification and data enrichment
- **Power BI Desktop** — dashboard and analytics
- **Claude Cowork** — AI-assisted bulk data enrichment
- **JSON** — publisher mapping reference

## Data Pipeline

1. Export collection data from ComicBase as CSV
2. Run `comic_publisher_classify.py` to enrich publisher data
3. Load enriched CSV into Power BI
4. Refresh dashboard

## Publisher Enrichment Process

The ComicBase export contains missing or inconsistent publisher data for 
a subset of records. The enrichment pipeline:

- Takes the raw CSV export from ComicBase
- References `publisher_map.json` for known publisher mappings
- Classifies unknown publishers using title matching logic
- Outputs an enriched CSV and a separate file of unresolved records
- Provides a review tool for manual resolution of edge cases

## Dashboard Pages

### CGC Summary
Graded book inventory with cost vs. current value analysis, top valuable 
slabs, and KPI cards for total graded value, cost, gain/loss, and count.

![CGC Summary](Screenshots/cgc_summary.png)

### Title Analysis
Collection breakdown by title group (Spider-Man, X-Books, Avengers, etc.), 
issue counts, total value, and dynamic donut chart toggling between 
issue count and price sum.

![Title Analysis](Screenshots/title_analysis.png)

### Research Titles To Sell
Selling research tool with value trend filtering, % price change year over 
year, publisher treemap, and GN/Single Issue filtering.

![Selling Research](Screenshots/selling_research.png)

### Titles by Trend and Change %
Year-over-year value change analysis showing biggest movers with 
prior year vs. current year pricing.

![Trend Analysis](Screenshots/trend_analysis.png)

## Keeping It Fresh

One of the best parts of this setup is that it's fully refreshable — 
your dashboard stays current whenever you want it to.

Here's all it takes:

1. Export a fresh CSV from ComicBase via File > Export
2. Re-run the publisher enrichment through Claude Cowork 
   (it'll update new records, flag anything it can't resolve, 
   and give you a tool to fix edge cases)
3. Hit Refresh in Power BI

That's it! New books you've added, updated prices, grade changes — 
everything flows through automatically. The whole process takes 
just a few minutes once it's set up.

## Initial Setup

1. Export your ComicBase collection to CSV via File > Export
2. Place the CSV in your project folder
3. Run the enrichment script:
   ```
   python comic_publisher_classify.py
   ```
4. Open `ComicBase Collection Dashboard.pbix` in Power BI Desktop
5. Update the data source path to point to your enriched CSV
6. Refresh

## Notes

- ComicBase 2026 uses a compressed proprietary format — direct SQLite 
  access is not available in this version
- Publisher data quality varies in ComicBase exports — the enrichment 
  pipeline addresses the most common gaps
- Pricing data comes from ComicBase's built-in price guide and may 
  not reflect current market values for all books

## Screenshots

See the `/screenshots` folder for dashboard previews.

## Author

Jamie Tarquini | [pmpknface.com](https://pmpknface.com) | 
[GitHub](https://github.com/pmpknface-jamie-t)
