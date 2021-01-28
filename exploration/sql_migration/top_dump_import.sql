create database IF NOT EXISTS osu_top_2021_01;
USE osu_top_2021_01;
SOURCE 2021_01_01_performance_osu_top/osu_user_stats.sql;
SOURCE 2021_01_01_performance_osu_top/osu_beatmaps.sql;
SOURCE 2021_01_01_performance_osu_top/osu_beatmap_difficulty.sql;
SOURCE 2021_01_01_performance_osu_top/osu_beatmap_difficulty_attribs.sql;
-- SOURCE 2021_01_01_performance_osu_top/osu_scores_high.sql; -- Reccomended to comment out and run on pv