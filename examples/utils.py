import polars as pl


def read_test_data() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Read test data from parquet files

    Returns:
        tuple containing:
            - close_df: DataFrame with time and close price columns
            - position_df: DataFrame with time and position columns
    """
    # Read raw data from parquet file
    df = pl.read_parquet("data/BTCUSDT-SWAP_15m.parquet")

    # Process close price data
    close_df = (
        df.select(pl.col("Time"), pl.col("close"))
        .rename({"Time": "time"})  # Rename Time column to lowercase
        .with_columns(
            pl.col("time").cast(pl.Datetime("ms"))
        )  # Convert time to datetime
    )

    # Process position data
    position_df = (
        df.select(pl.col("Time"), pl.col("position"))
        .rename({"Time": "time"})  # Rename Time column to lowercase
        .with_columns(
            pl.col("time").cast(pl.Datetime("ms"))
        )  # Convert time to datetime
    )

    return close_df, position_df
