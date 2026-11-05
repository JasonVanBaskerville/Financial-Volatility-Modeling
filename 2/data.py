"""Data access layer for Project 8 — Volatility Forecasting.

This module provides two main classes and one helper function
that together form the data pipeline for the volatility
forecasting system built across Lessons 1 through 4.

Overview
--------
In Lesson 1, students create the ``wrangle_data`` function,
which fetches daily stock prices from the AlphaVantage API
(intercepted locally by ``mock_alpha``), parses the JSON
response into a pandas DataFrame, computes percentage returns,
and returns the most recent *n* observations as a
``pd.Series``.

In Lesson 2, students add two classes to this module:

- ``AlphaVantageAPI`` — a thin wrapper around the
  AlphaVantage REST API that builds the request URL,
  sends an HTTP GET via ``requests.get``, and converts
  the JSON response into a clean DataFrame with columns
  ``["open", "high", "low", "close", "volume"]``, a
  ``DatetimeIndex`` named ``"date"``, and all-float dtypes.

- ``SQLRepository`` — a persistence layer that writes
  DataFrames into a SQLite database and reads them back.
  This decouples downstream code from the API: once data
  is stored locally, it can be reloaded instantly without
  network access.

Both classes are tested incrementally using ``assert``
statements (test-driven development) before being moved
into this file.

In Lessons 3 and 4, these components are imported and
used directly — no re-implementation needed.

Classes
-------
AlphaVantageAPI
    Fetches daily OHLCV stock data from the AlphaVantage
    API and returns it as a pandas DataFrame.

    Attributes
    ----------
    __api_key : str
        The API key used for authentication. Stored as a
        private attribute. For this project any placeholder
        string (e.g., ``"demo"``) works because the mock
        intercepts all requests.

    Methods
    -------
    get_daily(ticker, output_size="full")
        Build the AlphaVantage URL for the
        ``TIME_SERIES_DAILY`` endpoint, call
        ``requests.get``, parse the JSON response, and
        return a DataFrame with:

        - Columns: ``["open", "high", "low", "close",
          "volume"]`` (all ``float64``).
        - Index: ``DatetimeIndex`` named ``"date"``.

        Parameters
        ----------
        ticker : str
            The stock ticker symbol
            (e.g., ``"AMBUJACEM.BSE"``).
        output_size : str, optional
            ``"full"`` for the entire history or
            ``"compact"`` for the latest 100 observations.
            Default is ``"full"``.

        Returns
        -------
        pd.DataFrame
            Cleaned OHLCV data.

SQLRepository
    Reads from and writes to a SQLite database using
    ``pandas`` and ``sqlite3``.

    Attributes
    ----------
    connection : sqlite3.Connection
        An open SQLite database connection, passed in at
        construction time.

    Methods
    -------
    insert_table(table_name, records, if_exists="fail")
        Write a DataFrame into the database as a table.

        Parameters
        ----------
        table_name : str
            Name of the target table.
        records : pd.DataFrame
            The data to insert.
        if_exists : str, optional
            What to do if the table already exists.
            Accepts ``"fail"``, ``"replace"``, or
            ``"append"``. Default is ``"fail"``.

        Returns
        -------
        dict
            ``{"transaction_successful": bool,
            "records_inserted": int}``

    read_table(table_name, limit=None)
        Read a table from the database into a DataFrame.

        Parameters
        ----------
        table_name : str
            Name of the table to read.
        limit : int or None, optional
            Maximum number of rows to return. ``None``
            returns all rows. Default is ``None``.

        Returns
        -------
        pd.DataFrame
            Data with a ``DatetimeIndex`` named ``"date"``
            and all-float columns.

Functions
---------
wrangle_data(ticker, n_observations)
    Fetch daily prices from the AlphaVantage API (or the
    local mock) and return daily percentage returns as a
    ``pd.Series``.

    This is the first function students build in Lesson 1.
    It encapsulates the full fetch-parse-compute pipeline:

    1. Build the API URL with ``outputsize="full"``.
    2. Call ``requests.get`` (intercepted by the mock).
    3. Extract ``"Time Series (Daily)"`` from the JSON.
    4. Parse into a DataFrame, keep the ``"4. close"``
       column, cast to float.
    5. Sort ascending by date.
    6. Compute percentage returns with
       ``pct_change() * 100``.
    7. Drop the leading ``NaN`` and keep the most recent
       ``n_observations`` values.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol (e.g., ``"AMBUJACEM.BSE"``).
    n_observations : int
        Number of return observations to keep (most
        recent).

    Returns
    -------
    pd.Series
        Named ``"return"``, with a ``DatetimeIndex``
        sorted ascending and no ``NaN`` values.

Notes
-----
- The ``mock_alpha`` module must be activated
  (``activate_mock()``) before any function or method
  in this module calls ``requests.get``. Otherwise a
  real HTTP request will be sent, which will fail
  without a valid API key and network access.

- Students build each component inside the notebook
  first (with ``assert`` tests), then move the working
  code into this file. The recommended workflow in
  subsequent lessons is::

      %load_ext autoreload
      %autoreload 2
      from data import AlphaVantageAPI, SQLRepository

  This ensures that edits to ``data.py`` are picked up
  automatically without restarting the kernel.

Examples
--------
>>> from mock_alpha import activate_mock, deactivate_mock
>>> from data import wrangle_data
>>> activate_mock()
>>> returns = wrangle_data("AMBUJACEM.BSE", 2500)
>>> print(type(returns), len(returns))
<class 'pandas.core.series.Series'> 2500
>>> deactivate_mock()
"""

