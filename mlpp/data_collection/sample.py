from random import random

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

    def sample_custom_users(self, sample_func):
        max_pp = len(sample_func)

        users = list(self.user_stats.find({}, {'_id': 1, 'rank_score': 1}))

        sampled_users = []
        for user in users:
            if user['rank_score'] < max_pp and random() < sample_func[int(user['rank_score'])]:
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
        
        user_ids = self.random_user_ids(n_users)
        users = list(self.user_stats.find({'_id': {'$in': user_ids}}))
        scores = list(self.scores_high.find({'user_id': {'$in': user_ids}}))

        new_subset.user_stats.insert_many(users)
        new_subset.scores_high.insert_many(scores)

        return new_subset, user_ids
    
    def simulate(self, sample_func, sample_config, users=False):
        sampled_users = self.sample_custom_users(sample_func)

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
        
