#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: silkworm.

Description:
Silkworm is a poll-based US Presidential Election forecaster.

Author: Mike Woodward

Created on: 2020-07-26

"""

# %%---------------------------------------------------------------------------
# Module metadata
# -----------------------------------------------------------------------------
__author__ = "Mike Woodward"
__license__ = "MIT"


# %%---------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import numpy as np
import pandas as pd
import numpy
import scipy
import scipy.special


# %%---------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------
def generator_polynomial(probability, allocation):
    """
    Calculate the generator polynomial.

    int is needed because of minor Pandas requirement.
    """
    return [probability] + [0]*int(allocation - 1) + [1 - probability]


# %%---------------------------------------------------------------------------
# ElectorlCollegeModelModel
# -----------------------------------------------------------------------------
class ElectoralCollegeModel():
    """Models the state election results."""

    # %%
    def __init__(self,
                 state,
                 allocations,
                 election_year):
        """Initialize."""
        self.year = election_year
        self.state = state
        self.allocations = allocations

    # %%
    def setup(self):
        """
        Set up the data structures.

        Riskier setup done here, so init method less likely to fail.
        """
        self.state = self.state.merge(
            self.allocations[
                self.allocations['Year'] == self.year][['State abbreviation',
                                                        'Allocation']],
            on='State abbreviation',
            how='inner')

    # %%
    def update(self):
        """Update the electoral college forecast with state data."""
        _ecv = (self.allocations
                    .query('Year == {0}'
                           .format(self.year))['Allocation']
                    .sum())

        # Sort state data by date and by electoral college vote allocation
        self.state = self.state.sort_values(by=['Date', 'Allocation'])

        # Create the generator polynomials for each date/state/party
        self.state['Democratic polynomial'] = \
            self.state.apply(lambda x: generator_polynomial(
                x['Democratic probability'], x['Allocation']), axis=1)
        self.state['Republican polynomial'] = \
            self.state.apply(lambda x: generator_polynomial(
                x['Republican probability'], x['Allocation']), axis=1)

        # Pre-allocate to avoid appends growing piece by piece
        pdf_max = [None]*self.state['Date'].nunique()
        df_ec = [None]*self.state['Date'].nunique()

        # Go through every date working out the electoral college PDF
        for index, date in enumerate(self.state['Date'].unique()):

            date_slice = self.state[self.state['Date'] == date]

            cum_dem = [1]
            for array in date_slice['Democratic polynomial']:
                cum_dem = np.convolve(cum_dem, array)
            cum_dem = np.fliplr([cum_dem])[0]

            cum_rep = [1]
            for array in date_slice['Republican polynomial']:
                cum_rep = np.convolve(cum_rep, array)
            cum_rep = np.fliplr([cum_rep])[0]

            pdf_max[index] = {
                'Date': date,
                'Democratic maximum': np.where(cum_dem == cum_dem.max())[0][0],
                'Republican maximum': np.where(cum_rep == cum_rep.max())[0][0]
                }

            df_ec[index] = pd.DataFrame(
                {'Date': [date]*(_ecv+1),
                 'Electoral college vote': list(range(_ecv + 1)),
                 'Democratic distribution': cum_dem,
                 'Republican distribution': cum_rep})

        self.electoral_distribution = pd.concat(df_ec)
        self.electoral_maximum = pd.DataFrame(pdf_max)
