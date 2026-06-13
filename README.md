# CeneoScraper — Flask Web Application

## Description
A Flask web application that scrapes product reviews from Ceneo.pl (Poland's largest price-comparison website) and displays them with statistics and interactive charts. Built as an extra project for Computer Programming 2 course at Cracow University of Economics.

## Features
- Extract all opinions for any Ceneo.pl product by entering its product code
- Browse extracted products with summary statistics (opinion count, avg score, pros/cons count)
- View all opinions in a sortable and filterable table (DataTables)
- Visualize data with charts: pie chart (recommendation distribution) and bar chart (star ratings)
- Download opinions as CSV, XLSX or JSON

## Tech Stack
- Python 3 / Flask
- requests + BeautifulSoup4 — scraping
- pandas + openpyxl — data export
- Bootstrap 5 — UI
- DataTables — sortable/filterable tables
- Chart.js — charts

## How to Run
1. `pip install -r requirements.txt`
2. `python app.py`
3. Open `http://127.0.0.1:5000`

## Author
Mahir Şahin — Computer Science, Cracow University of Economics (UEK)
Computer Programming 2 (2025/2026) — Ph.D. Katarzyna Wójcik
