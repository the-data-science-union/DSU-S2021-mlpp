# 1. Implement class functions
# 2. Use your class in your notebook
# 3. Markdown on entire notebook
# 4. As 1st cell, Include description of your model as well as: training dataset, validation dataset error
# % rmse((true_est_pp - predicted_est_pp) / true_est_pp)

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

def get_dataframe(userIdCollection, userStatsCollection, beatmapCollection):
    sample_id = list(userIdCollection.find( {}, {"_id":0, "users": 1}))[0]["users"]
    
    user_info = {}
    for user in sample_id:
        user_info[user] = list(userStatsCollection.find( {"user_id": user, "enabled_mods": 0}, {"_id": 0, "beatmap_id": 1, "count50": 1, "count100": 1, "count300": 1, "countmiss": 1, "countgeki": 1, "countkatu": 1, "perfect": 1}))
    
    user_info_with_beatmap_features = user_info
    df = pd.DataFrame()
    for user in sample_id:
        for bm in user_info_with_beatmap_features[user]:
            bm.update(list(beatmapCollection.find( {"_id": bm["beatmap_id"]}, {"_id": 0, "countNormal": 1, "countSlider": 1, "countSpinner": 1, "countTotal": 1, "diff_approach": 1, "diff_drain": 1, "diff_overall": 1, "diff_size": 1, "diffcultyrating": 1, "hit_length": 1}))[0])
            bm.update(list(userStatsCollection.find( {"user_id": user, "beatmap_id": bm["beatmap_id"], "enabled_mods": 0}, {"_id": 0, "mlpp.est_user_pp": 1}))[0]["mlpp"])    
        df = df.append(pd.DataFrame(user_info_with_beatmap_features[user]))
    
    df.drop('beatmap_id', axis = 1, inplace = True)
    return df
    

class Xgboost_est_pp_model:
    
    def __init__(self):
        self.model = None
        
    def data_processing(df):
        norm_df = (df - np.mean(df))/np.std(df)
        return norm_df 
    
    def train_test_model(self, norm_df, testSize):
        X, y = norm_df.iloc[:,:-1],norm_df.iloc[:,-1]   
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = testSize)
        regressor = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=4,
            eta=0.2
        )
        self.model = regressor.fit(X_train, y_train)
        y_pred = regressor.predict(X_test)
        return np.sqrt(mean_squared_error(y_test, y_pred))

# class Pytorch_est_pp_model:
    
#     def __init__(self):
#         self.model = None
    
#     def data_processing(df):
#         return # some tensor to be put into model
    
#     def train_model(df):
#          #self.model = my_trained_model
    
#     def test(df):
#         model.test(df)