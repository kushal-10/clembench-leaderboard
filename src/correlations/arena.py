import pickle
import os

def chatbot_arena_rankings():
    '''
    Get chatbot arena rankings
    Returns:
        arena_rankings: list of [model_name, rank]
    '''
    file_path = os.path.join('src', 'elo_results.pkl')
    with open(file_path, 'rb') as file:
        data = pickle.load(file)
    chatbot_arena_leaderboard = data['full']['leaderboard_table_df']
    chatbot_arena_leaderboard = chatbot_arena_leaderboard.sort_values(by='rating', ascending=False)
    arena_models = chatbot_arena_leaderboard.index.tolist()
    arena_rankings = [[name, index+1] for index, name in enumerate(arena_models)]
    return arena_rankings

if __name__=='__main__':
    ranks = chatbot_arena_rankings()
    print(ranks)