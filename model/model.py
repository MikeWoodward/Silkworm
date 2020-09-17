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
import os
import glob
import pandas as pd
import requests
# try-except to handle execution as a standalone and as part of Bokeh
# application
try:
    from model.statemodel import StateModel
    from model.electoralcollegemodel import ElectoralCollegeModel
except ModuleNotFoundError:
    from statemodel import StateModel
    from electoralcollegemodel import ElectoralCollegeModel


# %%---------------------------------------------------------------------------
# Decorators
# -----------------------------------------------------------------------------
def reset_error(func):
    """Reset error handling."""

    def func_wrapper(*args):
        """Reset error handling."""
        args[0].error_status = False
        args[0].error_message = ''
        return func(*args)
    return func_wrapper


# %%---------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
RAWDATA = 'rawdata'
PROCESSEDDATA = 'processeddata'


# %%---------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------
class Model():
    """Class Model is part of the model-view-controller architecture.

    It contains the data model - the data used in the application.
    """

    # %%
    @reset_error
    def __init__(self):
        """Initialize object. First part of two-part initialization.

        Put initialization code here that's very unlikely to fail. This
        approach enables us to build a UI that can handle error messages
        before errors occur.
        """
        self.model_folder = os.path.dirname(os.path.realpath(__file__))

        self.summary = None
        self.allocations = None
        self.results = None
        self.polls = None
        self.electoral = None
        self.state = None

    # %%
    @reset_error
    def read_rawdata(self):
        """Read in the raw data necessary to make a forecast."""
        # State names
        # ===========
        names = pd.read_csv(os.path.join(self.model_folder,
                                         RAWDATA,
                                         'StateNames.csv'))

        # Election summary
        # ================
        self.summary = pd.read_csv(os.path.join(self.model_folder,
                                                RAWDATA,
                                                'ElectionSummary.csv'),
                                   parse_dates=['Election date'])

        # Electoral college allocations
        # =============================
        self.allocations = pd.read_csv(
            os.path.join(self.model_folder,
                         RAWDATA,
                         'ElectoralCollegeAllocations.csv'))
        # Reformat data
        states = self.allocations['State abbreviation'].tolist()
        self.allocations = (
            self.allocations.set_index('State abbreviation')
            .transpose()
            .reset_index()
            .fillna(0)
            .rename(columns={'index': 'Year'}))
        self.allocations = pd.melt(self.allocations,
                                   id_vars=['Year'],
                                   value_vars=states,
                                   var_name='State abbreviation',
                                   value_name='Allocation')
        # Tidying up
        self.allocations['Allocation'] = \
            self.allocations['Allocation'].astype(int)
        self.allocations['Year'] = \
            self.allocations['Year'].astype(int)

        # Election results
        # ================
        self.results = pd.read_csv(os.path.join(self.model_folder,
                                                RAWDATA,
                                                'ElectionResults.csv'))

        # Polls
        # =====
        self.polls = pd.read_csv(os.path.join(self.model_folder,
                                              RAWDATA,
                                              'Polls_2020.csv'),
                                 parse_dates=['start_date',
                                              'end_date'])

        # Renaming and tidying up data
        # ----------------------------
        # Rename columns - renaming any columns I need to merge on or
        # that I alter in some way
        self.polls = (self.polls.rename(
                        columns={'cycle': 'Year',
                                 'candidate_party': 'Party',
                                 'candidate_name': 'Candidate name',
                                 'state': 'State name'}))
        # Add a state abbreviations column
        self.polls = self.polls.merge(names,
                                      on='State name',
                                      how='left')

        # Change dataframe contents
        replace_dict = [{'col': 'Party', 'old': 'DEM', 'new': 'Democratic'},
                        {'col': 'Party', 'old': 'REP', 'new': 'Republican'},
                        {'col': 'Candidate name',
                         'old': 'Biden', 'new': 'Joe Biden'},
                        {'col': 'Candidate name',
                         'old': 'Trump', 'new': 'Donald Trump'}]
        for replace in replace_dict:
            self.polls.loc[
                self.polls[
                    replace['col']].str.contains(
                        replace['old']), replace['col']] = replace['new']

        # Filtering - generic
        # -------------------
        # Filter for state polls, just Democratic and Republican and
        # for just two named candidates
        self.polls = self.polls[(~self.polls['State name'].isnull()) &
                                (self.polls['Party'].isin(['Democratic',
                                                           'Republican'])) &
                                (self.polls['Year'] == 2020) &
                                (self.polls['Candidate name'].isin(
                                    ['Donald Trump', 'Joe Biden']))]
        # Some polls are for hypothetical match ups and removing candidates who
        # didn't make the final ticket can leave us with odd results,
        # so we need to remove all surveys and questions where just one
        # candidate is left after the previous clean up.
        two_candidates = (self.polls[['poll_id',
                                      'question_id',
                                      'Candidate name']]
                          .groupby(['poll_id', 'question_id'])
                          .nunique()['Candidate name']
                          .reset_index()
                          .query('`Candidate name` == 2')
                          [['poll_id', 'question_id']]
                          .drop_duplicates())
        self.polls = self.polls.merge(two_candidates,
                                      on=['poll_id', 'question_id'],
                                      how='inner')

        # Filtering - poll specific
        # -------------------------
        # Some polls require qualification, e.g. the same results are
        # presented in two or more seperate ways. We need to filter specific
        # polls here.

        # Higher and lower likelihood of turnout - some Monmouth
        # polls report three variants - remove higher and lower variants
        self.polls = self.polls[
            ~(
                (self.polls['poll_id'].isin([67821, 67101, 67920, 69464])) &
                (self.polls['notes'].isin(['lower likely turnout',
                                           'higher likely turnout']))
              )]

        # Arizona poll where second question is a head-to-head Trump vs. Biden
        self.polls = self.polls[~((self.polls['poll_id'] == 67934) &
                                  (self.polls['question_id'] == 127187))]
        # Colorado poll where second question is a head-to-head Trump vs. Biden
        self.polls = self.polls[~((self.polls['poll_id'] == 69433) &
                                  (self.polls['question_id'] == 129320))]
        # Florida poll where second question is a head-to-head Trump vs. Biden
        self.polls = self.polls[~((self.polls['poll_id'] == 66308) &
                                  (self.polls['question_id'] == 123433))]
        # Iowa poll where second question is a head-to-head Trump vs. Biden
        self.polls = self.polls[~((self.polls['poll_id'] == 67935) &
                                  (self.polls['question_id'] == 127189))]
        # Maine polls represent a challenge, for now, we'll just remove
        # Congressional District polls
        self.polls = self.polls[~self.polls['State name'].isin(
            ['Maine CD-1', 'Maine CD-2'])]
        # Maine poll where second question is a head-to-head Trump vs. Biden
        self.polls = self.polls[~((self.polls['poll_id'] == 67936) &
                                  (self.polls['question_id'] == 127191))]
        # Michigan poll where question 123714 seems to exclude 3rd parties
        self.polls = self.polls[~((self.polls['poll_id'] == 66406) &
                                  (self.polls['question_id'] == 123714))]
        # Michigan poll - 2nd option not clear
        self.polls = self.polls[~((self.polls['poll_id'] == 57656) &
                                  (self.polls['question_id'] == 93510))]
        # Michigan poll - 2nd option not clear
        self.polls = self.polls[~((self.polls['poll_id'] == 58192) &
                                  (self.polls['question_id'] == 94749))]
        # Nebraska polls represent a challenge, for now, we'll just remove
        # Congressional District polls
        self.polls = self.polls[~self.polls['State name'].isin(
            ['Nebraska CD-1', 'Nebraska CD-2'])]
        # New Hampshire poll with two presentations
        self.polls = self.polls[
            ~((self.polls['poll_id'] == 62978) &
              (self.polls['notes'] ==
               'split sample without undecided option'))]
        # North Carolina poll where second question is a head-to-head
        # Trump vs. Biden
        self.polls = self.polls[~((self.polls['poll_id'] == 67937) &
                                  (self.polls['question_id'] == 127193))]
        # North Carolina poll where second question is a head-to-head
        # Trump vs. Biden
        self.polls = self.polls[~((self.polls['poll_id'] == 68464) &
                                  (self.polls['question_id'] == 128157))]
        # Pennsylvania poll where second question is a head-to-head
        # Trump vs. Biden
        self.polls = self.polls[~((self.polls['poll_id'] == 68264) &
                                  (self.polls['question_id'] == 127878))]
        # Pennsylvania poll where second question is a head-to-head
        # Trump vs. Biden
        self.polls = self.polls[~((self.polls['poll_id'] == 68319) &
                                  (self.polls['question_id'] == 127966))]
        # # Utah poll - use UCEP educational model for now
        self.polls = self.polls[
            ~((self.polls['poll_id'] == 66525)
              & ((self.polls['notes'].isin(
                  ['CNN education weighting',
                   'CPS education weighting',
                   'CCES education weighting']))
                  | (self.polls['notes'].isna())))]
        # Wisconsin poll - 2nd option not clear
        self.polls = self.polls[~((self.polls['poll_id'] == 57697) &
                                  (self.polls['question_id'] == 93617))]

        # Filtering - population type
        # ---------------------------
        # Some polls report likely votes and registered voters etc, we will
        # preferentially select in this order: lv, rv, v, a - selecting
        # one and only one variant
        # A = ADULTS RV = REGISTERED VOTERS V = VOTERS LV = LIKELY VOTERS

        # Step 1: check that there are no other population types. This isn't
        # a show stopping error, so just report it.
        if (sorted(self.polls['population'].unique()) !=
                sorted(['lv', 'rv', 'v', 'a'])):
            self.error_status = True
            self.error_message = ("""Found an unexpected voter population """
                                  """type in the polls data file.""")

        # Step 2: introduce a population rank
        df = pd.DataFrame({'population': ['lv', 'rv', 'v', 'a'],
                           'population_rank': [1, 2, 3, 4]})
        self.polls = self.polls.merge(
            df,
            on='population',
            how='inner')

        # Step 3: Find the poll variants with the lowest (best) rank
        best_variants = (self.polls[['poll_id', 'population_rank']]
                         .groupby('poll_id')
                         .min()
                         .reset_index())

        # Step 4: Select just those poll variants
        self.polls = self.polls.merge(best_variants,
                                      on=['poll_id', 'population_rank'],
                                      how='inner')

        # Step 5: Remove the population_rank column
        self.polls = self.polls.drop(columns=['population_rank'])

        # Final filtering and formatting
        # ------------------------------
        self.polls = self.polls[['question_id',
                                 'poll_id',
                                 'pollster',
                                 'start_date',
                                 'end_date',
                                 'Year',
                                 'State abbreviation',
                                 'sample_size',
                                 'Party',
                                 'pct']]

        # This format is slightly easier to use
        self.polls = self.polls.pivot_table(index=['question_id',
                                                   'poll_id',
                                                   'pollster',
                                                   'start_date',
                                                   'end_date',
                                                   'Year',
                                                   'State abbreviation',
                                                   'sample_size'],
                                            columns='Party',
                                            values='pct').reset_index()
        # Now calculate the spread. Note, we're using a a proportion, not a %.
        self.polls['Spread D-R'] = (self.polls['Democratic']
                                    - self.polls['Republican'])/100

        # Final checks
        # ------------
        # Check state names and abbreviations are OK and we have 100%
        # coverage
        temp_ = self.polls[self.polls['State abbreviation'].isna()]
        if not temp_.empty:
            self.error_status = True
            self.error_message = ("""Found mismatch between state names and """
                                  """abbreviations in polling data.""")

    # %%
    @reset_error
    def get_years(self):
        """Get the years for which we have data or have run analysis."""
        years = {'summary': [],
                 'allocations': [],
                 'results': [],
                 'polls': [],
                 'analysis': []}

        if self.summary is not None and 'Year' in self.summary:
            years['summary'] = (
                self.summary.sort_values('Year', ascending=False)['Year']
                            .unique()
                            .tolist())

        if self.allocations is not None and 'Year' in self.allocations:
            years['allocations'] = (
                self.allocations.sort_values('Year', ascending=False)['Year']
                                .unique()
                                .tolist())

        if self.results is not None and 'Year' in self.results:
            years['results'] = (
                self.results.sort_values('Year', ascending=False)['Year']
                            .unique()
                            .tolist())

        if self.polls is not None and 'Year' in self.polls:
            years['polls'] = (
                self.polls.sort_values('Year', ascending=False)['Year']
                          .unique()
                          .tolist())

        # Get years for the analysis that's already been done.
        _files = [file.split('/')[-1] for file in
                  glob.glob(os.path.join(self.model_folder,
                                         PROCESSEDDATA,
                                         r'*.csv'))]
        _years = set([file[-8:-4] for file in _files])
        years['analysis'] =\
            [int(year) for year in _years
             if 'electoral_maximum_{0}.csv'.format(year) in _files
             and 'electoral_distribution_{0}.csv'.format(year) in _files
             and 'state_{0}.csv'.format(year) in _files
             and 'processed_polls_{0}.csv'.format(year) in _files]
        return years

    # %%
    @reset_error
    def cross_check(self):
        """Cross check that the data is consistent."""
        text = []

        # Data present
        # ============
        files = {'Summary': self.summary,
                 'Allocations': self.allocations,
                 'Results': self.results,
                 'Polls': self.polls}

        for k, v in files.items():
            if v is not None and 'Year' in v:
                text.append("{0} data file present.".format(k))
            else:
                text.append("{0} data NOT file present.".format(k))
                self.error_status = True

        # Allocations agree
        # =================
        summary = (self.summary[['Year',
                                 'Electoral College total']]
                   .rename(columns={'Electoral College total': 'Allocation'})
                   .sort_values(['Year'], ascending=False))
        allocations = (self.allocations[['Year', 'Allocation']]
                       .groupby(['Year'])
                       .sum()
                       .reset_index())
        results = (self.results
                   .groupby('Year')
                   .sum()
                   .reset_index()
                   .assign(Allocation=lambda x:
                           x['Democratic electoral'] +
                           x['Other electoral'] +
                           x['Republican electoral'])[['Year', 'Allocation']])

        college = {'Allocations': allocations,
                   'Results': results}

        for k, v in college.items():

            combo = summary.merge(v,
                                  on=['Year', 'Allocation'],
                                  how='right',
                                  indicator=True)

            if combo[combo['_merge'] != 'both'].empty:
                text.append(
                    '{0} - electoral college allocations agree.'.format(k))
            else:
                text.append("{0} - electoral college allocations don't agree. "
                            "Table of disagreements follows.".format(k))
                text.append(combo[combo['_merge'] != 'both'].to_html())
                self.error_status = True

        # Polls consistent
        # ================
        # Find potential duplicates
        pot_dups = (self.polls[['poll_id', 'question_id']]
                    .groupby(['poll_id'])
                    .nunique()
                    .query('question_id > 1')
                    [['question_id']]
                    .reset_index()['poll_id'])
        if not pot_dups.empty:
            text.append("Found unhandled potential duplicate polls in "
                        "polling file. ")
            text.append(str(pot_dups.to_list()))
            self.error_message = ("""Found unhandled potential duplicate """
                                  """polls in polling file. """
                                  """Duplicate are: {0}."""
                                  .format(str(pot_dups.to_list())))
            self.error_status = True
        else:
            text.append('Poll data has no duplicate questions.')

        return '\n'.join(text)

    # %%
    @reset_error
    def fetch_polls(self, year):
        """Fetch polling data from 538."""
        if year == 2020:
            url = ("""https://projects.fivethirtyeight.com"""
                   """/polls-page/president_polls.csv""")
            request = requests.get(url)
            if request.status_code != 200:
                self.error_status = True
                self.error_message = ("""model.fetch_polls returned """
                                      """an error code of {0}."""
                                      .format(request.status_code))
                return
            with open(os.path.join(self.model_folder,
                                   RAWDATA,
                                   "polls_2020.csv"),
                      "wb") as poll_file:
                poll_file.write(request.content)

    # %%
    @reset_error
    def calculate_forecast(self, year):
        """Forecast the results of the Presidential election."""
        # State model
        # ===========
        # Build the state model
        statemodel = StateModel(results=self.results,
                                polls=self.polls,
                                election_year=year)
        # Sets up more risky intialization that might fail
        statemodel.setup()
        # Calculates the state-level model
        statemodel.update()

        # Write the state data to disk
        statemodel.state.to_csv(os.path.join(self.model_folder,
                                             PROCESSEDDATA,
                                             'state_{0}.csv'.format(year)),
                                index=False)

        # Electoral college data
        # ======================
        # Now build the electoral college forecast model
        electoralmodel = ElectoralCollegeModel(state=statemodel.state,
                                               allocations=self.allocations,
                                               election_year=year)
        electoralmodel.setup()
        # Calculates the electoral college model
        electoralmodel.update()

        # Write the electoral college data to disk
        electoralmodel.electoral_maximum.to_csv(
            os.path.join(self.model_folder,
                         PROCESSEDDATA,
                         'electoral_maximum_{0}.csv'.format(year)),
            index=False)
        electoralmodel.electoral_distribution.to_csv(
            os.path.join(self.model_folder,
                         PROCESSEDDATA,
                         'electoral_distribution_{0}.csv'.format(year)),
            index=False)

        # Polling data
        # ============
        # Not really a forecast, but this is a convenient place to write
        # the cleaned up polling data to disk.
        self.polls.to_csv(
            os.path.join(self.model_folder,
                         PROCESSEDDATA,
                         'processed_polls_{0}.csv'.format(year)),
            index=False)

    # %%
    @reset_error
    def load_forecast(self, year):
        """Read in the forecast data, if present."""
        # Electoral college
        # =================
        self.electoral_maximum = pd.read_csv(
            os.path.join(self.model_folder,
                         PROCESSEDDATA,
                         'electoral_maximum_{0}.csv'.format(year)),
            parse_dates=['Date'])
        self.electoral_distribution = pd.read_csv(
            os.path.join(self.model_folder,
                         PROCESSEDDATA,
                         'electoral_distribution_{0}.csv'.format(year)),
            parse_dates=['Date'])

        # State forecasts
        # ===============
        self.state = pd.read_csv(
            os.path.join(self.model_folder,
                         PROCESSEDDATA,
                         'state_{0}.csv'.format(year)),
            parse_dates=['Date'])
        _names = pd.read_csv(os.path.join(self.model_folder,
                                          RAWDATA,
                                          'StateNames.csv'))
        # Add in the State names - makes it easier to display results
        self.state = self.state.merge(_names,
                                      on='State abbreviation',
                                      how='left')
        # Polls
        # =====
        # Not really a forecast, but the processed polling data is used
        # by the same display code that uses forecasts.
        self.polls = pd.read_csv(
            os.path.join(self.model_folder,
                         PROCESSEDDATA,
                         'processed_polls_{0}.csv'.format(year)),
            parse_dates=['start_date', 'end_date'])
        # Add in the State names - makes it easier to display results
        self.polls = self.polls.merge(_names,
                                      on='State abbreviation',
                                      how='left')
        # Only polls from January 1 of year onwards
        start_date = pd.to_datetime('{0}-01-01'.format(year))
        self.polls = self.polls[self.polls['end_date'] >= start_date]


# %%
# Code to test the model
if __name__ == "__main__":

    model = Model()
    print("*******")

    print("read_rawdata")
    model.read_rawdata()
    print("Error status: {0}".format(model.error_status))
    print("Error string: {0}".format(model.error_message))
    print('*******')

    print('get years')
    print(model.get_years())
    print("Error status: {0}".format(model.error_status))
    print("Error string: {0}".format(model.error_message))
    print("*******")

    print("cross_check results")
    print(model.cross_check())
    print('Errors:')
    print("Error status: {0}".format(model.error_status))
    print("Error string: {0}".format(model.error_message))
    print("*******")

    # print("Fetch 538 data")
    # model.fetch_polls(2020)
    # print('Errors:')
    # print("Error status: {0}".format(model.error_status))
    # print("Error string: {0}".format(model.error_message))

    model.calculate_forecast(2020)
    model.load_forecast(2020)
