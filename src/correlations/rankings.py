from src.leaderboard_utils import get_github_data
from src.correlations.helm import helm_rankings
from src.correlations.arena import chatbot_arena_rankings


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


if __name__=='__main__':

    clem = clem_rankings()
    arena = chatbot_arena_rankings()
    helm = helm_rankings()

    delta_arena = compare_rankings(clem, arena)
    delta_helm = compare_rankings(clem, helm)
    print(f"Delta Rankings w.r.t Clembench and Chatbot Arena: {delta_arena} \n Delta Rankings w.r.t Clembench and HELM: {delta_helm}")
