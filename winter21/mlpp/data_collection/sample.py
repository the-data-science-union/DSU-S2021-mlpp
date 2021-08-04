from random import random
import datetime

class ScoresSubset:
    def __init__(self, scores_high, user_stats):
        self.scores_high = scores_high
        self.user_stats = user_stats

    def sample_random_users(self, size):
        """Retrieve a random subset of user ids from coll_users

        Parameters
        ----------
        size (int): Number of user_ids to retrieve

        Returns
        -------
        list of user ids
        """

        random_users_pipeline = [
            {'$sample': {'size': size}},
            {'$project': {'_id': 1}}
        ]

        cursor = self.user_stats.aggregate(random_users_pipeline)
        return [u['_id'] for u in cursor]

    def sample_custom_users(self, sample_func, sample_config):

        users = list(self.user_stats.find({'rank_score': {'$lte': sample_config.max_pp}}, {'_id': 1, 'rank_score': 1}))

        sampled_users = []
        for user in users:
            if random() < sample_func(user['rank_score']):
                sampled_users.append(user)

        sampled_user_ids = [u['_id'] for u in sampled_users]
        
        return sampled_user_ids

    def init_random_sample(self, coll_scores, coll_users, n_users):
        """Samples a subset of users, storing scores in coll_to

        If coll_name already exists, skip resampling and just return user_ids in the
        existing sample

        Parameters
        ----------
        coll_name (string): New collection to store sampled scores
        n_users (int): Number of users to sample

        Returns
        -------

        list of user ids that were sampled
        """

        new_subset = ScoresSubset(coll_scores, coll_users)

        if new_subset.scores_high.count() > 0 or new_subset.user_stats.count() > 0:
            print("Sample collection already exists. Reusing existing sample.")
            return
        
        user_ids = self.sample_random_users(n_users)
        users = list(self.user_stats.find({'_id': {'$in': user_ids}}))
        scores = list(self.scores_high.find({'user_id': {'$in': user_ids}}))

        new_subset.user_stats.insert_many(users)
        new_subset.scores_high.insert_many(scores)

        return new_subset, user_ids
    
    def simulate(self, sample_func, sample_config, users=False):
        sampled_users = self.sample_custom_users(sample_func, sample_config)

        sampled_scores = list(
            self.scores_high.find({
                'user_id': {
                    '$in': sampled_users
                },
                'date': {
                    '$gt': sample_config.date_limit
                }
            }, {'mlpp.est_user_pp': 1})
        )

        sampled_pp = [s['mlpp']['est_user_pp'] for s in sampled_scores]

        return (sampled_pp, sampled_users) if users else sampled_pp

        
def get_more_recent_than(self, coll_name, year, month, day, hour, minute, second, new_sample_name):
        coll_name.aggregate([
    { "$match" : {"date" : {"$gt" : datetime.datetime(year, month, day, hour, minute, month) } } },
    { "$out" : "%s" %(new_sample_name) }
])
        
def get_maps_more_recent_than(self, coll_name, year, month, day, hour, minute, second, new_sample_name):
        coll_name.aggregate([
    { "$match" : {"last_update" : {"$gt" : datetime.datetime(year, month, day, hour, minute, month) } } },
    { "$out" : "%s" %(new_sample_name) }
])
    
def get_uniform_random_sample(self, coll_name, max_size_of_bins):
        
        cursor = coll_name.aggregate(
       [
         {
           "$group":
             {
               "_id": {},
               "max": { "$max": "$mlpp.est_user_pp" }
             }
         }
       ]
    )
        for document in cursor:
            print(document)
        print(document['max'])
        max_pp = document['max']
        
        a = 0
        b = 100

        while b <= max_pp + 100:
            self.osu_db.uniform_sample.insert_many(
            coll_name.aggregate([
            {
            '$match': {
                'mlpp.est_user_pp' : {
                    '$gt': a,
                    '$lt': b,
                }
            }
        },
        {'$sample': {
        'size': max_size_of_bins
        }
        }
        ])
        )
        a = b
        b += 100
        
    
        
