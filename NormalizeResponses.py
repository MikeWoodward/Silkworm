#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 17:54:57 2017

@author: mikewoodward
"""

import os.path
from os import listdir
import pandas as pd

# =============================================================================
# Main
# =============================================================================
if __name__ == '__main__':

    election = {'2008': u'2008-11-04',
                '2012': u'2012-11-06',
                '2016': u'2016-11-08'}

    raw_dir = 'RawPollResponses'
    normal_dir = 'NormalizedPollResponses'
    normal_file_name = 'NormalizedPollResponses.csv'

    year = '2016'

    print ""
    print "▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉"
    print "▉ NormalizeResponses ▉"
    print "▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉"
    print ""

    polls = pd.DataFrame()

    # Read in all the response data files
    # -----------------------------------

    print "Reading in raw response files"

    # Get the file listing
    files = listdir(raw_dir)

    # Filter so we're only using the right files
    filtered_files = []

    poll_responses = []

    for file_name in files:

        if '-responses.tsv' in file_name and year in file_name:
            filtered_files.append(file_name)

            state = file_name[5:7]

            temp = pd.read_csv(os.path.join(raw_dir, file_name),
                               sep='\t',
                               parse_dates=True,
                               infer_datetime_format=True,
                               converters={'question_text': str})

            temp['State'] = state

            polls = polls.append(temp)

    # Normalize data
    # --------------

    print "Normalizing data"

    # Get rid of columns we don't want in the next stage of the analysis
    polls.drop(['survey_house',
                'question_text',
                'margin_of_error',
                'mode',
                'partisanship',
                'partisan_affiliation',
                'response_text',
                'sample_subpopulation'],
               axis=1, inplace=True)

    # Pivot the table to make the contents of the pollster_label (which is the
    # politicians' last names) columns
    polls = pd.pivot_table(polls,
                           values='value',
                           columns='pollster_label',
                           index=['poll_slug',
                                  'observations',
                                  'start_date',
                                  'end_date',
                                  'State'],
                           fill_value=0)

    # We don't want the index, it makes subsequent operations more difficult
    polls.reset_index(inplace=True)

    # The Other column is everyone except the Democratic and Republican
    # candidates
    polls['Other'] = polls['Other'] + polls['Johnson'] + polls['McMullin']
    polls.drop(['Johnson', 'McMullin'], axis=1, inplace=True)

    polls['Election date'] = election[year]

    # Set the names to be the names expected in the next stage of the analysis
    polls.rename(columns={'poll_slug': 'Poll ID',
                          'observations': 'Observations',
                          'Clinton': 'Democratic',
                          'Trump': 'Republican',
                          'start_date': 'Poll start date',
                          'end_date': 'Poll end date'},
                 inplace=True)

    # Small efficiency thing here - has to be here because an error is flagged
    # if we do it earlier - possible data bug?
    polls['Observations'] = polls['Observations'].astype(int)

    polls.to_csv(os.path.join(normal_dir, normal_file_name),
                 index=False)
