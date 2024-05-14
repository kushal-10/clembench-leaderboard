import requests

class DataFormatError(Exception):
    pass

class DataRetrievalError(Exception):
    pass

def get_helm_releases():
    '''
    Returns
        latest_release: str of latest version under "Lite" title
    '''
    releases_url = "https://raw.githubusercontent.com/stanford-crfm/helm/main/helm-frontend/project_metadata.json"
    try:
        # Fetch JSON data from the URL
        response = requests.get(releases_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        # Find the entry with title "Lite"
        lite_entry = next((entry for entry in data if entry["title"] == "Lite"), None)
        # If "Lite" entry found, get the latest release
        if lite_entry:
            latest_release = lite_entry["releases"][0]  # Latest release is the first element
            return latest_release
        else:
            print("No 'Lite' entry found in the JSON data.")
            return None
    except requests.exceptions.RequestException as e:
        print("Error fetching JSON data:", e)
        return None

def get_helm_data():
    '''
    Load the JSON file for the HELM Leaderboard, Lite, Accuracy
    https://crfm.stanford.edu/helm/lite/latest/#/leaderboard

    Return 
        json_data: Loaded JSON data from the cloud
    '''
    latest_release = get_helm_releases()
    url = f"https://storage.googleapis.com/crfm-helm-public/lite/benchmark_output/releases/{latest_release}/groups/core_scenarios.json"
    # Read JSON data from the provided URL
    try:
        # Make an HTTP GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the JSON response
        json_data = response.json()
        return json_data
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None
    
def helm_mappings(models_list: list):
    '''
    Map the display names of HELM Leaderboard to the names used by Clembench Leaderboard
    Args:
        models_list - A lsit of models with their display names
    Returns: 
        mapped_list - A list of models with the display names swapped.
    '''
    latest_release = get_helm_releases()
    mapping_url = f"https://storage.googleapis.com/crfm-helm-public/lite/benchmark_output/releases/{latest_release}/schema.json"
    try:
        # Make an HTTP GET request to the URL
        response = requests.get(mapping_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        # Parse the JSON response
        json_data = response.json()
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None
    
    # Create a map
    model_map = {}
    models = json_data['models']
    for m in models:
        model_name = m['name']
        split_name = model_name.split('/')[-1] # Remove developer name
        model_map[m['display_name']] = split_name

    # Create a new list with mapped names instead of display names
    mapped_list = []    
    for model in models_list:
        mapped_list.append(model_map[model])

    return mapped_list

def helm_rankings():
    '''
    Get the HELM rankings from Lite Leaderboard
    Return:
        helm_rankings: list of [model_name, rank] from HELM Leaderboard - Lite
    '''
    helm_data = get_helm_data() # Get JSON data
    if helm_data is not None:
        # Read mean win rate and model name
        if helm_data[0]['name'] == "accuracy":
            print("Fetching data from the Accuracy tab under HELM Lite Leaderboard")
            accuracy_section = helm_data[0] # 0 - Accuracy, 1- Efficiency, 2 - General information
            headers = accuracy_section['header'] # Check if first column is the model name and second column in the mean win rate
            if headers[0]['value'] == 'Model/adapter' and headers[1]['value'] == 'Mean win rate':
                rows = accuracy_section['rows']
                models = []
                main_scores = []
                for i in range(len(rows)):
                    models.append(rows[i][0]['value']) #0 - Model name
                    main_scores.append(rows[i][1]['value']) #1 - Mean Win rate value

                # Sort Models based on their mean_win_rate, The JSON file contains data in alphabetical order
                model_score_pairs = zip(models, main_scores)
                sorted_model_score_pairs = sorted(model_score_pairs, key=lambda pair: pair[1], reverse=True)
                sorted_models = [pair[0] for pair in sorted_model_score_pairs]
                mapped_models = helm_mappings(sorted_models)
                helm_rankings = [[name, index+1] for index, name in enumerate(mapped_models)]
                return helm_rankings
            else:
                DataFormatError("First and Second columns of the leaderboard are not 'Model' and 'mean win rate' repectively")
        else:
            DataFormatError("First element of helm_data is not 'accuracy'. Check the online JSON file")
    else:
        DataRetrievalError("Failed to fetch HELM data from the URL.")
