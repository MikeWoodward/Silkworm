#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 11:26:01 2017

@author: mikewoodward

Gets Presidential polling data from the Huffington Post via the new (v2)
Pollster API

"""

import json
import os.path
import requests

# =============================================================================
# Main
# =============================================================================
if __name__ == '__main__':

    election = {'2008': u'2008-11-04',
                '2012': u'2012-11-06',
                '2016': u'2016-11-08'}

    raw_dir = 'RawPollResponses'

    year = '2016'

    # This is the 'suffix' used for the general election slugs used by the
    # Huffington Post API. The format they use is {two digit year, e.g. 16}-
    # {state}-Pre-GE {CandidateAvCandidateb}
    suffix = '-Pres-GE TrumpvClinton'

    print ""
    print "▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉"
    print "▉ GetPollResponses ▉"
    print "▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉"
    print ""

    print "Getting responses for election held on {0}".format(election[year])

    # Get the question slugs for the election
    # ---------------------------------------
    print "Getting the slugs"

    base_url = 'http://elections.huffingtonpost.com/pollster/api/v2/'\
               'questions.json'
    dict_url = {'cursor': '0', 'election_date': election[year]}

    # Variable holds question slugs. There's a slug for each state
    # Using a set  because it automatically copes with duplicates.
    slug_set = Set()

    # Read all the Huffington Post data until there's no more data
    while True:

        response = requests.get(base_url, params=dict_url)

        raw_json = json.loads(response.text)

        # If no more data, stop reading in
        if len(raw_json['items']) == 0:
            break

        # Update the cursor for the next pass
        dict_url['cursor'] = raw_json['next_cursor']

        # Now, filter on the election (yes, we need to do it again)
        # and the candidates - only leave the slugs with the election date
        # we selected.
        for item in raw_json['items']:

            if item['election_date'] == dict_url['election_date']:
                if suffix in item['slug'] and \
                   'Bloomberg' not in item['slug'] and \
                        '-US-Pres-GE' not in item['slug']:
                    slug_set.add(item['slug'])

    # Quick sanity check - we should have one slug for each state
    if len(slug_set) != 51:
        print "Warning! Should be 51 slugs but found {0}".format(len(slug_set))

    # Save the responses to file
    # --------------------------

    print "Writing the responses"

    base_url = 'http://elections.huffingtonpost.com/pollster/api/v2/questions/'
    tsv_raw = '/poll-responses-raw.tsv'

    for state_slug in slug_set:

        # Replace the space character with something we can use in the URL
        state_corrected = state_slug.replace(' ', '%20')
        url = '{0}{1}{2}'.format(base_url, state_corrected, tsv_raw)

        print url

        # Get the tsv data associated with that slug
        response = requests.get(url)

        file_name = '{0}-{1}-responses.tsv'.format(year, state_slug[3:5])

        state_name = os.path.join(raw_dir, file_name)

        # Save the data to file
        with open(state_name, 'w') as data_file:
            data_file.write(response.text.encode('utf-8'))
