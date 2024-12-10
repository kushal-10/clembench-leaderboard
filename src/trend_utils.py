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

START_DATE = '2023-06-01'
def get_param_size(params: str) -> float:
    """Convert parameter size from string to float.

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
    """Create a list of models based on clemscore differences.

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


def get_models_to_display(result_df: pd.DataFrame, open_dip: float = -0.5, comm_dip: float = -10) -> tuple:
    """Retrieve models to display based on clemscore differences.

    Args:
        result_df (pd.DataFrame): DataFrame containing model data.
        open_dip (float, optional): Threshold for open models. Defaults to -0.5.
        comm_dip (float, optional): Threshold for commercial models. Defaults to -10.

    Returns:
        tuple: Two lists of model names (open and commercial).
    """
    open_model_df = result_df[result_df['open_weight']==True]
    comm_model_df = result_df[result_df['open_weight']==False]

    open_model_df = open_model_df.sort_values(by='release_date', ascending=True)
    comm_model_df = comm_model_df.sort_values(by='release_date', ascending=True)
    open_models = populate_list(open_model_df, open_dip)
    comm_models = populate_list(comm_model_df, comm_dip)
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
             benchmark_ticks: dict = {}, **plot_kwargs) -> go.Figure:
    """Generate a scatter plot for the given DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing model data.
        start_date (str, optional): Start date for filtering. Defaults to '2023-06-01'.
        end_date (str, optional): End date for filtering. Defaults to '2024-12-30'.
        benchmark_ticks (dict, optional): Custom benchmark ticks for the version dates. Defaults to {}.
    
    Keyword Args:
        open_dip (float, optional): Threshold for open models' clemscore differences. Max dip in clemscore allowed to be considered in trend.
        comm_dip (float, optional): Threshold for commercial models' clemscore differences. Max dip in clemscore allowed to be considered in trend.
        height (int, optional): Height of the plot in pixels. Adjusted for mobile or desktop views.
        mobile_view (bool, optional): Flag to indicate if the plot should be optimized for mobile display. Defaults to False.

    Returns:
        go.Figure: The generated plot.
    """

    open_dip = plot_kwargs['open_dip']
    comm_dip = plot_kwargs['comm_dip']
    height = plot_kwargs['height']

    mobile_view = True if plot_kwargs['mobile_view'] else False

    max_clemscore = df['clemscore'].max()
    # Convert 'release_date' to datetime
    df['Release date'] = pd.to_datetime(df['release_date'], format='ISO8601')
    # Filter out data before April 2023
    df = df[df['Release date'] >= pd.to_datetime(start_date)]
    open_model_list, comm_model_list = get_models_to_display(df, open_dip, comm_dip)    
    models_to_display = open_model_list + comm_model_list
    print(f"open_model_list: {open_model_list}, comm_model_list: {comm_model_list}")

    # Create a column to indicate if the model should be labeled
    df['label_model'] = df['model'].apply(lambda x: x if x in models_to_display else "")
    # If select_all is False, then show only the models in models_to_display

    if mobile_view:
        df = df[df['model'].isin(models_to_display)]

    # Add an identifier column to each DataFrame
    df['Model Type'] = df['open_weight'].map({True: 'Open-Weight', False: 'Commercial'})

    marker_size = df['parameters'].apply(lambda x: np.sqrt(x) if x > 0 else np.sqrt(400)).astype(float)  # Arbitrary sqrt value to scale marker size based on parameter size

    open_color = 'red'
    comm_color = 'blue'

    # Create the scatter plot
    fig = px.scatter(df,
                    x="Release date",
                    y="clemscore",
                    color="Model Type",  # Differentiates the datasets by color
                    hover_name="model",
                    size=marker_size,
                    size_max=40,  # Max size of the circles
                    template="plotly_white")

    
    # Sort dataframes for line plotting
    df_open = df[df['model'].isin(open_model_list)].sort_values(by='Release date')
    df_commercial = df[df['model'].isin(comm_model_list)].sort_values(by='Release date')

    ## Custom tics for x axis
    # Define the start and end dates
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    # Generate ticks every two months
    date_range = pd.date_range(start=start_date, end=end_date, freq='2MS')  # '2MS' stands for 2 Months Start frequency
    # Create labels for these ticks
    custom_ticks = {date: date.strftime('%b %Y') for date in date_range}
    benchmark_tickvals = list(pd.to_datetime(list(benchmark_ticks.keys())))
    custom_ticks = {k:v for k,v in custom_ticks.items() if k not in benchmark_tickvals}
    custom_tickvals = list(custom_ticks.keys())


    # Plot Benchmark X-axis ticks with Vertical Dotted Lines
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

    if mobile_view:
        # Remove custom_tickvals within -1 month to +1 month of benchmark_tickvals for better visibility
        one_month = pd.DateOffset(months=1)
        filtered_custom_tickvals = [
            date for date in custom_tickvals 
            if not any((benchmark_date - one_month <= date <= benchmark_date + one_month) for benchmark_date in benchmark_tickvals)
        ]
        # Alternate <br> for benchmark ticks based on date difference (Eg. v1.6, v1.6.5 too close to each other for MM benchmark)
        benchmark_tick_texts = []
        for i in range(len(benchmark_tickvals)):
            if i == 0:
                benchmark_tick_texts.append(f"<br><b>{benchmark_ticks[benchmark_tickvals[i]]}</b>")
            else:
                date_diff = (benchmark_tickvals[i] - benchmark_tickvals[i - 1]).days
                if date_diff <= 60:
                    benchmark_tick_texts.append(f"<br><br><b>{benchmark_ticks[benchmark_tickvals[i]]}</b>")
                else:
                    benchmark_tick_texts.append(f"<br><b>{benchmark_ticks[benchmark_tickvals[i]]}</b>")
        fig.update_xaxes(
            tickvals=filtered_custom_tickvals + benchmark_tickvals,  # Use filtered_custom_tickvals
            ticktext=[f"{date.strftime('%b')}<br>{date.strftime('%y')}" for date in filtered_custom_tickvals] + 
                      benchmark_tick_texts,  # Use the new benchmark tick texts
            tickangle=0,
            tickfont=dict(size=10)
        )
        fig.update_yaxes(range=[0, 110]) # Set y-axis range to 110 for better visibility of legend and avoiding overlap with interactivity block of plotly on top-right
        display_mode = 'lines+markers'
    else:
        fig.update_xaxes(
            tickvals=custom_tickvals + benchmark_tickvals,  # Use filtered_custom_tickvals
            ticktext=[f"{date.strftime('%b')} {date.strftime('%Y')}" for date in custom_tickvals] + 
                    [f"<br><b>{benchmark_ticks[date]}</b>" for date in benchmark_tickvals],  # Added <br> for vertical alignment
            tickangle=0,
            tickfont=dict(size=10)  
        )
        fig.update_yaxes(range=[0, max_clemscore+10])
        display_mode = 'lines+markers+text'


    # Add lines connecting the points for open models
    fig.add_trace(go.Scatter(x=df_open['Release date'], y=df_open['clemscore'],
                            mode=display_mode,  # Include 'text' in the mode
                            name='Open Models Trendline',
                            text=df_open['label_model'],  # Use label_model for text labels
                            textposition='top center',  # Position of the text labels
                            line=dict(color=open_color), showlegend=False))

    # Add lines connecting the points for commercial models
    fig.add_trace(go.Scatter(x=df_commercial['Release date'], y=df_commercial['clemscore'],
                            mode=display_mode,  # Include 'text' in the mode
                            name='Commercial Models Trendline',
                            text=df_commercial['label_model'],  # Use label_model for text labels
                            textposition='top center',  # Position of the text labels
                            line=dict(color=comm_color), showlegend=False))


    # Update layout to ensure text labels are visible   
    fig.update_traces(textposition='top center')

    # Update the Legend Position and plot dimensions
    fig.update_layout(height=height,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ) 
    )
    return fig

