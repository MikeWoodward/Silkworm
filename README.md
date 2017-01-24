#PresidentialPredictor

This software takes state level opinion polls data and forecasts who will win the US presidential election.

The data comes from the Huffington Post Pollster API (http://elections.huffingtonpost.com/pollster/api). The software is based on the work of Sam Wang of the Princeton Election Consortium (http://election.princeton.edu/). I took his MATLAB code and made a series of modifications:
* I only use opinion polls if there are more than 10 polls reported in the state, less than 10 polls and I use the previous election result (I found this experimentally to be more reliable)
* I average over the last 10 polls or more. I take at least 10 polls - including all the polls that took place during the period covered by the 10 polls. For example, if the 10th poll took place on October 26, and there were five polls in total taken on October 26, I include all those polls meaning I average over 14 polls.
* I use a weighted median of the polls.

The results visualization is done with Bokeh using the Bokeh Server. You'll need to start the Bokeh server prior to running the presidential predicter software (from the command line, type 'bokeh serve').

There are two main files:
* PollGetter.py - this retrieves the poll data using the Huffington Post Pollster API.
* PresidentialPredicter.py - the code that does all the work.

To run the software:
* Run PollGetter to get the opnion poll data
* Run the PresidentialPredicter to make a forecast.

This software works well for predicting the 2012 election, but like all similar models, it fails with the 2016 election.