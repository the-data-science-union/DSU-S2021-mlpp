import sys
sys.path.extend(['../..','./modules'])

import os
from pymongo import ASCENDING as A
from tqdm import tqdm
import signal

from config import client
import sql_parser
import utils
from osu_parser.beatmapparser import BeatmapParser

osu_db = client['osu_mlpp_db1']

songs_path = "../../../data/2021_04_01_osu_files"
osu_songs = os.listdir(songs_path)


class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)

def process_hit_objects(hit_objs):
    processed_objs = []
    last_t = 0
    
    for obj in hit_objs:
        if obj['object_name'] not in ['circle', 'slider']:
            processed_objs.append([-1,-1,-1,-1,-1,-1])
            continue

        d_t1 = obj['startTime'] - last_t
        last_t = obj['startTime']

        x,y = obj['position']

        if (obj['object_name'] == 'circle'):
            x1,y1 = obj['position']
            d_t2 = 0
        else:
            x1,y1 = obj['end_position']
            d_t2 = obj['duration']

        processed_objs.append([x,y,x1,y1,d_t1,d_t2])
    
    return processed_objs

beatmap_ids = list(
    map(
        lambda x: x['_id'],
        osu_db.osu_beatmaps.find(
            {
                'mlpp.hit_objects': {
                    '$exists': False
                }
            },
            {
                '_id': 1
            }
        )
    )
)

failed = {
    'Overflow': 0,
    'Timeout': 0,
    'Other': 0
}

pbar = tqdm(beatmap_ids)

for _id in pbar:
    parser = BeatmapParser()
    path = os.path.join(songs_path, f'{_id}.osu')

    signal.alarm(30)
    try:
        parser.parseFile(path)
        parsed_obj = parser.build_beatmap()
        hit_objects = process_hit_objects(parsed_obj['hitObjects'])

        query = {'_id': _id}
        update = {
            '$set': {
                'mlpp.hit_objects': hit_objects,
                'mlpp.parsed_file_object': parsed_obj
            }
        }

        osu_db.osu_beatmaps.update_one(query, update)
    except OverflowError:
        failed['Overflow']+=1
    except TimeoutException:
        failed['Timeout']+=1
    except Exception as e:
        failed['Other']+=1
    else:
        signal.alarm(0)
    
    pbar.set_description(f"(OF: {failed['Overflow']} T: {failed['Timeout']} O: {failed['Other']}) ")

print(failed)