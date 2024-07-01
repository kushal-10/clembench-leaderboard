import os
import pandas as pd
import requests
import json
from io import StringIO
from datetime import datetime


def get_github_data():
    """
    Read and process data from CSV files hosted on GitHub. - https://github.com/clembench/clembench-runs

    Returns:
        github_data (dict): Dictionary with one key "text" containing a list of DataFrames for each version's leaderboard data,
                                 sorted by a ranking column (e.g., clemscore).
        formatted_date (str): Formatted date of the latest version in "DD Month YYYY" format.
    """
    base_repo = "https://raw.githubusercontent.com/kushal-10/clembench-runs/check/website/"
    json_url = base_repo + "benchmark_runs.json"
    response = requests.get(json_url)

    # Check if the JSON file request was successful
    if response.status_code != 200:
        print(f"Failed to read JSON file: Status Code: {response.status_code}")
        return None, None, None, None

    json_data = response.json()
    versions = json_data['versions']

    # Sort version names - latest first
    version_names = sorted(
        [ver['version'] for ver in versions],
        key=lambda v: float(v[1:]),
        reverse=True
    )
    print(f"Found {len(version_names)} versions from get_github_data(): {version_names}.")

    # Get Last updated date of the latest version
    latest_version = version_names[0]
    latest_date = next(
        ver['date'] for ver in versions if ver['version'] == latest_version
    )
    formatted_date = datetime.strptime(latest_date, "%Y/%m/%d").strftime("%d %b %Y")

    # Get Leaderboard data - for text-only + multimodal
    github_data = {}

    # Text only data
    text_dfs = []
    for version in version_names:
        csv_url = f"{base_repo}{version}/results.csv"
        csv_response = requests.get(csv_url)
        if csv_response.status_code == 200:
            df = pd.read_csv(StringIO(csv_response.text))
            df = process_df(df)  # Process the DataFrame with custom function
            df = df.sort_values(by=df.columns[1], ascending=False)  # Sort by clemscore column
            text_dfs.append(df)
        else:
            print(f"Failed to read CSV file for version: {version}. Status Code: {csv_response.status_code}")

    github_data["text"] = text_dfs
    github_data["date"] = formatted_date

    return github_data


def process_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process dataframe
    - Remove repition in model names
    - Convert datatypes to sort by "float" instead of "str" for sorting
    - Update column names
    Args:
        df: Unprocessed Dataframe (after using update_cols)
    Returns:
        df: Processed Dataframe
    """

    # Change column type to float from str
    list_column_names = list(df.columns)
    model_col_name = list_column_names[0]
    for col in list_column_names:
        if col != model_col_name:
            df[col] = df[col].astype(float)

    # Remove repetition in model names, if any
    models_list = []
    for i in range(len(df)):
        model_name = df.iloc[i][model_col_name]
        splits = model_name.split('--')
        splits = [split.replace('-t0.0', '') for split in splits] # Comment to not remove -t0.0
        if splits[0] == splits[1]:
            models_list.append(splits[0])
        else:
            models_list.append(splits[0] + "--" + splits[1])
    df[model_col_name] = models_list

    # Update column names
    update = ['Model', 'Clemscore', '% Played', 'Quality Score']
    game_metrics = list_column_names[4:]

    for col in game_metrics:
        splits = col.split(',')
        update.append(splits[0].capitalize() + "" + splits[1])
    
    map_cols = {}
    for i in range(len(update)):
        map_cols[list_column_names[i]] = str(update[i])

    df = df.rename(columns=map_cols)    
    return df


def filter_search(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """
    Filter the dataframe based on the search query
    Args:
        df: Unfiltered dataframe
        query: a string of queries separated by ";"
    Return:
        filtered_df: Dataframe containing searched queries in the 'Model' column
    """
    queries = query.split(';')
    list_cols = list(df.columns)
    df_len = len(df)
    filtered_models = []
    models_list = list(df[list_cols[0]])
    for q in queries:
        q = q.lower()
        q = q.strip()
        for i in range(df_len):
            model_name = models_list[i]
            if q in model_name.lower():
                filtered_models.append(model_name) # Append model names containing query q

    filtered_df = df[df[list_cols[0]].isin(filtered_models)]

    if query == "":
        return df

    return filtered_df
