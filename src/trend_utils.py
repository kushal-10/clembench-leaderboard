## Fetch Model Registry and clemscores
import requests
import pandas as pd
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from src.assets.text_content import REGISTRY_URL, REPO
from src.leaderboard_utils import get_github_data


# Fetch Model Registry
response = requests.get(REGISTRY_URL)
model_registry_data = response.json()
model_registry_df = pd.DataFrame(model_registry_data)
# Custom tick labels
base_repo = REPO
json_url = base_repo + "benchmark_runs.json"
response = requests.get(json_url)

# Check if the JSON file request was successful
if response.status_code != 200:
    print(f"Failed to read JSON file: Status Code: {response.status_code}")

json_data = response.json()
versions = json_data['versions']


def get_param_size(params: str) -> float:
    """Get the size of parameters in a float format.

    Args:
        params (str): The parameter size as a string (e.g., '1000B', '1T').

    Returns:
        float: The size of parameters in float.
    """
    if not params:
        param_size = 0
    else:
        if params[-1] == "B":
            param_size = params[:-1]
            param_size = float(param_size)
        elif params[-1] == "T":
            param_size = params[:-1]
            param_size = float(param_size)
            param_size *= 1000
        else:
            print("Not a valid parameter size")

    return param_size

def date_difference(date_str1: str, date_str2: str) -> int:
    """Calculate the difference in days between two dates.

    Args:
        date_str1 (str): The first date as a string in 'YYYY-MM-DD' format.
        date_str2 (str): The second date as a string in 'YYYY-MM-DD' format.

    Returns:
        int: The difference in days between the two dates.
    """
    date_format = "%Y-%m-%d"
    date1 = datetime.strptime(date_str1, date_format)
    date2 = datetime.strptime(date_str2, date_format)
    return (date1 - date2).days


def populate_list(df: pd.DataFrame, abs_diff: float) -> list:
    """Populate a list of models based on clemscore differences.

    Args:
        df (pd.DataFrame): DataFrame containing model data.
        abs_diff (float): The absolute difference threshold for clemscore.

    Returns:
        list: A list of model names that meet the criteria.
    """
    l = [df.iloc[0]['model']]
    prev_clemscore = df.iloc[0]['clemscore']
    prev_date = df.iloc[0]['release_date']

    for i in range(1, len(df)):
        curr_clemscore = df.iloc[i]['clemscore']
        curr_date = df.iloc[i]['release_date']
        date_diff = date_difference(curr_date, prev_date)

        if curr_clemscore - prev_clemscore >= abs_diff:
            if date_diff == 0:
                l[-1] = df.iloc[i]['model']
            else:
                l.append(df.iloc[i]['model'])

            prev_clemscore = curr_clemscore
            prev_date = curr_date

    # Add the last model if the difference between the last and previous date is greater than 15 days
    last_date = df.iloc[-1]['release_date']
    if date_difference(last_date, prev_date) > 15:
        l.append(df.iloc[-1]['model'])

    return l


def get_models_to_display(result_df: pd.DataFrame, open_diff: float = -0.5, comm_diff: float = -10) -> tuple:
    """Get models to display based on clemscore differences.

    Args:
        result_df (pd.DataFrame): DataFrame containing model data.
        open_diff (float, optional): Threshold for open models. Defaults to -0.5.
        comm_diff (float, optional): Threshold for commercial models. Defaults to -10.

    Returns:
        tuple: Two lists of model names (open and commercial).
    """
    open_model_df = result_df[result_df['open_weight']==True]
    comm_model_df = result_df[result_df['open_weight']==False]

    open_model_df = open_model_df.sort_values(by='release_date', ascending=True)
    comm_model_df = comm_model_df.sort_values(by='release_date', ascending=True)
    open_models = populate_list(open_model_df, open_diff)
    comm_models = populate_list(comm_model_df, comm_diff)
    return open_models, comm_models


