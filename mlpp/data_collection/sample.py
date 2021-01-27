class osuDumpSampler:

    def __init__(self, osu_db):
        self.osu_db = osu_db

    def get_random_user_ids(self, size):
        random_users_pipeline = [
            {'$sample': {'size': size}},
            {'$project': {'_id': 1}}
        ]

        cursor = self.osu_db['osu_user_stats'].aggregate(random_users_pipeline)
        return [u['_id'] for u in cursor]

    def get_user_scores(self, user_ids):
        return list(self.osu_db['osu_scores_high'].find({'user_id': {'$in': user_ids}}))
        
    def use_random_sample(self, coll_name, n_users):
        sample_coll = self.osu_db[coll_name]

        if coll_name not in self.osu_db.list_collection_names():
            user_ids = self.get_random_user_ids(n_users)
            scores = self.get_user_scores(user_ids)
            
            sample_coll.update_one({'_id': 'metadata'}, {'$set': {'user_ids': user_ids}}, upsert=True)
            sample_coll.insert_many(scores)

            return user_ids
        else:
            return sample_coll.find_one({'_id': 'metadata'}, {'user_ids': 1})['user_ids']