# Isolated functions to load/reload the leaderboard data from github - and plot the results
from src.leaderboard_utils import get_github_data
from src.plot_utils import split_models


def get_primary_leaderboard():
    '''
    Returns
        primary_leaderboard_df[0]: Dataframe containing the primary leaderboard (laterst version of the benchmark results)
    '''
    primary_leaderboard_df, _, _ = get_github_data()
    print("Reloading primary df: ")
    print(primary_leaderboard_df)
    return primary_leaderboard_df[0]


def get_open_models():
    '''
    Returns
        open_models: Checkbox group containing the open models
    '''
    primary_leaderboard_df, _, _ = get_github_data()
    temp_df = primary_leaderboard_df[0]
    models = list(temp_df[list(temp_df.columns)[0]].unique())
    open_models, _ = split_models(models)
    return open_models


def get_closed_models():
    '''
    Returns
        closed_models: Checkbox group containing the closed models
    '''
    primary_leaderboard_df, _, _ = get_github_data()
    temp_df = primary_leaderboard_df[0]
    models = list(temp_df[list(temp_df.columns)[0]].unique())
    _, closed_models = split_models(models)
    return closed_models


def get_plot_df():
    '''
    Returns
        plot_df: Dataframe containing the results of latest version for plotting
    '''
    primary_leaderboard_df, _, _ = get_github_data()
    plot_df = primary_leaderboard_df[0]
    return plot_df


def get_version_names():
    '''
    Returns
        version_names: List containing the versions of the benchmark results for dropdown selection
    '''
    _, _, version_names = get_github_data()
    return version_names


def get_version_df():
    '''
    Returns
        version_dfs: Dataframe containing the benchmark results for all versions
    '''
    _, version_dfs, _ = get_github_data()
    return version_dfs


def get_prev_df(name='initial'):
    '''
    Returns
        prev_df: Dataframe containing the benchmark results for the previous versions (default = latest version)
    '''
    _, version_dfs, version_names = get_github_data()

    if name == 'initial':
        name = version_names[0]

    ind = version_names.index(name)
    prev_df = version_dfs[ind]
    return prev_df

