
from config.database import get_engine, get_env_data, get_price_data
from config import settings


def export_satellite_data(
        start_date="2023-01-01", 
        end_date="2026-01-01"
    ):

    """Export satellite data from PostgreSQL to CSV."""

    engine = get_engine()

    try:
        df = get_env_data(
            engine,
            start_date=start_date,
            end_date=end_date,
        )

        df.to_csv(
            settings.EXPORT_ENV_DATA_PATH, 
            index=False
        )

        print(f"Satellite records exported: {len(df):,}")
        print(f"CSV export: {settings.EXPORT_ENV_DATA_PATH}")

    finally:
        engine.dispose()


def export_price_data(
    start_date=None,
    end_date=None,
    market=None,
    products=None,
    price_type=None,
):
    """Export selected FEWS NET price records from PostgreSQL."""

    engine = get_engine()

    try:
        df = get_price_data(
            engine=engine,
            start_date=start_date,
            end_date=end_date,
            market=market,
            products=products,
            price_type=price_type,
        )

        df.to_csv(
            settings.EXPORT_PRICE_DATA_PATH, 
            index=False
        )

        print(f"Exported {len(df):,} price records.")
        print(f"Export location: {settings.EXPORT_PRICE_DATA_PATH}")

    finally:
        engine.dispose()

from pathlib import Path

from config import settings
from config.database import (
    get_engine,
    get_processed_features,
)


def export_processed_features(
    start_date=None,
    end_date=None,
    output_path=None,
):
    """Export processed features from PostgreSQL to CSV."""

    engine = get_engine()

    try:
        df = get_processed_features(
            engine=engine,
            start_date=start_date,
            end_date=end_date,
        )

        df.to_csv(
            settings.EXPORT_PROCESSED_DATA_PATH, 
            index=False
        )

        print(f"Exported {len(df):,} processed records.")
        print(f"Export location: {settings.EXPORT_PROCESSED_DATA_PATH}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    export_satellite_data()
    
    export_price_data(
        market=settings.TARGET_MARKET,
        products=list(settings.CROP_RENAME_MAP.keys()),
        price_type="Wholesale",
    )

    export_processed_features()

    