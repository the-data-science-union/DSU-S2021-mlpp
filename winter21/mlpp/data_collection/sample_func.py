import numpy as np
from datetime import datetime
import math
from tqdm import tqdm
import logging


def displacement_err(data):
    n = 50
    uni = np.full(n, len(data) / n)
    binned, _ = np.histogram(data, n)
    displacement = np.sum(np.abs(binned - uni)) / 2
    return displacement / len(data)


class SampleConfig():
    def __init__(self, date_limit=datetime(2019, 1, 1), max_pp=7000, n_bins=200):
        self.date_limit = date_limit
        self.max_pp = max_pp
        self.n_bins = n_bins

class SampleFunctionGenerator():

    def __init__(self, subset, sample_config):
        self.subset = subset
        self.date_limit = sample_config.date_limit
        self.max_pp = sample_config.max_pp
        self.n_bins = sample_config.n_bins

    def greedy(self, prop=.05, fill_factor=.5):
        n_scores = self.subset.scores_high.count()

        bins_score_cnt, sample_func = np.zeros(
            self.n_bins), np.zeros(self.n_bins)
        bin_width = self.max_pp / self.n_bins
        bin_cap = math.ceil(n_scores * prop / self.n_bins)
        bins_hist = []

        for i in tqdm(range(self.n_bins - 1, -1, -1)):
            diff = bin_cap - bins_score_cnt[i]
            pp_floor, pp_ceil = i * bin_width, (i + 1) * bin_width

            if diff > 0:

                pipeline = self.__pp_histogram_pipeline(pp_floor, pp_ceil)

                u_bins_score_cnt = np.zeros(self.n_bins)
                for bin_cnt in self.subset.scores_high.aggregate(pipeline):
                    u_bins_score_cnt[int(bin_cnt['_id'])] = bin_cnt['count']

                curr_range_scores = u_bins_score_cnt[i]
                should_resize = curr_range_scores > diff

                u_prop = (diff / curr_range_scores) * \
                    fill_factor if should_resize else 1
                bins_score_cnt += u_bins_score_cnt * u_prop
                sample_func[i] = u_prop

            bins_hist.append(bins_score_cnt.copy())

        return sample_func, bins_score_cnt / bin_cap, bins_hist

    def pdf(self, dist, prop=.05):

        logging.debug(f"Sampling for {100 * prop}% of scores:")

        scores = list(
            self.subset.scores_high.find(
                {
                    'date': {
                        '$gt': self.date_limit
                    }
                },
                {
                    'mlpp.est_user_pp': 1,
                    '_id': 0
                }
            )
        )

        pp_data = [s['mlpp']['est_user_pp'] for s in scores]

        logging.debug(f"Aggregated scores from {self.subset.scores_high.name}")

        best_params = dist.fit(pp_data)
        arg = best_params[:-2]
        loc = best_params[-2]
        scale = best_params[-1]

        def pdf(i): return dist.pdf(i, loc=loc, scale=scale, *arg)

        logging.debug(f"Fitting to {dist.name}")

        t = self.__dist_threshold(pdf, prop)

        table = np.zeros(self.max_pp)
        for i in range(1, self.max_pp + 1):
            p = pdf(i)
            if p > t:
                table[i-1] = t/p
            else:
                table[i-1] = 1

        logging.debug(f"Generated sampling function")

        def func(x): 
            return table[np.asarray(x).astype(int)]
        
        return func

    def __field_histogram_pipeline(_, field, bin_width):
        return [
            {
                '$set': {
                    'range_i': {
                        '$floor': {
                            '$divide': [field, bin_width]
                        }
                    }
                }
            },
            {
                '$group': {
                    '_id': '$range_i',
                    'count': {
                        '$sum': 1
                    }
                }
            }, {
                '$sort': {
                    '_id': 1
                }
            }
        ]

    def __pp_histogram_pipeline(self, pp_floor, pp_ceil):
        user_ids_in_range = [u['_id'] for u in self.subset.user_stats.find(
            {
                'mlpp.est_current_pp': {
                    '$gte': pp_floor,
                    '$lt': pp_ceil
                }
            },
            {
                '_id': 1
            }
        )]

        pipeline = [
            {
                '$match': {
                    'user_id': {
                        '$in': user_ids_in_range
                    },
                    'date': {
                        '$gt': self.date_limit
                    }
                }
            },
            *self.__field_histogram_pipeline('$mlpp.est_user_pp', pp_ceil - pp_floor)
        ]

        return pipeline

    def __dist_threshold(self, pdf, f_prop):
        pdf_y = list(map(pdf, np.arange(1, self.max_pp + 1)))
        pdf_y = np.asarray(pdf_y)

        start, end = 0, 1

        while(True):
            mid = (start + end) / 2

            capped_y = np.copy(pdf_y)
            capped_y[pdf_y > mid] = mid
            prop = np.sum(capped_y)

            if (abs(f_prop - prop) / f_prop < .05):
                return mid

            if (prop > f_prop):
                end = mid
            else:
                start = mid
