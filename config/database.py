import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config.secrets import DB_CONFIG

# SQLAlchemy Connection Engine
DATABASE_URI = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)


def get_engine() -> Engine:
    """Create and return the SQLAlchemy database engine."""
    return create_engine(DATABASE_URI)

# ============================================================
# RAW SATELLITE DATA
# ============================================================

def get_latest_satellite_month(engine: Engine) -> pd.Timestamp:
    """
    Return the next month after the latest satellite observation.

    Start form January 2017 if the table contains no records.
    """

    query = text("""
        SELECT MAX(period_start)
        FROM raw_env_data
    """)
    
    with engine.connect() as connection:
        latest_date = connection.execute(query).scalar()

    if latest_date is None:
        return pd.Timestamp("2017-01-01")

    latest_date = pd.Timestamp(latest_date)

    return (
        latest_date.to_period("M").to_timestamp()
        + pd.offsets.MonthBegin(1)
    )


def get_env_data(engine: Engine, start_date=None, end_date=None) -> pd.DataFrame:
    """Fetch raw satellite-derived environmental data, optionally filtered by date range."""

    # query = text("""
    #     SELECT * 
    #     FROM raw_env_data
    #     ORDER BY period_start
    # """)

    query = text("""
        SELECT *
        FROM raw_env_data
        WHERE (:start_date IS NULL OR period_start >= :start_date)
          AND (:end_date IS NULL OR period_start <= :end_date)
        ORDER BY period_start, "LGA_NAME"
    """)

    params = {
        "start_date": start_date,
        "end_date": end_date
    }

    with engine.connect() as connection:
        df = pd.read_sql(query, connection, params=params)

    if df.empty:
        raise ValueError("'raw_env_data' contains no records for the requested date range.")

    return df


def save_satellite_data(df: pd.DataFrame, engine: Engine) -> None:
    """
    Insert satellite observations or update existing LGA-month records.

    Requires a unique constraint or index on
    (period_start, LGA_NAME).
    """

    if df.empty:
        print("No new satellite data to save.")
        return

    required_columns = [
        "period_start", 
        "LGA_NAME", 
        "NDVI", 
        "NDMI", 
        "Rainfall",
    ]

    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Satellite data is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    df = df[required_columns].copy()
    df["period_start"] = pd.to_datetime(df["period_start"]).dt.date

    if df["LGA_NAME"].isna().any():
        raise ValueError("LGA_NAME cannot contain missing values.")

    if df.duplicated(["period_start", "LGA_NAME"]).any():
        raise ValueError("Duplicate LGA-month records detected.")

    # PostgreSQL upsert: insert new records or update matching records.
    query = text("""
        INSERT INTO raw_env_data (
            period_start,
            "LGA_NAME",
            "NDVI",
            "NDMI",
            "Rainfall"
        )
        VALUES (
            :period_start,
            :LGA_NAME,
            :NDVI,
            :NDMI,
            :Rainfall
        )
        ON CONFLICT (period_start, "LGA_NAME")
        DO UPDATE SET
            "NDVI" = EXCLUDED."NDVI",
            "NDMI" = EXCLUDED."NDMI",
            "Rainfall" = EXCLUDED."Rainfall"
    """)

    records = (
        df.astype(object)
        .where(pd.notna(df), None)
        .to_dict(orient="records")
    )

    with engine.begin() as connection:
        connection.execute(query, records)

    print(f"Saved {len(df)} satellite records to PostgreSQL.")


# ============================================================
# RAW MARKET-PRICE DATA
# ============================================================

from sqlalchemy import text
from sqlalchemy.engine import Engine
import pandas as pd


