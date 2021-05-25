import random
from tqdm import tqdm
import numpy as np
import torch
from torch.utils.data import Dataset
from pymongo import UpdateOne
from scipy.stats import t

#from utils import Stopwatch


class BeatmapDataset(Dataset):
    def __init__(self, col, transform=None, ids=None):
        super(BeatmapDataset).__init__()

        self.col = col
        self.transform = transform
        self.data = self.__getSamples(ids)

    def __documentToSample(self, doc):
        sample = (
            torch.tensor(doc['X1']).type(torch.float32),
            torch.tensor(doc['X2']).type(torch.float32),
            torch.tensor(doc['Y']).type(torch.float32).unsqueeze(0)
        )

        if self.transform:
            sample = self.transform(sample)

        return sample

    def __getSamples(self, ids):
        query = None
        
        if ids != None:
            query = {
                '_id': {
                    '$in': ids
                }
            }

        return list(map(self.__documentToSample, self.col.find(query)))

    def __getitem__(self, i):
        return self.data[i]

    def __len__(self):
        return len(self.data)

    def __random_split(N, pcnt=.8):
        perm_ids = torch.randperm(N)
        split = int(N * pcnt)
        return perm_ids[: split].tolist(), perm_ids[split:].tolist()

    @classmethod
    def split(self, col, pcnt, **kwargs):
        N = col.count_documents({})
        train_ids, test_ids = self.__random_split(N)

        return (
            BeatmapDataset(col, ids=train_ids, **kwargs),
            BeatmapDataset(col, ids=test_ids, **kwargs)
        )


class BeatmapSamples():

    def __init__(self, 
                 col_in, 
                 col_out, 
                 limit=100, 
                 p_min=5, 
                 p_max=50, 
                 ratio_min = float('-inf'), 
                 ratio_max = float('inf'), 
                 fail_ratio=False, 
                 fail_min=0, 
                 drain_min=0):
        col_in.create_index('playcount')
        col_in.create_index('playmode')

        self.col_in = col_in
        self.col_out = col_out
        self.limit = limit
        self.p_min = p_min
        self.p_max = p_max
        self.ratio_min = ratio_min
        self.ratio_max = ratio_max
        self.fail_ratio = fail_ratio
        self.fail_min = max(self.fail_ratio, fail_min)

        cursor = col_in.find({
            'playmode': 0,
            'diff_drain': {
                '$gte': drain_min
            }
        }, {
            '_id': 1
        }).sort('playcount', -1).limit(limit)

        self.top_ids = [x['_id'] for x in cursor]

    def clear_out(self):
        self.col_out.remove()

    def beatmap_samples(self, _id):
        """Generates samples from a beatmap

        Args:
            _id: Beatmap id

        Returns:
            list(X1, X2, Y): Paired X1 & X2 sample inputs, Y label
        """
        b = self.col_in.find_one({'_id': _id})  # beatmap document

        # aux [0, 0]
        p = [[0, 0]] + self.partition(b, self.p_min)
        p = torch.tensor(p).T  # [[object counts], [chunk counts]]

        # find object & chunk starting indecies
        p = torch.cumsum(p, 1)
        N = p.shape[1] - 2  # (no. partitions - 1) total samples

        fail = torch.tensor(b['mlpp']['fail'])
        objs = torch.tensor(b['mlpp']['hit_objects'])

        o_i, t_i = p
        for i in range(N):
            X = torch.zeros(2, 7, self.p_max, dtype=torch.float32)
            z = [0, 0]

            valid = True

            # compute samples for X1, X2
            for j in range(2):

                # object & chunk range
                k = i + j
                o1, o2 = o_i[k: k + 2]
                t1, t2 = t_i[k: k + 2]

                # check object count <= p_max
                if o2 - o1 > self.p_max:
                    valid = False
                    break

                # transform objects into channels & cut timepoint
                # place at front of tensor
                X[j][:, :o2 - o1] = objs[o1:o2, :-1].T
                z[j] = fail[t1:t2].sum() / (t2 - t1)

                if z[j] < self.fail_min:
                    valid = False
                    break

            if not valid:
                continue
                
            abs_ratio = z[0] / z[1] if z[0] > z[1] else z[1] / z[0]
            
            if not (self.ratio_min <= abs_ratio <= self.ratio_max):
                continue

            # ratio or binary label
            Y = z[0] / z[1] if self.fail_ratio else int(z[0] > z[1])

            yield X[0], X[1], Y

    def generate(self):
        """Creates samples dumped into col_out

        Returns (col_out):
            sample: {
                X1: 7 by (p_max) size array of hit_objects,
                X2: Refer to X1,
                Y: (no. fails X1 > X2) ? 1 : 0
            }

        """
        if self.col_out.count_documents({}):
            print('col_out not empty')
            return

        step = 0
        for _id in tqdm(self.top_ids):
            for sample in self.beatmap_samples(_id):
                X1, X2, Y = sample
                self.col_out.insert({
                    '_id': step,
                    'beatmap_id': _id,
                    'X1': X1.tolist(),
                    'X2': X2.tolist(),
                    'Y': Y
                })
                step += 1

        # equalize for regression
        if self.fail_ratio:
            res = list(self.col_out.find(None, {'Y': 1}))

            id_arr = [x['_id'] for x in res]

            Y_arr = np.asarray([x['Y'] for x in res])
            Y_arr = self.log_t_equalize(Y_arr)

            updates = [
                UpdateOne(
                    {
                        '_id': _id
                    }, {
                        '$set': {
                            'Y': Y
                        }
                    }
                )for _id, Y in zip(id_arr, Y_arr)
            ]

            self.col_out.bulk_write(updates)

    @ classmethod
    def log_t_equalize(self, arr):
        res = np.log(arr)

        params = t.fit(res)
        arg = params[:-2]
        loc = params[-2]
        scale = params[-1]

        res = t.cdf(res, loc=loc, scale=scale, *arg)

        return res

    @ classmethod
    def partition(self, b, min_size):
        """Partitions beatmap by chunks, with at least min_size objects each

        Args:
            b: MLpp beatmap document
            min_size: minimum objects per slice
        Returns:
            list(slice): slices partitioning all beatmap chunks in order

        Types:
            slice: [no. objects, no. chunks]
        """

        # seconds => ms
        tot_len = b['total_length'] * 1000

        fail = b['mlpp']['fail']
        objs = b['mlpp']['hit_objects']

        # count objects in each chunk
        counts = [0 for _ in range(100)]

        for obj in objs:
            t = obj[-1]  # time of object

            # calculate chunk index
            try:
                idx = min(int(100 * t / tot_len), 99)
                counts[idx] += 1
            except Exception as e:
                print(b)
                raise e

        partitions = []
        cur = [0, 0]  # [no. objects, no. chunks]

        for cnt in counts:
            cur[0] += cnt
            cur[1] += 1

            # no. objs meets minimum
            if cur[0] >= min_size:
                partitions.append(cur)
                cur = [0, 0]

        return partitions


class Normalize:
    def norm(x):
        std, mean = torch.std_mean(x, 0)
        return (x - mean.unsqueeze(0)) / std.unsqueeze(0)

    def __call__(self, sample):
        X, Y = sample
        x1, x2 = X

        return torch.stack((norm(x1), norm(x2)))


class ShufflePairs:
    def __call__(self, sample):
        X1, X2, Y = sample

        Y1 = torch.tensor([random.randint(0, 1)]).type(torch.float32)

        if Y == Y1:
            return X1, X2, Y1
        else:
            return X2, X1, Y1
