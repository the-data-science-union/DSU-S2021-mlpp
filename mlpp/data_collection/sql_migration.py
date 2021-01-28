import pymongo
from pymongo import UpdateOne
from tqdm import tqdm


def get_fields(cursor_ex):
    return list(map(lambda c: c[0], cursor_ex.description))


class SqlDumpMigrator:

    def __init__(self, sql_inst):
        self.sql_inst = sql_inst

    def insert_user_scores(self, sql_db_name, user_id, new_db):

        with self.sql_inst.cursor() as cursor:
            cursor.execute(
                f"select * from {sql_db_name}.osu_scores_high WHERE user_id = {user_id}")
            fields = get_fields(cursor)
            fields[0] = '_id'

            user_scores = [dict(zip(fields, row)) for row in cursor]

            new_db['osu_scores_high'].insert_many(user_scores)

    def migrate_users_and_scores(self, dump_names, new_db):
        user_ids = new_db['osu_user_stats'].find({}, {})
        migrated_users = set(map(lambda u: u['_id'], user_ids))

        for db_name in dump_names:
            print(f"Importing dump users & scores: {db_name}")

            with self.sql_inst.cursor() as cursor:
                cursor.execute(f"select * from {db_name}.osu_user_stats")

                fields = get_fields(cursor)
                fields[0] = '_id'

                with tqdm(total=cursor.rowcount) as progress_bar:
                    for row in cursor:
                        user_stats = dict(zip(fields, row))

                        if user_stats['_id'] not in migrated_users:
                            new_db['osu_user_stats'].insert(user_stats)
                            self.insert_user_scores(
                                db_name, user_stats['_id'], new_db)

                            migrated_users.add(user_stats['_id'])

                        progress_bar.update(1)
            print()

    def migrate_beatmaps(self, dump_names, new_db):
        for db_name in dump_names:
            print(f"Importing dump beatmaps: {db_name}")

            with self.sql_inst.cursor() as cursor:
                cursor.execute(f"select * from {db_name}.osu_beatmaps")

                fields = get_fields(cursor)
                fields[0] = '_id'

                updates = []
                for row in cursor:
                    beatmap = dict(zip(fields, row))
                    query = {'_id': beatmap['_id']}
                    update = {'$setOnInsert': beatmap}
                    updates.append(UpdateOne(query, update, upsert=True))

                if len(updates) > 0:
                    new_db['osu_beatmaps'].bulk_write(
                        updates)

    def migrate_beatmap_attribs(self, dump_names, new_db):
        new_db['osu_beatmap_attribs'].create_index(
            [
                ('beatmap_id', pymongo.ASCENDING),
                ('mods', pymongo.ASCENDING),
                ('attrib_id', pymongo.ASCENDING)
            ],
            unique=True
        )
        
        beatmaps = new_db['osu_beatmap_attribs'].find({}, {'beatmap_id': 1})
        migrated_b_ids = set(b['beatmap_id']for b in beatmaps)
        b_attribs = []

        for db_name in dump_names:
            new_beatmaps = 0

            print(f"Extracting dump attribs: {db_name}", end = "")

            WHERE_CLAUSE = (f'WHERE beatmap_id NOT IN {tuple(migrated_b_ids)}'
                            if len(migrated_b_ids) > 1 else ''
                            )

            with self.sql_inst.cursor() as cursor:

                SELECT_STAR_ATTRIB = f"""
                    SELECT
                        beatmap_id,
                        mods,
                        17 AS attrib_id,
                        diff_unified AS value
                    FROM
                        {db_name}.osu_beatmap_difficulty
                    {WHERE_CLAUSE}
                """

                SELECT_OTHER_ATTRIBS = f"""
                    SELECT
                        beatmap_id,
                        mods,
                        attrib_id,
                        value
                    FROM
                        {db_name}.osu_beatmap_difficulty_attribs
                    {WHERE_CLAUSE}
                    ORDER BY beatmap_id, mods, attrib_id
                """

                cursor.execute(f"""
                    {SELECT_STAR_ATTRIB}
                    UNION
                    {SELECT_OTHER_ATTRIBS}
                """)

                fields = get_fields(cursor)

                for row in cursor:
                    attrib = dict(zip(fields, row))

                    if attrib['beatmap_id'] not in migrated_b_ids:
                        new_beatmaps += 1
                        migrated_b_ids.add(attrib['beatmap_id'])
                    
                    b_attribs.append(attrib)
            
            print(f" - {new_beatmaps} new beatmaps extracted")

        print("Importing all attributes")
        if len(b_attribs) > 0:
            new_db['osu_beatmap_attribs'].insert_many(b_attribs)
