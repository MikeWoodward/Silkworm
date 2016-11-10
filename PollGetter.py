# -*- coding: utf-8 -*-
"""
Created on Sun Nov  8 18:06:01 2015

@author: mwoodward
"""

# =============================================================================
# Imports
# =============================================================================
import csv
import datetime
import io
import json
import os.path
import pandas as pd
import requests


# =============================================================================
# HuffintonPolls
# =============================================================================
class HuffingtonPolls(object):

    def __init__(self, year):

        self.error_flag = False
        self.error_strings = []

        self.base_url = "http://elections.huffingtonpost.com" \
                        "/pollster/api/polls.json"
        self.dict_url = {'page': 1, 'topic': '{0}-president'.format(year)}

        self.list_polls = []
        self.page = None

        self.poll_count = 0  # Count of polls
        self.dem_count = 0  # Count of Democratic responses
        self.rep_count = 0  # Count of Republican responses

        # Used for debugging
        self.poll_log = []

        self.write_page = True

        # Get the poll responses and how they map to parties etc.
        with open(os.path.join('Input',
                               'PollResponseCodes{0}.json'.
                               format(year))) as df:
            self.responses = json.load(df)

    def get_page(self, page_number):

        """Returns True if the page has content that can be parsed, False
        if there's no content."""

        self.dict_url['page'] = page_number

        response = requests.get(self.base_url, params=self.dict_url)

        # Check for a null response - no more data so return
        if len(response.text) == 2:
            return False

        self.page = response.text

        if self.write_page:

            f_name = os.path.join('Raw data',
                                  '{0}-{1}.txt'.format(self.dict_url['topic'],
                                                       self.dict_url['page']))

            with io.open(f_name, 'w', encoding='utf8') as f:
                f.write(response.text)

        return True

    def parse_responses(self, response_list):

        """Parse poll responses"""

        democratic = 0
        republican = 0
        other = 0
        undecided = 0
        for response in response_list:

            choice = response['choice'].rstrip()

            if choice in self.responses['Republican'] or \
               response['party'] == 'Rep':

                republican = response['value']
                self.rep_count += 1

            elif response['party'] == 'Dem' or \
                    choice in self.responses['Democratic']:

                democratic = response['value']
                self.dem_count += 1

            elif choice in self.responses['Other candidates']:

                other += response['value']

            elif choice in self.responses['Other responses']:

                other += response['value']

            elif choice in self.responses['Undecided']:

                undecided += response['value']

            else:
                self.error_flag = True
                self.error_strings.append("Error! Untrapped response. "
                                          "Response is: {0}".format(response))

        return democratic, republican, other, undecided

    def parse_page(self):

        """Parse all the polls on the page"""

        poll_list = json.loads(self.page)

        for poll in poll_list:

            sponsors = ''
            for sp in range(len(poll['sponsors']) - 1):
                sponsors += poll['sponsors'][sp]['name']
                sponsors += " | "
            else:
                sponsors = sponsors[:-3]

            for q_index, question in enumerate(poll['questions']):

                # If the topic is wrong, ot it's a national poll, carry on
                # with the loop

                if question['topic'] != self.dict_url['topic'] or \
                   question['state'] == u'US':
                    continue

                for s_index, sub in enumerate(question['subpopulations']):

                    self.poll_count += 1

                    poll_id = '{0}-{1}-{2}'.format(poll['id'],
                                                   q_index,
                                                   s_index)
                    obs = sub['observations']
                    pop_type = sub['name']

                    democratic, republican, other, undecided = \
                        self.parse_responses(sub['responses'])

                    # Update the poll log - used for debugging
                    self.poll_log.append(poll_id)

                    # Trap an error condition that can happen - missing
                    # Democratic or Republican responses
                    if self.rep_count != self.dem_count or \
                       self.rep_count != self.poll_count or \
                       self.dem_count != self.poll_count:

                        self.error_flag = True

                        self.error_strings.append(
                            "Error! - disagreement in poll counts\n"
                            "Poll is {0}\n"
                            "Responses are:\n"
                            "{1}\n".format(poll['id'], sub['responses']))

                    poll_dict = {'Poll ID': poll_id,
                                 'Poll start date': poll['start_date'],
                                 'Poll end date': poll['end_date'],
                                 'Source': poll['source'],
                                 'Pollster': poll['pollster'],
                                 'Partisan': poll['partisan'],
                                 'Method': poll['method'],
                                 'State': question['state'],
                                 'Observations': obs,
                                 'Population type': pop_type,
                                 'Sponsors': sponsors,
                                 'Democratic': democratic,
                                 'Republican': republican,
                                 'Other': other,
                                 'Undecided': undecided}

                    self.list_polls.append(poll_dict)

# =============================================================================
# main
# =============================================================================
if __name__ == '__main__':

    ELECTION_2008_DATE = pd.to_datetime('2008-11-04')
    ELECTION_2012_DATE = pd.to_datetime('2012-11-06')
    ELECTION_2016_DATE = pd.to_datetime('2016-11-08')

    election = ELECTION_2016_DATE

    year = election.year

    print ""
    print "▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉"
    print "▉ Poll Getter ▉"
    print "▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉"
    print ""
    print "Election year {0}\n".format(year)

    poll_reader = HuffingtonPolls(year)

    print "Reading pages from Huffington Post:"

    page_counter = 1
    while poll_reader.get_page(page_counter):

        print "{0:3d}, ".format(page_counter),

        if (page_counter % 10) == 0:
            print

        poll_reader.parse_page()

        page_counter += 1
    else:
        print

    # Write poll data to file
    print "\nWriting polls to file\n"

    df = pd.DataFrame(poll_reader.list_polls)

    df['Election date'] = election.date()

    df.sort_values(by=['State', 'Poll start date'], inplace=True)

    df.to_csv(os.path.join('Input', 'OpinionPolls{0}.csv'.format(year)),
              columns=['Election date',
                       'Poll ID', 'State', 'Pollster',
                       'Sponsors',
                       'Poll start date', 'Poll end date',
                       'Source',
                       'Partisan', 'Method', 'Population type',
                       'Observations', 'Democratic', 'Republican',
                       'Other', 'Undecided'],
              index=False)

    # Write errors and logs to file
    print "Error status"
    print "------------"
    today = datetime.date.today().isoformat()

    if poll_reader.error_flag:
        print "Errors found! The data is unreliable."
        print "See the errors file for a list of errors.\n"
        with open(os.path.join('Diagnostics', 'Errors-{0}.txt'.format(today)),
                  'w') as f:
            f.write("\n".join("%s" % (s) for s in poll_reader.error_strings))
    else:
        print "No errrors flagged.\n"

    poll_reader.poll_log.sort()

    with open(os.path.join('Diagnostics', '{0}.txt'.format(today)), 'w') as f:
        csv = csv.writer(f)
        csv.writerow(poll_reader.poll_log)

    # Summarize results
    print "Results"
    print "======="
    print "Number of polls: {0}".format(poll_reader.poll_count)
    print "Count of Democratic responses: {0}".format(poll_reader.dem_count)
    print "Count of Republican responses: {0}".format(poll_reader.rep_count)
    print "Most recent date in polls is {0}".format(df['Poll end date'].max())