from __future__ import annotations

import sqlite3

import pandas as pd
import requests


class AlphaVantageAPI:
    """Fetch daily OHLCV data from the AlphaVantage API.

    Parameters
    ----------
    api_key : str, optional
        API key for authentication. Default is
        ``"demo"``.
    """

    def __init__(self, api_key: str = "demo") -> None:
        self.__api_key = api_key

    def get_daily(
        self,
        ticker: str,
        output_size: str = "full",
    ) -> pd.DataFrame:
        """Fetch daily OHLCV data for *ticker*.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.
        output_size : str, optional
            ``"full"`` or ``"compact"``. Default
            ``"full"``.

        Returns
        -------
        pd.DataFrame
            Columns ``["open", "high", "low", "close",
            "volume"]``, all float, with a
            ``DatetimeIndex`` named ``"date"``.
        """
        # Build the URL with query parameters
        url = (
            "https://www.alphavantage.co/query?"
            "function=TIME_SERIES_DAILY&"
            f"symbol={ticker}&"
            f"outputsize={output_size}&"
            "datatype=json&"
            f"apikey={self.__api_key}"  # in a real project, you would use your own API key
        )

        response = requests.get(url)

        # Parse JSON into a dictionary
        data = response.json()
        
        # Extract the time series portion
        stock_data = data["Time Series (Daily)"]
        
        # Convert to DataFrame (values arrive as strings)
        df = pd.DataFrame.from_dict(
            stock_data, orient="index", dtype=float
        )
        
        # Fix the index: convert to DatetimeIndex, name it
        df.index = pd.to_datetime(df.index)
        df.index.name = "date"
        
        # Clean column names: "1. open" -> "open"
        df.columns = [c.split(". ")[1] for c in df.columns]
        
        # Sort chronologically (API returns newest first)
        df.sort_index(inplace=True)

        return df


class SQLRepository:
    """Read from and write to a SQLite database.

    Parameters
    ----------
    connection : sqlite3.Connection
        An open database connection.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def insert_table(
        self,
        table_name: str,
        records: pd.DataFrame,
        if_exists: str = "fail",
    ) -> dict:
        """Write *records* into the database.

        Parameters
        ----------
        table_name : str
            Target table name.
        records : pd.DataFrame
            Data to insert.
        if_exists : str, optional
            ``"fail"``, ``"replace"``, or ``"append"``.
            Default ``"fail"``.

        Returns
        -------
        dict
            ``{"transaction_successful": bool,
            "records_inserted": int}``
        """
        try:
            records.to_sql(table_name, self.connection, if_exists=if_exists)
            return {
                "transaction_successful": True,
                "records_inserted": len(records)
            }
        except sqlite3.Error as e:
            self.connection.rollback()

            return {
                "transaction_successful": False,
                "records_inserted": 0,
                "error_message": str(e),  # Opsional: untuk debug
            }

    def read_table(
        self,
        table_name: str,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """Read a table from the database.

        Parameters
        ----------
        table_name : str
            Table to read.
        limit : int or None, optional
            Max rows. ``None`` returns all.

        Returns
        -------
        pd.DataFrame
            ``DatetimeIndex`` named ``"date"``,
            all-float columns.
        """
        if limit is None:
            query = f"SELECT * FROM {table_name}"
        else:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
    
        result = pd.read_sql(
            query,
            self.connection,
            parse_dates=["date"],
            index_col="date",
        )
    
        result = result.astype(float)
    
        return result


def wrangle_data(ticker: str, n_observations: int) -> pd.Series:
    """Fetch daily prices and return percentage returns.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol.
    n_observations : int
        Number of return observations to keep.

    Returns
    -------
    pd.Series
        Named ``"return"``, ``DatetimeIndex``, no NaN.
    """
    av = AlphaVantageAPI()

    prices = av.get_daily(ticker=ticker)

    prices = prices["close"]

    simple_returns = prices.pct_change() * 100

    simple_returns = (
        simple_returns
        .dropna()
        .tail(n_observations)
        .rename("return")
    )

    return simple_returns
    
    