def get_final_trend_plot(benchmark: str = "Text", mobile_view: bool = False) -> go.Figure:
    """Fetch and generate the final trend plot for all models.

    Args:
        benchmark (str, optional): The benchmark type to use. Defaults to "Text".
        mobile_view (bool, optional): Flag to indicate mobile view. Defaults to False.

    Returns:
        go.Figure: The generated trend plot for selected benchmark.
    """
    # Fetch Model Registry
    response = requests.get(REGISTRY_URL)
    model_registry_data = response.json()
    # Custom tick labels
    base_repo = REPO
    json_url = base_repo + "benchmark_runs.json"
    response = requests.get(json_url)

    # Check if the JSON file request was successful
    if response.status_code != 200:
        print(f"Failed to read JSON file: Status Code: {response.status_code}")

    json_data = response.json()
    versions = json_data['versions']

    if mobile_view:
        height = 450
    else:
        height = 1000

    plot_kwargs = {'height': height, 'open_dip': -0.5, 'comm_dip': -5,
                   'mobile_view': mobile_view}

    if benchmark == "Text":
        text_dfs = get_github_data()['text']
        text_result_df = get_trend_data(text_dfs, model_registry_data)

        ## Get benchmark tickvalues as dates for X-axis
        benchmark_ticks = {}
        for ver in versions:
            if 'multimodal' not in ver['version']: # Skip MM specific benchmark dates
                benchmark_ticks[pd.to_datetime(ver['release_date'])] = ver['version']
        fig =  get_plot(text_result_df, start_date=START_DATE, end_date=datetime.now().strftime('%Y-%m-%d'), benchmark_ticks=benchmark_ticks, **plot_kwargs)
    else:
        mm_dfs = get_github_data()['multimodal']
        result_df = get_trend_data(mm_dfs, model_registry_data)
        df = result_df

        ## Get benchmark tickvalues as dates for X-axis
        benchmark_ticks = {}
        for ver in versions:
            if 'multimodal' in ver['version']:
                ver['version'] = ver['version'].replace('_multimodal', '')
            if date_difference(ver['release_date'], '2024-07-15') >= 0:
                benchmark_ticks[pd.to_datetime(ver['release_date'])] = ver['version'] ## MM benchmark dates considered after v1.6 (incl.)
        fig = get_plot(df, start_date=START_DATE, end_date=datetime.now().strftime('%Y-%m-%d'), benchmark_ticks=benchmark_ticks, **plot_kwargs)

    return fig
