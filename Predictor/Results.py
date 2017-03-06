#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  5 21:45:20 2017

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
# Results
# =============================================================================
class Results(object):

    """Class to hold election results data"""

    def __init__(self, previous_election):

        """Read the election results"""

        self.results = pd.read_csv(os.path.join("Input",
                                                "ElectionResults.csv"),
                                   parse_dates=['Election date'])

    def prepare_data(self):

        """Sets the party share of the popular vote and other data prep
        tasks"""

        self.results['Total votes'] = (self.results['Democratic votes'] +
                                       self.results['Other votes'] +
                                       self.results['Republican votes'])

        self.results['Dem share'] = (self.results['Democratic votes'] /
                                     self.results['Total votes'])

        self.results['Rep share'] = (self.results['Republican votes'] /
                                     self.results['Total votes'])

        self.results['Oth share'] = (self.results['Other votes'] /
                                     self.results['Total votes'])

        self.results['Margin'] = (self.results['Dem share'] -
                                  self.results['Rep share'])

        self.results.drop(['Democratic electoral',
                           'Other electoral',
                           'Republican electoral',
                           'Democratic votes',
                           'Other votes',
                           'Republican votes',
                           'Total votes'], axis=1, inplace=True)

    def select(self, election):

        """Returns the results for a given election"""

        return self.results[self.results['Election date'] == election]
