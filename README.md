# osu! MLpp

## Members
Project Lead: Victor Lin

Project Members:

Winter & Spring - Sophie Yun, Justin Kaufman, Marco Scialanga, Emily Gong, Karen Nguyen

Spring - Trach Zhao, Gilbert Neuner, Sine Polcharoen, Elizabeth Gallmeister

## Objective

Explore "Learning to Rank" algorithms for the rhythm game osu! with large player datasets and applications to other ranking systems

## Introduction
MMOs (Massively Multiplayer Online Game) commonly face difficulties in accurately ranking their players. This is certainly the case for the popular rhythm game [osu!](https://osu.ppy.sh/) since the release of ppv1 in 2012, its first global player ranking algorithm. Since then, improvements have been made to its successor, ppv2, but a **traditional programming approach** has continued to dominate discussion, where hand-written algorithms and equations attempt to model the complex factors associated with determining a player's skill/proficiency at the game. However, this approach is vulnerable to subjective and contradictory perspectives on how skill in the game, and thereby how player points are rewarded, should be defined. We can clearly see this struggle to map algorithmic code to the complicated processes in osu! in parts of ppv2's source code:

```
// Lots of arbitrary values from testing.
// Considering to use derivation from perfect accuracy in a probabilistic manner - assume normal distribution
_accValue =
  pow(1.52163f, beatmap.DifficultyAttribute(_mods, Beatmap::OD)) * pow(betterAccuracyPercentage, 24) *
  2.83f;
```
Source: https://github.com/ppy/osu-performance/blob/master/src/performance/osu/OsuScore.cpp

With millions of active players, osu! has sufficient player activity to be loosely considered big data. This project, osu! MLpp, attempt to leverage the different public data sources in osu! to explore a more objective and machine learning-based approach that avoids resorting to "arbritrary values from testing" and "assumptions".

## Methodology
With a team of 10 members, the project approached collaborative research with a centralized framework. MLpp leveraged aws resources to centralize it's codebase and data, using github primarily for public sharing. Due to it's rich querying and processing syntax and scalability for big data (> 10 GB), MongoDB was a more suitable choice for the project's data storage in comparison to other databases and file-based representations.

## Data Acquistion
The osu! performance repository contains a [public data dump](http://data.ppy.sh/) that samples data points from 10,000 randomly chosen users each month. While this provided a sufficient _quantity_ of data, MLpp layed out strict _quality_ specifications concerned with bias, richness, and granularity of data that weren't readily addressed by the existing dumps. Thus, MLpp took additional steps in gathering high quality data that would be incorproated into analysis and modeling.

### Revised Player Sampling - Even Skill Distribution
In particular, we found the osu_scores_high table, which contains the high scores (best performances) of each beatmap (terminology for a 'game level' in osu!) the 10,000 users have played, to be extremely valuable to training models that would attempt to assign a number to each player performance. However, such a model would require a relatively even distribution of datapoints from players at all skill-levels in the game. On the contrary, we found the skill distribution of the random 10k user set to be strongly left skewed due to a far lower proportion of players who stick with the game and acquire a high skill-level:

![Random Sampling vs Biased Sampling](https://github.com/the-data-science-union/dsu-mlpp/blob/main/images/random_vs_biased_sampling.png)

The two histograms compare random sampling with our revised sampling function. The x-axis roughly represents skill and the y-axis counts the number of players sampled at each skill range. We can see the random sample is strongly skewed and has an error of 40%, which is determined by it's percent area displacement from an even distribution. The revised function biases the probability of sampling a player depending on their current skill-level, resulting in a more even distribution and lower displacement error. **The revised sampling function was proposed to osu! head developers and accepted as an alternative dataset in the archive.** The proposed function takes on the following exponential form, with s being the player's total pp (terminology for 'skill level' in osu!) and p being the probability of sampling the player:

![Biased Sampling Function Formula](https://github.com/the-data-science-union/dsu-mlpp/blob/main/images/sampling_function_eq.png)

### Estimating Missing Values - Player Historical pp
The existing archive only provides each player's current pp value and not a timeline of their pp over time since account creation. Knowing the pp at the time of each performance found in osu_scores_high would be extremely valuable to gauging skill level at time of play. Thus, MLpp estimated the pp at time of play by assuming each player's pp is primarily comprised of their high scores on each beatmap. With this assumption, the osu_scores_high dataset can be used to plot a player's estimated pp over time. We compared our estimation to an existing website that stores a comprehensive timeline of pp for a small, select group of players with astonishingly similar results:

![Estimated Player Historical pp](https://github.com/the-data-science-union/dsu-mlpp/blob/main/images/est_pp_line_chart.png)

## Data Modeling
MLpp explored 3 ways in which acquired game data could be used to provide insight and improvements to existing algorithms
- **Beatmap Failtimes Prediction**: Predicted player fail chance for beatmaps using XGBoost Random Forest Regression Model
- **Beatmap Difficulty Recalculation**: Adjusted  difficulty scores for beatmaps using Elo Rating System
- **Ranking System Validation/Testing**: Developed alternative method to discover over-weighted beatmaps

### Beatmap Failtimes Prediction (Sophie Yun, Emily Gong, Sine Polcharoen)
We predicted failtimes by looking at measurements of each hit object within a certain time interval. This should provide a more accurate estimation than the current difficulty rating system. This can also be helpful in predicting other metrics, such as performance points. All these come down to encourage head developers to collect more specific data and therefore to create better beatmaps that are tailored to players at different skill levels.
**Our Goal:** By extracting all the attributes about **hit objects**, which include locations (x, y, x1, y1), repeat_count, duration, d_time, and time, we hope to predict **failtimes** for some of the most popular **beatmaps** in the osu! system.

#### Summarizing & Tabulating Beatmaps
We retrieved data on 500 beatmaps with a difficulty rating of 1.5 to 2. These beatmaps are on the easier side, so there will be greater amount of players attempting to play them. This means that we will have a more hollistic data set, covering players of various player levels. For our model, we do not want a large amount of higher-level players, because that could heavily skew our model. For each beatmap, hit objects were grouped into intervals and averaged to create a tabular dataset:

|    |   x |   y |   x1 |   y1 |   repeat_count |   duration |   d_time |   time |
|---:|----:|----:|-----:|-----:|---------------:|-----------:|---------:|-------:|
|  0 |  64 | 320 |   64 |  320 |              1 |          0 |     5538 |   5538 |
|  1 |  64 | 192 |   64 |  192 |              1 |          0 |      697 |   6235 |
|  2 |  64 |  64 |   64 |   64 |              1 |          0 |      698 |   6933 |
|  3 | 448 |  64 |  448 |   64 |              1 |          0 |     1395 |   8328 |
|  4 | 448 | 192 |  448 |  192 |              1 |          0 |      698 |   9026 |
|  ..| ... | ... |  ... |  ... |              . |          . |      ... |   .... |


#### Linear Regression
We attempted a Linear Regression Model. However, after looking at diagnostic plots, it is clear that our data does fit the assumptions of linear regression. Thus, we will look at another approach.

<p float="left">
  <img src="https://github.com/the-data-science-union/dsu-mlpp/blob/main/images/failtimes_linear_scatter.png" width="440" />
  <img src="https://github.com/the-data-science-union/dsu-mlpp/blob/main/images/failtimes_linear_pplot.png" width="400" />
</p>

#### KNN Regression
We attempted a KNN Regression Model. However, after doing research into the topic, we found that KNN models work best with 2 predictors. Since our data has over 2 predictors, we concluded that the KNN Regression Model was not the right choice for this problem.

#### XGBoost Random Forest Regression
We had much better success with the random forest model from the XGBoost package. The model produced a rmse of 6.73% and closely predicts failrate in the beatmap even when failrate is volatile and spikes.

![XGboost Prediction Line Chart](https://github.com/the-data-science-union/dsu-mlpp/blob/main/images/failtimes_xgboost_prediction.png)

### Beatmap Difficulty Recalculation (Karen Nguyen, Tracy Zhao, Elizabeth Gallmeister)

#### Elo Preprocessing
The ELO rating in our case is the scaled beatmaps average score. The difference in the ELO rating serves as a predictor of the outcome of a match-up between two beatmaps. ELO is based on pair-wise comparisons; after every match, the winning beatmap takes points from the losing beatmap. The difference between the ELO rating of the winner and loser determines the total number of points gained or lost after a match-up. If the outcome is as predicted, only a few points are added to the winner's rating/taken from the loser's rating. We took the 1000 most popular beatmaps and ran through every possible match-up to finalize our ELO ratings, which represent our new beatmap difficulty scores. 

We scaled the existing beatmap difficulty ratings by a factor of 300 in order to implement the ELO algorithm because the average ELO score is usually around 1500, based off our research. 

We also randomized the order of beatmaps in our dataframe because the pairwise comparisons are performed sequentially, so the order matters. 

|    |   index |       Beatmap id |   playcount |   Difficulty rating |   Scaled Difficulty Rating |
|---:|--------:|-----------------:|------------:|--------------------:|---------------------------:|
|  0 |     585 | 118226           | 2.60438e+06 |             5.62648 |                   1687.94  |
|  1 |     998 |      1.07737e+06 | 1.82553e+06 |             3.59548 |                   1078.64  |
|  2 |     345 | 719594           | 3.59722e+06 |             5.21833 |                   1565.5   |
|  3 |     514 | 537630           | 2.81615e+06 |             3.31143 |                    993.429 |
|  4 |     860 | 135247           | 2.01899e+06 |             4.41289 |                   1323.87  |

#### Elo Simulation
Using player scores, we simulated "matches" between beatmaps and applied the elo update function. We rescaled our ELO ratings down by 300, so that the range of beatmap difficulty scores is roughly between 0 and 10, similar to the original beatmap difficulty scores. We compared the existing distribution of difficulties with our revised difficulty values and found they were similar:

![New Difficulty Distribution](https://github.com/the-data-science-union/dsu-mlpp/blob/main/images/difficulty_ppv2_vs_elo.png)

## Conclusion
Our exploration of the application of an ML and big data approach towards different facets of osu!'s ranking system shows potential for further refinement and real application to rhythm games and MMOs in general. With respect to predicting beatmap failtimes and difficulty, random forest and pair-wise comparison models appear to arrive at similar results to the existing system's algorithms. This does not mean that the potential of an ML-based approach will be capped by the existing system. Considering we have already shown MLpp achieving similar behavior to the existing system, an ML approach bears several advantages over traditional programming for player ranking in the future. The objectivity and flexibility of ML models in this scenario means that, in a real application, such a ranking model can adopt minimal assumptions and avoid individual biases that commonly create controversy in the player-base. Furthermore, ML models would excel at continous adaption to changing metas, player behavior, etc. that would simply require the model to be retrained on fresh data. The existing system, on the other hand, struggles with this adaptability to the changing in-game environment.
