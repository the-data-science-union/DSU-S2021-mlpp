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
        
    def test(self):
        return
