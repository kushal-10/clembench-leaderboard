from src.leaderboard_utils import get_github_data

import pandas as pd
import pickle
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def clem_rankings():
    '''
    Get clembench rankings
    Returns:
        clem_rankings: list of [model_name, rank]
    '''
    clembench_leaderboard, _, _ = get_github_data()
    clembench_leaderboard_df = clembench_leaderboard[0]
    clem_models = clembench_leaderboard_df['Model'].tolist()
    clem_rankings = [[name, index+1] for index, name in enumerate(clem_models)]
    return clem_rankings


def chatbot_arena_rankings():
    '''
    Get chatbot arena rankings
    Returns:
        arena_rankings: list of [model_name, rank]
    '''
    with open('src/mapping/results/arena.pkl', 'rb') as file:
        data = pickle.load(file)
    chatbot_arena_leaderboard = data['full']['leaderboard_table_df']
    chatbot_arena_leaderboard = chatbot_arena_leaderboard.sort_values(by='rating', ascending=False)
    arena_models = chatbot_arena_leaderboard.index.tolist()
    arena_rankings = [[name, index+1] for index, name in enumerate(arena_models)]
    return arena_rankings

def helm_rankings():
    '''
    Get HELM benchmark rankings
    Returns:
        helm_rankings: list of [model_name, rank]
    '''
    url = 'https://crfm.stanford.edu/helm/lite/latest/#/leaderboard'
    # response = requests.get(url)

    driver = webdriver.Chrome()
    driver.get(url)
    # Wait for the table to be loaded (adjust timeout as needed)
    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
    except Exception as e:
        print("Table not found within the timeout period.")
        driver.quit()
        exit()
    # Get the page source after JavaScript has executed
    html_content = driver.page_source
    # Close the WebDriver
    driver.quit()

    soup = BeautifulSoup(html_content, 'html.parser')
    models = []
    main_scores = []

    soup = soup.find('table')
    for row in soup.find_all('tr')[1:]:  # Skip the header row
        columns = row.find_all('td')
        model = columns[0].text.strip()
        main_score = columns[1].text.strip()
        models.append(model)
        main_scores.append(main_score)

    helm_rankings = [[name, index+1] for index, name in enumerate(models)]

    ## FOR MODEL MAPPING
    models_url = "https://crfm.stanford.edu/helm/lite/latest/#/models"
    mdriver = webdriver.Chrome()
    mdriver.get(models_url)
    try:
        table = WebDriverWait(mdriver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
    except Exception as e:
        print("Table not found within the timeout period.")
        mdriver.quit()
        exit()
    html_content = mdriver.page_source
    mdriver.quit()
    model_soup = BeautifulSoup(html_content, 'html.parser')
    mapping = {}

    model_soup = model_soup.find('table')
    for row in model_soup.find_all('tr')[1:]:  # Skip the header row
        columns = row.find_all('td')
        model = columns[1].find_all('span')
        display_name = columns[1].find_all('span')[0].text.strip()
        model_name = columns[1].find_all('span')[1].text.strip()
        model_name = model_name.split('/')[1]
        mapping[display_name] = model_name 


    helm_rankings = [[mapping[name], rank] for name, rank in helm_rankings]
    return helm_rankings

def compare_rankings(rankingA, rankingB):
    '''
    Compare rankings of another benchmark with Clembench
    Args:
        rankingA: list of [model_name, rank] corresponding to clembench
        rankingB: list of [model_name, rank] corresponding to another benchmark
    Returns:
        delta_rankings: A dataframe consisting of 'Model' and 'Delta' (Difference in ranking w.r.t Clembench)
            
    Delta = Rank in Clembench - Rank in another benchmark
    Ensure model_name matches with Clembench
    '''
    dict_a = dict(rankingA)

    # Filter models in rankingB that are in rankingA (clembench) and update rank
    rankingB_updated = []
    rank = 1
    for model,_ in rankingB:
        if model in dict_a:
            rankingB_updated.append([model, rank]) 
            rank += 1
    dict_b = dict(rankingB_updated)

    delta_list = []
    for model, rank_a in rankingA:
        if model in dict_b:
            rank_b = dict_b[model]
            delta = rank_a - rank_b
            delta_list.append([model, delta])
        else:
            delta_list.append([model, 'N/A'])

    return delta_list


if __name__=='__main__':
    clem = clem_rankings()
    arena = chatbot_arena_rankings()
    helm = helm_rankings()
    delta_arena = compare_rankings(clem, arena)
    delta_helm = compare_rankings(clem, helm)
    print(f"Delta Rankings w.r.t Clembench and Chatbot Arena: {delta_arena} \n Delta Rankings w.r.t Clembench and HELM: {delta_helm}")