def get_trend_data(text_dfs: list, model_registry_data: list) -> pd.DataFrame:
    """Process text data frames to extract model information.

    Args:
        text_dfs (list): List of DataFrames containing model information.
        model_registry_data (list): List of dictionaries containing model registry data.

    Returns:
        pd.DataFrame: DataFrame containing processed model data.
    """
    visited = set()  # Track models that have been processed
    result_df = pd.DataFrame(columns=['model', 'clemscore', 'open_weight', 'release_date', 'parameters', 'est_flag'])

    for df in text_dfs:
        for i in range(len(df)):
            model_name = df['Model'].iloc[i]
            if model_name not in visited:
                visited.add(model_name)
                for dict_obj in model_registry_data:
                    if dict_obj["model_name"] == model_name:
                        if dict_obj["parameters"] == "" :
                            params = "1000B"
                            est_flag = True
                            print(f"EST PARAMS for {model_name}: {params}")
                        else:
                            params = dict_obj['parameters']
                            est_flag = False

                        param_size = get_param_size(params)
                        new_data = {'model': model_name, 'clemscore': df['Clemscore'].iloc[i], 'open_weight':dict_obj['open_weight'],
                                    'release_date': dict_obj['release_date'], 'parameters': param_size, 'est_flag': est_flag}
                        result_df.loc[len(result_df)] = new_data
                        break
    return result_df  # Return the compiled DataFrame


def get_plot(df: pd.DataFrame, start_date: str = '2023-06-01', end_date: str = '2024-12-30',
              open_diff: float = -0.5, comm_diff: float = -10, benchmark_ticks: dict = {},
              height: int = 1000, width: int = 1450) -> go.Figure:
    """Generate a plot for the given DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing model data.
        start_date (str, optional): Start date for filtering. Defaults to '2023-06-01'.
        end_date (str, optional): End date for filtering. Defaults to '2024-12-30'.
        open_diff (float, optional): Threshold for open models. Defaults to -0.5. The threshold is the allowed dip in clemscore for the trendline to be plotted.
        comm_diff (float, optional): Threshold for commercial models. Defaults to -10. The threshold is the allowed dip in clemscore for the trendline to be plotted.
        benchmark_ticks (dict, optional): Custom benchmark ticks for the version dates. Defaults to {}.

    Returns:
        go.Figure: The generated plot.
    """
    max_clemscore = df['clemscore'].max()
    # Convert 'release_date' to datetime
    df['Release date'] = pd.to_datetime(df['release_date'], format='ISO8601')
    # Filter out data before April 2023
    df = df[df['Release date'] >= pd.to_datetime(start_date)]
    open_model_list, comm_model_list = get_models_to_display(df, open_diff, comm_diff)    
    models_to_display = open_model_list + comm_model_list

    # Create a column to indicate if the model should be labeled
    df['label_model'] = df['model'].apply(lambda x: x if x in models_to_display else "")
    # Add an identifier column to each DataFrame
    df['Model Type'] = df['open_weight'].map({True: 'Open-Weight', False: 'Commercial'})

    marker_size = df['parameters'].apply(lambda x: np.sqrt(x) if x > 0 else np.sqrt(200)).astype(float)  # Arbitrary
    marker_symbol = df['parameters'].apply(lambda x: 'circle' if x > 0 else 'circle-open')

    open_color = 'red'
    comm_color = 'blue'

    # Create the scatter plot
    fig = px.scatter(df,
                    x="Release date",
                    y="clemscore",
                    color="Model Type",  # Differentiates the datasets by color
                    text="label_model",  # Adds text labels from the 'label_model' column
                    hover_name="model",
                    size=marker_size,
                    size_max=40,  # Max size of the circles
                    symbol=marker_symbol,
                    symbol_sequence=['circle'],
                    template="plotly_white")
                    # title=f"Commercial v/s Open-Weight models for {data} benchmark - clemscore over time.  The size of the circles represents the scaled value of the parameters of the models. Larger circles indicate higher parameter values.")

    # Sort dataframes for line plotting
    df_open = df[df['model'].isin(open_model_list)].sort_values(by='Release date')
    df_commercial = df[df['model'].isin(comm_model_list)].sort_values(by='Release date')

    ## Custom tics for x axis
    benchmark_tickvals = list(pd.to_datetime(list(benchmark_ticks.keys())))
    # Define the start and end dates
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    # Generate ticks every two months
    date_range = pd.date_range(start=start_date, end=end_date, freq='2MS')  # '2MS' stands for 2 Months Start frequency
    # Create labels for these ticks
    custom_ticks = {date: date.strftime('%b %Y') for date in date_range}

    combined_ticks = {}
    for key in benchmark_ticks:
        if key not in combined_ticks:
            combined_ticks[key] = benchmark_ticks[key]
    for key in custom_ticks:
        if key not in combined_ticks:
            combined_ticks[key] = custom_ticks[key]
    combined_tickvals = list(combined_ticks.keys())
    combined_ticktext = list(combined_ticks.values())

    # Plot Benchmark Ticks with Vertical Dotted Lines
    for date in benchmark_tickvals:
        fig.add_shape(
            go.layout.Shape(
                type='line',
                x0=date,
                x1=date,
                y0=0,
                y1=1,
                yref='paper',
                line=dict(color='#A9A9A9', dash='dash')
            )
        )

    # Update x-axis with combined ticks
    fig.update_xaxes(
        tickvals=combined_tickvals,
        ticktext=combined_ticktext,
        tickangle=0
    )

    # Remove old legend entries
    for trace in fig.data:
        trace.showlegend = False


    # Add lines connecting the points for open models
    fig.add_trace(go.Scatter(x=df_open['Release date'], y=df_open['clemscore'],
                            mode='lines+markers', name='Open Models Trendline',
                            line=dict(color=open_color), showlegend=False))

    # Add lines connecting the points for commercial models
    fig.add_trace(go.Scatter(x=df_commercial['Release date'], y=df_commercial['clemscore'],
                            mode='lines+markers', name='Commercial Models Trendline',
                            line=dict(color=comm_color), showlegend=False))


    # Update layout to ensure text labels are visible
    fig.update_traces(textposition='top center')
    fig.update_yaxes(range=[0, max_clemscore+10])

    # Update the x-axis title
    fig.update_layout(width=width, height=height,
        xaxis_title='Release dates of models and clembench versions'  # Set your desired x-axis title here
    )

    # Add custom legend
    fig.add_trace(go.Scatter(
        x=[None],  # X coordinate for the legend entry
        y=[None],  # Y coordinate for the legend entry
        mode='markers',
        marker=dict(symbol='circle', color=open_color),
        legendgroup='marker',
        showlegend=True,
        name='Open-Weight Models'
    ))

    fig.add_trace(go.Scatter(
        x=[None],  # X coordinate for the legend entry
        y=[None],  # Y coordinate for the legend entry
        mode='markers',
        marker=dict(symbol='circle', color=comm_color),
        legendgroup='marker',
        showlegend=True,
        name='Commercial Models'
    ))

    return fig


