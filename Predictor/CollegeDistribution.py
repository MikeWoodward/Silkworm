#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  5 22:04:10 2017

@author: mikewoodward

For details of licensing etc, see the Github page:
    https://github.com/MikeWoodward/PresidentialPredictor
"""


# =============================================================================
# Imports
# =============================================================================
import numpy as np
import pandas as pd


# =============================================================================
# Functions
# =============================================================================
def array_para(x):

    """Returns a list of array parameters"""
    return [x[0]] + [0]*int(x[1] - 1) + [1 - x[0]]


# =============================================================================
# CollegeDistribution
# =============================================================================
class CollegeDistribution(object):

    """Class that holds data on the electoral college daily distribution"""

    def __init__(self, dailies, alloc):

        self.dailies = dailies
        self.alloc = alloc

    def calc_dist(self):

        """Calculate the electoral college vote distribution"""

        # Create a merged array that contains the daily data and the
        # allocations
        daily_alloc = self.dailies.merge(self.alloc)

        # Now store the generator polynomial. Create a temp structure first.
        daily_alloc['D temp'] = daily_alloc[['Dem probability',
                                             'Allocation']].values.tolist()

        daily_alloc['R temp'] = daily_alloc[['Rep probability',
                                             'Allocation']].values.tolist()

        daily_alloc['Dem poly'] = daily_alloc['D temp'].apply(array_para)
        daily_alloc['Rep poly'] = daily_alloc['R temp'].apply(array_para)

        # Now work out the electoral college distribution on a daily basis
        dist_ec = []
        for date in daily_alloc['Date'].unique():

            date_alloc = daily_alloc[daily_alloc['Date'] == date]

            cum_dem = [1]
            cum_rep = [1]

            for array in date_alloc['Dem poly']:

                cum_dem = np.convolve(cum_dem, array)

            cum_dem = np.fliplr([cum_dem])[0]

            for array in date_alloc['Rep poly']:

                cum_rep = np.convolve(cum_rep, array)

            cum_rep = np.fliplr([cum_rep])[0]

            dist_ec.append({'Date': date,
                            'Democratic': cum_dem,
                            'Republican': cum_rep,
                            'D_max': np.where(cum_dem == cum_dem.max())[0][0],
                            'R_max': np.where(cum_rep == cum_rep.max())[0][0]})

        self.dist = pd.DataFrame(dist_ec)

    def get_latest(self):

        """Return the latest (most recent) Electoral College distribution."""

        t = self.dist[self.dist['Date'] ==
                      self.dist['Date'].max()]

        dem_dist = t['Democratic'].values[0].tolist()
        rep_dist = t['Republican'].values[0].tolist()

        return dem_dist, \
            rep_dist, \
            self.dist['Date'].max(), \
            dem_dist.index(max(dem_dist)), \
            rep_dist.index(max(rep_dist))
