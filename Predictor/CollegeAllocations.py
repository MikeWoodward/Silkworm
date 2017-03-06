#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  5 21:49:32 2017

@author: mikewoodward

For details of licensing etc, see the Github page:
    https://github.com/MikeWoodward/PresidentialPredictor
"""


# =============================================================================
# Imports
# =============================================================================
import os.path
import pandas as pd


# =============================================================================
# CollegeAllocations
# =============================================================================
class CollegeAllocations(object):

    """Class to hold electoral college allocations"""

    def __init__(self):

        """Read in the data file and reformat the data"""
        self.alloc = pd.read_csv(os.path.join("Input",
                                              "ElectoralCollege.csv"))

    def prepare_data(self):

        """Reformats the dataframe"""

        self.alloc = pd.melt(self.alloc,
                             id_vars=['State'],
                             var_name='Election date',
                             value_name='Allocation')

        self.alloc['Election date'] = \
            pd.to_datetime(self.alloc['Election date'])

    def select(self, election):

        """Returns the electoral college allocation for an election"""

        return self.alloc[self.alloc['Election date'] == election]
