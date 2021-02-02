import datetime
class osuDumpSampler:
    """Implements ways to sample a subset of users/scores from an osu db

    Attributes:
        osu_db (pymongo.database): Mongo db w/ osu_scores_high & osu_user_stats collections
    """

    def __init__(self, osu_db):
        self.osu_db = osu_db

    def get_random_user_ids(self, size):
        """Retrieve a random subset of user ids from osu_user_stats.

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

        cursor = self.osu_db['osu_user_stats'].aggregate(random_users_pipeline)
        return [u['_id'] for u in cursor]

    def get_user_scores(self, user_ids):
        """Retrieve all scores played by a set of users from osu_scores_high

        Parameters
        ----------
        user_ids (list): user_ids to retrieve scores for

        Returns
        -------
        list of scores
        """

        return list(self.osu_db['osu_scores_high'].find({'user_id': {'$in': user_ids}}))

    def use_random_sample(self, coll_name, n_users):
        """Samples a subset of users, storing scores in a new collection of self.osu_db

        If coll_name already exists, skip resampling and just return user_ids in the
        existing sample

        Parameters
        ----------
        coll_name (string): New collection to store sampled scores
        n_users (int): Number of users to sample

        Returns
        -------
        list of user_ids that were sampled
        """

        sample_coll = self.osu_db[coll_name]

        if coll_name not in self.osu_db.list_collection_names():
            user_ids = self.get_random_user_ids(n_users)
            scores = self.get_user_scores(user_ids)

            sample_coll.update_one({'_id': 'metadata'}, {
                                   '$set': {'user_ids': user_ids}}, upsert=True)
            sample_coll.insert_many(scores)

            return user_ids
        else:
            return sample_coll.find_one({'_id': 'metadata'}, {'user_ids': 1})['user_ids']
        
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
        
    
        