def get_price_data(
    engine: Engine,
    start_date=None,
    end_date=None,
    market=None,
    products=None,
    price_type=None,
) -> pd.DataFrame:
    """Fetch raw market-price data with optional filters."""

    conditions = []
    params = {}

    if start_date is not None:
        conditions.append("period_date >= :start_date")
        params["start_date"] = start_date

    if end_date is not None:
        conditions.append("period_date < :end_date_exclusive")
        params["end_date_exclusive"] = (
            pd.Timestamp(end_date) + pd.Timedelta(days=1)
        )

    if market is not None:
        conditions.append("market = :market")
        params["market"] = market

    if products is not None:
        if not products:
            raise ValueError("'products' cannot be an empty list.")

        conditions.append("product IN :products")
        params["products"] = tuple(products)

    if price_type is not None:
        conditions.append("price_type = :price_type")
        params["price_type"] = price_type

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    query = text(f"""
        SELECT *
        FROM raw_fewsnet_prices
        {where_clause}
        ORDER BY period_date
    """)

    # SQLAlchemy requires expanding bind parameters for IN clauses.
    if products is not None:
        query = query.bindparams(
            __import__("sqlalchemy").bindparam(
                "products",
                expanding=True,
            )
        )

    with engine.connect() as connection:
        df = pd.read_sql(query, connection, params=params)

    if df.empty:
        raise ValueError(
            "No records found in 'raw_fewsnet_prices' "
            "for the requested filters."
        )

    return df

# def get_price_data(engine: Engine) -> pd.DataFrame:
#     """Fetch raw market-price data."""

#     query = text("""
#         SELECT *
#         FROM raw_fewsnet_prices
#     """)

#     with engine.connect() as connection:
#         df = pd.read_sql(query, connection)

#     if df.empty:
#         raise ValueError("'raw_fewsnet_prices' contains no records.")

#     return df

# ============================================================
# GEOGRAPHIC DATA
# ============================================================

def get_lga_map_data(engine: Engine) -> gpd.GeoDataFrame:
    """Fetch Kano LGA boundaries from PostGIS as a GeoDataFrame."""

    query = text("""
        SELECT name_2 AS lga_name, geom
        FROM lga_map_data
        WHERE name_1 = 'Kano'
    """)

    try:
        gdf = gpd.read_postgis(
            query, 
            con=engine, 
            geom_col='geom',
        )
    except Exception as exc:
        raise RuntimeError(
            "Failed to load Kano LGA boundaries from PostGIS."
        )from exc

    if gdf.empty:
        raise ValueError("No Kano LGA boundaries wre found.")

    # Ensure CRS is WGS84 (required for Plotly)
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    else:
        gdf = gdf.to_crs(epsg=4326)

    return gdf

# ============================================================
# PROCESSED FEATURES
# ============================================================

from sqlalchemy import text
import pandas as pd


def get_processed_features(
    engine,
    start_date=None,
    end_date=None,
) -> pd.DataFrame:
    """Fetch processed features from PostgreSQL, optionally filtered by date."""

    conditions = []
    params = {}

    if start_date is not None:
        conditions.append('"Date" >= :start_date')
        params["start_date"] = start_date

    if end_date is not None:
        conditions.append('"Date" < :end_date_exclusive')
        params["end_date_exclusive"] = (
            pd.Timestamp(end_date) + pd.Timedelta(days=1)
        )

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    query = text(f"""
        SELECT *
        FROM processed_features
        {where_clause}
        ORDER BY "Date"
    """)

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
            params=params,
        )

    if df.empty:
        raise ValueError(
            "No records found in 'processed_features' "
            "for the requested date range."
        )

    return df

# def get_processed_features(engine: Engine) -> pd.DataFrame:
#     """Fetch engineered features stored in PostgreSQL."""

#     query = text("""
#         SELECT *
#         FROM processed_features
#         ORDER BY "Date"
#     """)

#     with engine.connect() as connection:
#         df = pd.read_sql(query, connection)

    
#     if df.empty:
#         raise ValueError("'processed_features' contains no records.")

#     return df

# ============================================================
# MODEL PREDICTIONS
# ============================================================

def save_predictions(engine: Engine, df: pd.DataFrame) -> None:
    """Append model predictions to the predictions table."""
    if df.empty:
        print("No predictions to save.")
        return

    try:
        df.to_sql(
            name="predictions",
            con=engine,
            if_exists="append",
            index=False,
            method="multi",
        )
    except Exception as exc:
        raise RuntimeError(
            "Failed to save model predictions to PostgreSQL."
        ) from exc