def get_final_trend_plot(benchmark: str = "text", mobile_flag: bool = False) -> go.Figure:
    """Get the final trend plot for all models.

    Returns:
        go.Figure: The generated trend plot for selected benchmark.
    """
    if mobile_flag:
        height = 450
        width = 450
    else:
        height = 1000
        width = 1450

    if benchmark == "text":
        text_dfs = get_github_data()['text']
        result_df = get_trend_data(text_dfs, model_registry_data)
        df = result_df
        benchmark_ticks = {}
        for ver in versions:
            if 'multimodal' not in ver['version']:
                benchmark_ticks[pd.to_datetime(ver['date'])] = ver['version']
        fig =  get_plot(df, start_date='2023-06-01', end_date=datetime.now().strftime('%Y-%m-%d'), open_diff=-0.5, comm_diff=-5, benchmark_ticks=benchmark_ticks, height=height, width=width)
    else:
        text_dfs = get_github_data()['multimodal']
        result_df = get_trend_data(text_dfs, model_registry_data)
        df = result_df
        benchmark_ticks = {}
        for ver in versions:
            if 'multimodal' in ver['version']:
                ver['version'] = ver['version'].replace('_multimodal', '')
            benchmark_ticks[pd.to_datetime(ver['date'])] = ver['version']
        fig = get_plot(df, start_date='2023-06-01', end_date=datetime.now().strftime('%Y-%m-%d'), open_diff=-0.5, comm_diff=-5, benchmark_ticks=benchmark_ticks, height=height, width=width)


    if mobile_flag:
        # Remove all name labels on points
        for trace in fig.data:
            trace.text = []  # Clear text labels
   
        # # Show only benchmark ticks
        # fig.update_xaxes(tickvals=combined_tickvals, ticktext=combined_ticktext)  # Show only benchmark ticks
        # fig.update_layout(width=width, height=height)

    return fig
