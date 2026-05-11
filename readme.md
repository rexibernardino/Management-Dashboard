# 📊 Streamlit Management Dashboard

A web-based dashboard application built with Streamlit to process and visualize financial transaction data (Fixed Income, Money Market, Spot, and Swap) directly from Google Sheets.

## 🚀 Key Features
- **Auto-Sync Google Drive**: Automatically pulls data from Google Sheets using a Service Account.
- **Login System**: Secure access using credentials stored in Streamlit Secrets.
- **Data Filtering**: Filter by a dynamic date range.
- **Interactive Visualization**: Horizontal bar charts using Plotly with sorting options (Ascending/Descending).
- **FX Combined View**: Feature to combine 'Spot' and 'Swap' category data into a single 'FX Total' view.
- **Data Explorer**: Raw table for reviewing processed data.

## 🛠️ Tech Stack

This project is built using the following technologies:
* Python: The primary programming language.
* Streamlit: A framework for interactive web dashboard interfaces.
* Pandas: Used for cleaning, manipulating, and analyzing tabular data.
* Plotly Express: A library for data visualization in the form of dynamic bar charts.
* Gspread & Google OAuth: For authentication and communication with the Google Sheets API.
* Google Sheets: Serves as a cloud database for storing transaction data.

---

## 📂 File Structure

This project's folder structure is designed to be modular and easy to manage:

```text
├── .streamlit/
│ └── secrets.toml      # Login credentials & GCP Service Account (Local only)
├── app.py              # Main files: UI logic, login, and period filter
├── data_processor.py   # Module: Data processing, cleaning, and Google Sheets API
├── visualizer.py       # Module: Plotly graphing logic
├── requirements.txt    # List of required Python libraries
├── .gitignore          # List of files that should not be uploaded (secrets.toml)
└── README.md           # Project documentation
```

---

## 🛠️ Installation

1. **Clone Repository**: 
```bash 
git clone https://github.com/rexibernardino/Management-Dashboard
```

2. **Install Library**: 
```bash 
pip install -r requirements.txt
```