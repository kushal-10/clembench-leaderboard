from src.mapping.rankings import clem_rankings, chatbot_arena_rankings, helm_rankings, compare_rankings
import pandas as pd

def get_rankings():
    clem = clem_rankings()
    
    dict_clem = dict(clem)
    models = list(dict_clem.keys())
    
    arena = chatbot_arena_rankings()
    helm = helm_rankings()
    delta_arena = compare_rankings(clem, arena)
    delta_helm = compare_rankings(clem, helm)

    arena_rankings = [rank for _, rank in delta_arena]
    helm_rankings = [rank for _, rank in delta_helm]

    data = {
        'Model': models,
        'Clembench': [rank for _, rank in clem],
        'Chatbot Arena': arena_rankings,
        'HELM': helm_rankings
    }

    return pd.DataFrame(data)