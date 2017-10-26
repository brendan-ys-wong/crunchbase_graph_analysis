import pandas as pd
pd.set_option('display.max_rows', 800)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 200)
import matplotlib.pyplot as plt
import networkx as nx
from collections import Counter, defaultdict
import numpy as np
from analysis_functions_similarity import *
import graphlab
from graphlab.toolkits.cross_validation import cross_val_score, KFold


import sys
reload(sys)
sys.setdefaultencoding('utf8')

# # Data ETL Pipeline
df = pd.read_csv('/Users/brendanwong/galvanize/Capstone/crunchbase-data/investments.csv')
df = df_preprocessing(df)
# Hold-out data is from the last 6 months of 2015
mask_d = (~df['funded_year_month'].isin(['2015-07', '2015-08', '2015-09', '2015-10', '2015-11', '2015-12']))
observation_data = df[mask_d]
# I dropped user-item interaction data for investors that had less than 50 investments,
# due to the the large number of users for which this applied.
# This sparse interaction data would be expected to hurt the performance of my recommendation model.
mask_i = (observation_data.groupby('investor_name')['company_name'].apply(lambda g: len(g) >50))
observation_data_large = observation_data[(observation_data['investor_name'].isin(mask_i[mask_i].index))]
len(observation_data_large)

# # Model 1: Only using interaction data, item-similarity model, Jaccard difference, 50+ investors
interaction_data = observation_data_large[['company_name', 'investor_name']]
interaction_data.to_csv('/Users/brendanwong/galvanize/interaction_data/interaction_data.csv')
sf = graphlab.SFrame.read_csv('/Users/brendanwong/galvanize/interaction_data/interaction_data.csv')
train, test = graphlab.recommender.util.random_split_by_user(sf, user_id="company_name", item_id="investor_name", max_num_users=25000)
m1 = graphlab.recommender.item_similarity_recommender.create(observation_data=train, user_id = 'company_name', item_id = 'investor_name')
eval_1 = m1.evaluate(test2, cutoffs=[40])
eval_1


# # Model 2: Same as model 1, but using all investors
interaction_data2 = observation_data[['company_name', 'investor_name']]
interaction_data2.to_csv('/Users/brendanwong/galvanize/interaction_data/interaction_data2.csv')
sf2 = graphlab.SFrame.read_csv('/Users/brendanwong/galvanize/interaction_data/interaction_data2.csv')
train2, test2 = graphlab.recommender.util.random_split_by_user(sf2, user_id="company_name", item_id="investor_name", max_num_users=25000)
m2 = graphlab.recommender.item_similarity_recommender.create(observation_data=train2, user_id = 'company_name', item_id = 'investor_name')
eval_2 = m2.evaluate(test2, cutoffs=[40])
eval_2


# # Cross Validation
# folds = KFold(sf, num_folds=5)
# params = {'user_id':'company_name', 'item_id':'investor_name'}
# job = cross_val_score(folds, graphlab.recommender.item_similarity_recommender.create, params)
# job.get_results()



# # # Model 2: Same as model 1, but with dummifie US city as item side data
# mask = (observation_data[(observation_data['company_country_code'] == 'USA')].groupby('company_city').count() > 300)
# big_cities_list = mask[(mask['company_name'] == True)]
# cities = list(big_cities_list.index)
# dummy_df = add_cities_dummies(df, cities)
# dummy_df = dummy_df.drop(['company_permalink', 'company_city','company_category_list', 'company_country_code', 'company_state_code', 'company_region', 'investor_permalink', 'investor_country_code', 'investor_state_code', 'investor_region', 'investor_city', 'funding_round_permalink', 'funding_round_type', 'funding_round_code', 'funded_at', 'raised_amount_usd', 'funded_year', 'funded_year_month'], axis=1)
# dummy_df.to_csv('/Users/brendanwong/galvanize/interaction_data/interaction_data_2.csv')
# dummy_df_user = dummy_df.drop('investor_name', axis=1)
# dummy_df_user.to_csv('/Users/brendanwong/galvanize/interaction_data/interaction_data_2_user.csv')
#
# sf2 = graphlab.SFrame.read_csv('/Users/brendanwong/galvanize/interaction_data/interaction_data_2.csv')
# sf2_user  = graphlab.SFrame('/Users/brendanwong/galvanize/interaction_data/interaction_data_2_user.csv')
# m2 = graphlab.recommender.item_similarity_recommender.create(observation_data=sf2, user_id = 'company_name', item_id = 'investor_name', user_data=sf2_user)
# folds = KFold(sf2, num_folds=5)
# params = {'user_id':'company_name', 'item_id':'investor_name', 'user_data':sf2_user}
# job = cross_val_score(folds, graphlab.recommender.item_similarity_recommender.create, params)
# job.get_results()


# # Model 3: Item Content Data recommender
# df.head()
company_cat = observation_data_large[['company_name', 'company_category_list']]
company_cat = company_cat.drop_duplicates()
company_cat.to_csv('/Users/brendanwong/galvanize/interaction_data/company_cat.csv')
sf_cc = graphlab.SFrame.read_csv('/Users/brendanwong/galvanize/interaction_data/company_cat.csv')
sf_cc

# interaction_data_3 = observation_data_large[['company_name', 'investor_name']]
# interaction_data_3.to_csv('/Users/brendanwong/galvanize/interaction_data/interaction_data_3.csv')
# sf3 = graphlab.SFrame.read_csv('/Users/brendanwong/galvanize/interaction_data/interaction_data_3.csv')
# train, test = graphlab.recommender.util.random_split_by_user(sf3, user_id="investor_name", item_id="company_name")
av = graphlab.toolkits.feature_engineering.AutoVectorizer(features=['company_category_list'])
av.fit(sf_cc)
m3 = graphlab.recommender.item_content_recommender.create(item_data=sf_cc, item_id='company_name', item_data_transform=av)

sf_test = graphlab.SFrame({'X1':[21000],'company_name':['ZZZ_Test'], 'company_category_list': ['Analytics']})
m3.get_similar_items(['Zynga'])

sf_cc[(sf_cc['company_name'] == 'Zyncro')]
# folds = KFold(sf3, num_folds=3)
# params = {'item_id':'investor_name'}
# job = cross_val_score(folds, graphlab.recommender.item_content_recommender.create, params)
# job.get_results()

# # TFIDF Vectorizing Industry
company_cat.head()
vocab = []
vocab = [str(x).split('|') for x in company_cat['company_category_list']]
l = set()
vocab
for word in vocab:
    for i in range(len(word)):
        l.add(word[i])
len(l)
