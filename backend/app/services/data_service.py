from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"


def load_tickets() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "tickets.csv")


def load_agents() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "agents.csv")


def load_customers() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "customers.csv")


def load_orders() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "orders.csv")


def load_products() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "products.csv")