from src.leaderboard_utils import get_github_data
from src.correlations.helm import helm_rankings
from src.correlations.arena import chatbot_arena_rankings

from scipy.stats import spearmanr, pearsonr
import matplotlib.pyplot as plt
import numpy as np
import os


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

def clean_rankings(rankingA, rankingB):
    '''
    Consider only common models in clembench and targeted leaderboard
    Args:
        rankingA: list of [model_name, rank] corresponding to clembench
        rankingB: list of [model_name, rank] corresponding to another benchmark
    Returns:
        rankingA, rankingB: list of [model_name, rank] common in both benchmarks
    
    '''
    dict_a = dict(rankingA) # Typecast into a dictionary

    # Clean Rankings of benchmark B
    rankingB_cleaned = []
    rank = 1
    for model,_ in rankingB:
        if model in dict_a:
            rankingB_cleaned.append([model, rank]) 
            rank += 1

    dict_b = dict(rankingB_cleaned)

    # Clean Rankings of benchmark A
    rankingA_cleaned= []
    rank = 1
    for model,_ in rankingA:
        if model in dict_b:
            rankingA_cleaned.append([model, rank]) 
            rank += 1

    return rankingA_cleaned, rankingB_cleaned

def get_correlation(rankingA, rankingB):
    '''
    Args:
        rankingA: list of [model_name, rank] corresponding to clembench
        rankingB: list of [model_name, rank] corresponding to another benchmark
    Returns:
        corr_value: Spearman's correlation coefficient
    '''
    rankingA, rankingB = clean_rankings(rankingA, rankingB)
    rankingA.sort()
    rankingB.sort()

    ranksA = [r[1] for r in rankingA]
    ranksB = [r[1] for r in rankingB]

    corr, _ = spearmanr(ranksA, ranksB)
    # corr, _ = pearsonr(ranksA, ranksB)

    return corr

def corr_plots(rankingA, rankingB, leaderboard_name):
    '''
    Args:
        rankingA: list of [model_name, rank] corresponding to clembench
        rankingB: list of [model_name, rank] corresponding to another benchmark
    '''
    rankingA, rankingB = clean_rankings(rankingA, rankingB)
    rankingA.sort()
    rankingB.sort()

    ranksA = [r[1] for r in rankingA]
    ranksB = [r[1] for r in rankingB]
    ranksA = np.array(ranksA)
    ranksB = np.array(ranksB)

    # Scatter plot
    slope, intercept = np.polyfit(ranksA, ranksB, 1)
    plt.figure(figsize=(8, 6))
    plt.scatter(ranksA, ranksB)
    plt.title(f"Scatter Plot of Ranks between Clembench and {leaderboard_name}")
    plt.xlabel("Clembench Ranks")
    plt.ylabel(f"{leaderboard_name} Ranks")
    plt.grid(True)
    plt.plot(ranksA, slope*ranksA + intercept, color='red')

    save_path = os.path.join('src', 'correlations', f"CLEM_{leaderboard_name}_ranks.png")
    plt.savefig(save_path)

if __name__=='__main__':

    clem = clem_rankings()
    arena = chatbot_arena_rankings()
    helm = helm_rankings()

    hc_corr = get_correlation(clem, helm)
    ac_corr = get_correlation(clem, arena)
    print(f"Spearman's Correlation Coefficient between HELM Leaderboard and clembench - {hc_corr}")
    print(f"Spearman's Correlation Coefficient between Chatbot Arena and clembench - {ac_corr}")

    corr_plots(clem, helm, "HELM")
    corr_plots(clem, arena, "ChatbotArena")
