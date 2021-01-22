from pymongo import UpdateOne
from tqdm import tqdm

def get_fields(cursor_ex):
    return list(map(lambda c: c[0], cursor_ex.description))

class SqlDumpMigrator:

    def __init__(self, sql_inst, mongo_inst):
        self.sql_inst = sql_inst
        self.mongo_inst = mongo_inst

    def insert_user_scores(self, sql_db_name, user_id, new_db_name):
        new_mongo_db = self.mongo_inst[new_db_name]

        with self.sql_inst.cursor() as cursor:
            cursor.execute(
                f"select * from {sql_db_name}.osu_scores_high WHERE user_id = {user_id}")
            fields = get_fields(cursor)
            fields[0] = '_id'

            user_scores = [dict(zip(fields, row)) for row in cursor]

            new_mongo_db['osu_scores_high'].insert_many(user_scores)

    def migrate_users_and_scores(self, dump_names, new_db_name):
        new_mongo_db = self.mongo_inst[new_db_name]

        user_ids = new_mongo_db['osu_user_stats'].find({}, {})
        migrated_users = set(map(lambda u: u['_id'], user_ids))

        for db_name in dump_names:
            print(f"Importing dump beatmaps: {db_name}")

            with self.sql_inst.cursor() as cursor:
                cursor.execute(f"select * from {db_name}.osu_user_stats")

                fields = get_fields(cursor)
                fields[0] = '_id'

                with tqdm(total=cursor.rowcount) as progress_bar:
                    for row in cursor:
                        user_stats = dict(zip(fields, row))

                        if user_stats['_id'] not in migrated_users:
                            new_mongo_db['osu_user_stats'].insert(user_stats)
                            self.insert_user_scores(db_name, user_stats['_id'], new_db_name)

                            migrated_users.add(user_stats['_id'])

                        progress_bar.update(1)
            print()
    
    def migrate_beatmaps(self, dump_names, new_db_name):
        for db_name in dump_names:
            print(f"Importing dump: {db_name}")

            with self.sql_inst.cursor() as cursor:
                try:
                    cursor.execute(f"select * from {db_name}.osu_beatmaps")
                    
                    fields = get_fields(cursor)
                    fields[0] = '_id'

                    updates = []
                    for row in cursor:
                        beatmap = dict(zip(fields, row))
                        query = {'_id': beatmap['_id']}
                        update = {'$setOnInsert': beatmap}
                        updates.append(UpdateOne(query, update, upsert=True))

                    self.mongo_inst[new_db_name]['osu_beatmaps'].bulk_write(updates)
                except Exception as e:
                    print(e)


