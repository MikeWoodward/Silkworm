#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  5 21:22:23 2017

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
# ElectionDates
# =============================================================================
class ElectionDates(object):

    """Class to store election dates"""

    def __init__(self):

        """Read the election dates"""

        self.dates = pd.read_csv(os.path.join("Input",
                                              "ElectionDates.csv"),
                                 parse_dates=['Election date'])

    def prepare_data(self):

        self.dates['Year'] = self.dates['Election date'].dt.year

    def select(self, year):

        """Returns the election date given teh election year."""

        return self.dates[self.dates['Year'] == year]['Election date'].iloc[0]
