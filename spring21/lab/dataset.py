from tqdm import tqdm
import torch
from torch.utils.data import IterableDataset
import random
from utils import Stopwatch


class BeatmapDataset(IterableDataset):
    def __init__(self, col, transform=None, ids=None):
        super(BeatmapDataset).__init__()

        self.col = col
        self.transform = transform
        self.ids = ids

    def __iter__(self):
        
        timer = Stopwatch()
        
        query = None

        if self.ids != None:
            query = {
                '_id': {
                    '$in': self.ids
                }
            }

        for sample in self.col.find(query):
            sample = tuple(torch.tensor(sample[key]).type(torch.float32)
                           for key in ['X1', 'X2', 'Y'])

            if self.transform:
                sample = self.transform(sample)
            
            timer.start()
            yield sample
            timer.stop()
        print(timer.elapsed)


    def __len__(self):
        return len(self.ids) if self.ids != None else self.col.count_documents({})

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

    def __init__(self, col_in, col_out, limit=100, p_min=5, p_max=50):
        col_in.create_index('playcount')
        col_in.create_index('playmode')

        self.col_in = col_in
        self.col_out = col_out
        self.limit = limit
        self.p_min = p_min
        self.p_max = p_max

        cursor = col_in.find({'playmode': 0}, {'_id': 1}).sort(
            'playcount', -1).limit(limit)
        self.top_ids = [x['_id'] for x in cursor]

    def clear_out(self):
        self.col_out.remove()

    def __partition(self, b, min_size):

        tot_len = b['total_length'] * 1000

        fail = b['mlpp']['fail']
        objs = b['mlpp']['hit_objects']

        counts = [0 for _ in range(100)]

        for obj in objs:
            t = obj[-1]
            idx = int(100 * t / tot_len)
            counts[idx] += 1

        partitions = []
        cur = [0, 0]

        for cnt in counts:
            if cur[0] < min_size:
                cur[0] += cnt
                cur[1] += 1
            else:
                partitions.append(cur)
                cur = [cnt, 1]

        return partitions

    def beatmap_samples(self, _id):
        b = self.col_in.find_one({'_id': _id})

        p = [[0, 0]] + self.__partition(b, self.p_min)
        p = torch.tensor(p).T
        p = torch.cumsum(p, 1)
        N = p.shape[1] - 2

        fail = torch.tensor(b['mlpp']['fail'])
        objs = torch.tensor(b['mlpp']['hit_objects'])

        o_i, t_i = p
        for i in range(N):
            X = torch.zeros(2, 7, self.p_max, dtype=torch.float32)
            z = [0, 0]

            valid = True
            for j in range(2):
                k = i + j
                o1, o2 = o_i[k: k + 2]
                t1, t2 = t_i[k: k + 2]

                if o2 - o1 > self.p_max:
                    valid = False
                    break

                X[j][:, :o2 - o1] = objs[o1:o2, :-1].T
                z[j] = fail[t1:t2].sum() / (t2 - t1)

            Y = torch.tensor([int(z[0] > z[1])], dtype=torch.float32)

            if valid:
                yield X[0], X[1], Y

    def generate(self):
        if self.col_out.count_documents({}):
            print('col_out not empty')
            return

        step = 0
        for _id in tqdm(self.top_ids):
            for sample in self.beatmap_samples(_id):
                X1, X2, Y = sample
                self.col_out.insert({
                    '_id': step,
                    'X1': X1.tolist(),
                    'X2': X2.tolist(),
                    'Y': Y.tolist()
                })
                step += 1


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
