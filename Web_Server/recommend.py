import pandas as pd
from scipy.spatial.distance import correlation
import numpy as np
from sklearn.neighbors import NearestNeighbors


class recommend():

    def __init__(self):
        self.menu_data = None
        self.rating_data = None
        self.dish_info = None
        self.user_dish_rating_pivot = None

    def get_data(self):
        self.menu_data = pd.read_csv('Data/dishes.csv', usecols=[0, 1], encoding = 'utf-8')
        # when writing csv dynamically, there will be a blank line at the end
        self.rating_data = pd.read_csv('Data/rating.csv', usecols=[0, 1, 2])[:-1]
        # combine two datasets
        self.dish_info = pd.merge(self.menu_data, self.rating_data, left_on='DishName', right_on='DishName')

        self.user_dish_rating_pivot = pd.pivot_table(self.dish_info, values='Rating', index=['UserID'],
                                                      columns=['DishID']).fillna(0)

    # find the similarity between 2 users by using correlation
    def get_corr_dist(self, user1, user2):
        user1 = np.array(user1)
        user2 = np.array(user2)

        common_dish_ids = []
        for i in range(len(user1)):
            if user1[i] > 0 and user2[i] > 0:
                common_dish_ids.append(i)
        if len(common_dish_ids) == 0:
            return 0
        else:
            user1 = np.array([user1[i] for i in common_dish_ids])
            user2 = np.array([user2[i] for i in common_dish_ids])
            return correlation(user1, user2)

    def k_nearest_neighbour(self, current_user, k):

        corr_matrix = pd.DataFrame(index=['UserID'], columns=['correlation'])
        for i in self.user_dish_rating_pivot.index:
            # finding the correlation distance between user i and the current user and add it to the correlation matrix
            corr_matrix.loc[i] = self.get_corr_dist(self.user_dish_rating_pivot.loc[current_user],
                                                    self.user_dish_rating_pivot.loc[i])
        corr_matrix = pd.DataFrame.sort_values(corr_matrix, ['correlation'], ascending=[0])
        nearest_neighbours = corr_matrix[:k]

        predicted_dish_rating = pd.DataFrame(index=['DishID'], columns=['rating'])
        predicted_rating = 0

        # iterating all dishes for a current user
        for i in self.user_dish_rating_pivot.columns:
            for j in corr_matrix.index[:k]:
                if self.user_dish_rating_pivot.loc[j, i] > 0:
                    predicted_rating += ((self.user_dish_rating_pivot.loc[j, i]) *
                                         nearest_neighbours.loc[j, 'correlation'])

            predicted_dish_rating.loc[i, 'rating'] = predicted_rating

        return predicted_dish_rating

    # generate top n recommendations for a current user
    def recommend_n_dishes(self, current_user, n):
        dishes_already_eaten = list(self.user_dish_rating_pivot.loc[current_user]
                                    .loc[self.user_dish_rating_pivot.loc[current_user] > 0].index)

        predicted_dish_rating = self.k_nearest_neighbour(current_user, 6).drop(dishes_already_eaten)

        top_n_ratings = pd.DataFrame.sort_values(predicted_dish_rating, ['rating'], ascending=[0])[:n]
        top_n_dishes = self.menu_data.loc[self.menu_data.DishID.isin(top_n_ratings.index)]
        result = list(top_n_dishes.DishName)

        return result
