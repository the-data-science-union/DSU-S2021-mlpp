import numpy as np

from .osu_calc import compute_acc

def beatmap_comparisons(subset, user_id):
    """Sorts a user's highscores by date, then evaluates
    a list of pairwise comparison between chronologically
    consecutive beatmap pairs
    
    'winning' beatmap is determined by the lower accuracy
    
    Parameters
    ----------
    subset: ScoresSubset
        Collection of scores to extract user's highscores
    user_id: int
        Id of user to generate comparisons for
    
    Returns
    -------
    list
        list of beatmap_id pairs (i, j), where i > j
    """
    fields = {
        'count50': 1,
        'count100': 1,
        'count300': 1,
        'countmiss': 1,
        'beatmap_id': 1,
        'user_id': 1
    }
    
    def compare(s_i, s_j):
        return compute_acc(s_i) < compute_acc(s_j)

    ordered_scores = list(subset.scores_high.find({'user_id': user_id}, fields).sort('date'))
    comparisons = []
    count_fail = 0
    
    for i in range(len(ordered_scores) - 1):
        s_i, s_j = ordered_scores[i], ordered_scores[i + 1]
        
        try: 
            i, j = s_i['beatmap_id'], s_j['beatmap_id']

            obsv = [i, j] if compare(s_i, s_j) else [j, i]
            comparisons.append(obsv)
        except: 
            return None
    
    return comparisons

def beatmap_frequency(comps):
    """Finds the frequency of each beatmap in a set of
    comparisons
    
    Parameters
    ----------
    comps: list
        list of beatmap comparisons
    """
    unique, counts = np.unique(comps, return_counts = True)

    freq = np.asarray((unique, counts)).T
    freq = freq[np.argsort(-freq[:, 1])]
    
    return freq

def prepare_comparisons(comps, beatmaps):
    bm_ids = set(beatmaps)
    
    comp_filter = lambda comp: comp[0] in bm_ids and comp[1] in bm_ids
    filtered_comps_iter = filter(comp_filter, comps.tolist())
    
    filtered_comps = np.array(list(filtered_comps_iter))
    
    index = {bm_id: i for i, bm_id in enumerate(bm_ids)}
    to_index = np.vectorize(lambda bm_id: index[bm_id])
    
    indexed_comps = to_index(filtered_comps)
    
    return indexed_comps, index