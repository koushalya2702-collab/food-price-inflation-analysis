# Food Price Inflation Analysis

A Streamlit dashboard for exploring food-price records over time.

## Project structure

```text
food-price-inflation-analysis/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── data/
    └── food_prices.csv   # Add your dataset here; it is not included in this starter bundle.
```

## Run locally

1. Install Python (Python 3.11 or 3.12 is a safe choice for broad package compatibility).
2. Open a terminal in this project folder.
3. Create and activate a virtual environment (optional but recommended).
4. Install packages:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Put your dataset at `data/food_prices.csv`, or upload it in the app's sidebar.
6. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

## Deploy

Push `app.py`, `requirements.txt`, `README.md`, and the dataset (if its licence permits sharing) to GitHub. Then create a Streamlit Community Cloud app, choose the repository and `app.py` as the entry point, and deploy.

If the dataset is too large or cannot be shared publicly, do not commit it. Use the sidebar CSV uploader or a permitted data-hosting option instead.

## Important analysis note

The dashboard filters by commodity, unit, and price type before plotting the time series. It uses monthly median prices to reduce the influence of outliers. The percentage change shown is a change in the selected dataset's monthly median, not an official CPI inflation statistic.
