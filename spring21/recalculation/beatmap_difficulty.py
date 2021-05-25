#!/usr/bin/env python
# coding: utf-8

# ## Beatmap Difficulty Recalculation

# In[154]:

from config import client
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import itertools
from tqdm import tqdm

# In[155]:


db = client['osu_mlpp_db1']
beatmaps = db.osu_beatmaps
user_stats = db.osu_user_stats
scores_high = db.osu_scores_high


# ## Retrieve Beatmaps by Popularity

# In[156]:


most_popular_bm = list(beatmaps.find({}, {'playcount': 1}))


# In[157]:


most_popular_bm = sorted(most_popular_bm, key = lambda i : i['playcount'], reverse = True)


# In[158]:


most_popular_bm[:10]


# In[159]:


most_popular_bm = {b['_id']: b['playcount'] for b in most_popular_bm}


# In[160]:


df_most_popular_bm = pd.DataFrame.from_dict(most_popular_bm, orient='index').reset_index()
df_most_popular_bm = df_most_popular_bm.rename(columns={'index':'Beatmap id',
                                                        0: 'playcount'})


# ## Retrieving Difficulty Rating for Each Beatmap

# In[162]:


difficulty_info = list(beatmaps.find({}, {'difficultyrating': 1}))


# In[163]:


difficulty_info = {b['_id']: b['difficultyrating'] for b in difficulty_info}


# In[164]:


df_bm_difficulty = pd.DataFrame.from_dict(difficulty_info, orient='index').reset_index()
df_bm_difficulty = df_bm_difficulty.rename(columns={'index':'Beatmap id', 
                                                    0: 'Difficulty rating'})


# In[165]:


df_sorted_bm_with_rating = df_most_popular_bm.merge(df_bm_difficulty, on = 'Beatmap id')
df_sorted_bm_with_rating = df_sorted_bm_with_rating[0:1000]
df_sorted_bm_with_rating.tail()


# In[166]:


df_sorted_bm_with_rating.hist(column = 'Difficulty rating', bins = [0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10])


beatmap_dict = {}


def get_bm_scores(id_):
    beatmap_scores = list(scores_high.find({'beatmap_id': id_}, {'_id': 0, 'score':1}))
    scores_df = pd.DataFrame.from_dict(beatmap_scores)
    scores_df = (scores_df - scores_df.min()) / (scores_df.max() - scores_df.min())
    return np.mean(scores_df)[0]


# set elo constants
mean_elo = 1500
elo_width = 400
k_factor = 64


df_sorted_bm_with_rating['Scaled Difficulty Rating'] = df_sorted_bm_with_rating['Difficulty rating'] * 300

df_sorted_bm_with_rating = df_sorted_bm_with_rating.sample(frac = 1).reset_index()


bm_ratings_dict = dict(zip(df_sorted_bm_with_rating['Beatmap id'], df_sorted_bm_with_rating['Scaled Difficulty Rating']))
bm_ratings_dict


# Python 3 program for Elo Rating
import math

def find_winner(score_a, score_b):
    if score_a < score_b: 
        return 1 # A wins
    else: 
        return 0 # B wins

# Function to calculate the Probability
def Probability(ra, rb):
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (ra - rb) / 400))

# Function to calculate Elo rating
# K is a constant.
# d determines whether Player A wins or Player B.
def EloRating(Ra, Rb, K, d):
    # To calculate the Winning Probability of Player B
    Pb = Probability(Ra, Rb)
    # To calculate the Winning Probability of Player A
    Pa = Probability(Rb, Ra)
    # Case - 1: When Player A wins, increase A Elo Ratings
    if (d == 1) :
        Ra = Ra + K * (1 - Pa)
        Rb = Rb + K * (0 - Pb)
    # Case - 2: When Player B wins, increase B Elo Ratings
    else :
        Ra = Ra + K * (0 - Pa)
        Rb = Rb + K * (1 - Pb)
    return (round(Ra, 6), round(Rb, 6))

    
# score_a = get_bm_scores(397534)
# score_b = get_bm_scores(131891)
# Ra = df_sorted_bm_with_rating['Scaled Difficulty Rating'][0]
# Rb = df_sorted_bm_with_rating['Scaled Difficulty Rating'][1]
# d = find_winner(score_a, score_b)
# K = 30
# Ra, Rb = EloRating(Ra, Rb, K, d)

# This code is contributed by Smitha Dinesh Semwal


# In[ ]:

import csv

def write_dict(my_dict):
    w = csv.writer(open("spring21/recalculation/output.csv", "w"))
    for key, val in bm_ratings_dict.items():
        w.writerow([key, val])

K = 30
cnt = 0

for pair in tqdm(itertools.combinations(list(bm_ratings_dict.keys()),2)):
    cnt += 1
    
    if cnt % 1000 == 0:
        write_dict(bm_ratings_dict)
        
    try:
        score_a = get_bm_scores(pair[0])
        score_b = get_bm_scores(pair[1])
        Ra = df_sorted_bm_with_rating.loc[df_sorted_bm_with_rating['Beatmap id'] == pair[0]]['Scaled Difficulty Rating'].iloc[0]
        Rb = df_sorted_bm_with_rating.loc[df_sorted_bm_with_rating['Beatmap id'] == pair[1]]['Scaled Difficulty Rating'].iloc[0]
        d = find_winner(score_a, score_b)
        Ra, Rb = EloRating(Ra, Rb, K, d)
        bm_ratings_dict[pair[0]] = Ra
        bm_ratings_dict[pair[1]] = Rb 
    except:
        continue

write_dict(bm_ratings_dict)