#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  5 22:12:33 2017

@author: mikewoodward

For details of licensing etc, see the Github page:
    https://github.com/MikeWoodward/PresidentialPredictor
"""

# =============================================================================
# Imports
# =============================================================================
from bokeh.client import push_session
from bokeh.document import Document
from bokeh.layouts import row, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, LabelSet
from bokeh.models.widgets import (CheckboxGroup, DataTable, Div,
                                  Panel, Select,
                                  TableColumn, Tabs)
from bokeh.plotting import figure

import json
import os.path
import pandas as pd


# =============================================================================
# Color functions
# =============================================================================
# The color palettes here are based on the Brewer color palettes for red and
# blue. The equations are based on a quadratic fit to the palettes. See
# http://colorbrewer2.org/

def red(i):
    """Function returns a red in the 'red' palette based on the Brewer
    red palette"""
    r = int(103.0847 + 552.9536*i - 550.8563*i**2 -
            22.44393*i**3 + 173.0536*i**4)
    g = int(1.760684 + 1.109039*i + 457.3675*i**2 -
            28.21238*i**3 - 187.3753*i**4)
    b = int(12.95416 + 99.96996*i - 430.8376*i**2 +
            1327.971*i**3 - 769.7902*i**4)
    return (r, g, b)


def blue(i):
    """Function returns a blue in the 'blue' palette based on the Brewer
    blue palette"""
    r = int(8.198135 - 111.9301*i + 1002.573*i**2 -
            821.4079*i**3 + 168.2797*i**4)
    g = int(48.39549 + 231.4737*i + 214.9868*i**2 -
            437.5405*i**3 + 193.3427*i**4)
    b = int(107.6317 + 474.3465*i - 941.2028*i**2 +
            1038.521*i**3 - 424.8765*i**4)
    return (r, g, b)


def get_palette(color='red', count=9):
    """Gets a complete red or blue color palette"""

    ilist = [x/float((count-1)) for x in range(count)]

    if color == 'red':
        c_f = red
    else:
        c_f = blue

    colors = []

    # Calls either the red or blue function to get the complete red or blue
    # palette
    for i in ilist:
        colors.append("#" + "".join(map(chr, c_f(i))).encode('hex'))

    return colors


# =============================================================================
# Display
# =============================================================================
class Display(object):

    """Class that displays the results - uses Bokeh."""

    def __init__(self, current, previous, polls, states, college,
                 current_allocations):

        self.page_width = 1200  # The width of the display in the browser
        self.page_height = 650  # The height of the display

        self.current = current
        self.previous = previous

        self.polls = polls
        self.states = states
        self.college = college
        self.alloc = current_allocations

        # The latest (most recent) Electraol College distribution
        self.d_dist, self.r_dist, self.ec_date, self.d_max, self.r_max = \
            self.college.get_latest()

        # The Bokeh display is tabbed
        tabs = Tabs(tabs=[self.splash_page(),
                          self.ec_dist_page(),
                          self.ec_time_page(),
                          self.state_table(),
                          self.poll_page(),
                          self.state_polls(),
                          self.margin_weight(),
                          self.choropleth(),
                          self.status_page()])

        document = Document()
        document.title = "Presidential predictor"
        document.add_root(tabs)
        session = push_session(document)
        session.show()

        session.loop_until_closed()

    def splash_page(self):

        """This is the title page displayed as the first tab."""

        with open(os.path.join("HTML templates", "splash.html"), 'r') as h:
            html = h.read()

        html = html.format(self.ec_date.date(),
                           self.d_max,
                           self.r_max,
                           self.current.date(),
                           self.previous.date())

        d = Div(text=html, width=self.page_width, height=self.page_height)

        return Panel(child=widgetbox(d), title="Title")

    def status_page(self):

        """Some summary data - displayed in its own tab."""

        html = "<h1>Status</h1>"
        html += "<p>Number of opinion polls used: {0}</p>"\
                .format(self.polls['Poll ID'].nunique())
        html += "<p>{0}</p>".format(self.states.get_status().replace('\n',
                                                                     '<br>'))

        d = Div(text=html, width=self.page_width, height=self.page_height)

        return Panel(child=widgetbox(d), title="Status")

    def state_table(self):

        """Shows state-by-state data in a table."""

        margin = self.states.get_latest_results()
        margin_alloc = margin.merge(self.alloc)
        margin_alloc['Margin %'] = 100*margin_alloc['Margin']
        margin_alloc['Dem %'] = 100*margin_alloc['Dem share']
        margin_alloc['Rep %'] = 100*margin_alloc['Rep share']

        source = ColumnDataSource(margin_alloc)

        columns = [TableColumn(field="State", title="State", ),
                   TableColumn(field="Method", title="Method"),
                   TableColumn(field="Margin %", title="Margin %"),
                   TableColumn(field="Dem %", title="Dem %"),
                   TableColumn(field="Rep %", title="Rep %"),
                   TableColumn(field="Closeness", title="Closeness"),
                   TableColumn(field="Winner", title="Winner"),
                   TableColumn(field="Allocation", title="Allocation")]

        data_table = DataTable(source=source,
                               columns=columns,
                               width=self.page_width,
                               height=self.page_height)

        return Panel(child=widgetbox(data_table), title="State")

    def ec_time_page(self):

        """Shows the Electoral College results over time as a line chart."""

        p2 = figure(plot_width=self.page_width,
                    plot_height=self.page_height,
                    title="Electoral College over time",
                    x_axis_type="datetime")

        p2.multi_line([self.college.dist['Date'],
                       self.college.dist['Date'],
                       self.college.dist['Date']],
                      [self.college.dist['D_max'],
                       self.college.dist['R_max'],
                       len(self.college.dist['Date'])*[270]],
                      line_width=2,
                      color=["blue", "red", "black"],
                      alpha=[0.5, 0.5, 0.1])

        p2.xaxis.axis_label = 'Date'
        p2.yaxis.axis_label = "Electoral College votes"

        return Panel(child=p2, title="Electoral College over time")

    def ec_dist_page(self):

        dem = pd.DataFrame(range(len(self.d_dist)), columns=['EC'])
        dem['prob'] = self.d_dist
        dem = dem[dem['prob'] > 0]

        rep = pd.DataFrame(range(len(self.r_dist)), columns=['EC'])
        rep['prob'] = self.r_dist
        rep = rep[rep['prob'] > 0]

        p1 = figure(plot_width=self.page_width,
                    plot_height=self.page_height,
                    title="Electoral College distribution")

        p1.vbar(x=dem['EC'],
                width=1,
                bottom=0,
                top=dem['prob'].tolist(),
                color='blue',
                alpha=0.5)

        p1.vbar(x=rep['EC'],
                width=1,
                bottom=0,
                top=rep['prob'].tolist(),
                color='red',
                alpha=0.5)

        p1.xaxis.axis_label = 'Electoral College votes'
        p1.yaxis.axis_label = "Probability"

        return Panel(child=p1, title="Electoral College distribution")

    def poll_page(self):

        """The number of polls over time."""

        p1 = figure(plot_width=self.page_width,
                    plot_height=self.page_height,
                    title="Polls over time",
                    x_axis_type="datetime")

        polls = self.polls.groupby('Poll end date')['Poll ID'].count()

        p1.vbar(x=polls.index.tolist(),
                width=1,
                bottom=0,
                top=polls.values.tolist(),
                color='green',
                alpha=0.5)

        p1.xaxis.axis_label = 'Date'
        p1.yaxis.axis_label = "Poll count"

        return Panel(child=p1, title="Polls over time")

    # Set of helper functions for the state_polls method
    def sp_state_changed(self, attrname, old, new):

        polls = ColumnDataSource(self.polls[self.polls['State'] == new])

        self.sp_poll_data.data = polls.data

        daily = ColumnDataSource(self.daily[self.daily['State'] == new])

        self.sp_states.data = daily.data

    def sp_responses_changed(self, active):

        for index in range(len(self.sp_resp_q)):

            self.sp_resp_q[index].visible = index in active

    def sp_lines_changed(self, active):

        for index in range(len(self.sp_line)):

            self.sp_line[index].visible = index in active

    def state_polls(self):

        """Shows the state polls as a line chart with drop down lists for
        state selection and options to show party etc."""

        # Sizing for display
        f_w = 0.75
        c_w = 0.25

        # Initial selections
        # ------------------
        state_selected = 'FL'
        self.sp_poll_data = ColumnDataSource(self.polls[self.polls['State'] ==
                                             state_selected])

        self.daily = self.states.get_daily_modified()
        self.sp_states = ColumnDataSource(self.daily[self.daily['State'] ==
                                          state_selected])

        # Charts
        # ------
        # Polls figure
        p1 = figure(plot_width=int(self.page_width*f_w),
                    plot_height=self.page_height,
                    title="Polls by state",
                    x_axis_type="datetime")

        self.sp_resp_q = 4*[None]

        # Democratic
        self.sp_resp_q[0] = p1.circle('Poll end date',
                                      'Democratic',
                                      color="blue",
                                      source=self.sp_poll_data)

        # Undecided
        self.sp_resp_q[1] = p1.circle('Poll end date',
                                      'Undecided',
                                      color="black",
                                      source=self.sp_poll_data)

        # Other
        self.sp_resp_q[2] = p1.circle('Poll end date',
                                      'Other',
                                      color="green",
                                      source=self.sp_poll_data)

        # Republican
        self.sp_resp_q[3] = p1.circle('Poll end date',
                                      'Republican',
                                      color="red",
                                      source=self.sp_poll_data)

        self.sp_line = 3*[None]

        self.sp_line[0] = p1.line('Date',
                                  'Democratic',
                                  color='blue',
                                  source=self.sp_states)

        self.sp_line[1] = p1.line('Date',
                                  'Other',
                                  color='green',
                                  source=self.sp_states)

        self.sp_line[2] = p1.line('Date',
                                  'Republican',
                                  color='red',
                                  source=self.sp_states)

        # Controls
        # --------
        # State dropdown list
        options = self.polls['State'].unique().tolist()
        states = Select(name='State',
                        value=state_selected,
                        options=options,
                        title='State')
        states.on_change('value', self.sp_state_changed)

        # Checkbox for parties
        resp_b = [0, 1, 2, 3]
        d_r = Div(text="Responses")
        responses = CheckboxGroup(labels=["Democratic",
                                          "Don't know",
                                          "Other",
                                          "Republican"],
                                  active=resp_b,
                                  name="Responses")

        responses.on_click(self.sp_responses_changed)

        # Checkbox for lines
        line_b = [0, 1, 2]
        d_l = Div(text="Lines")
        lines = CheckboxGroup(labels=["Democratic",
                                      "Other",
                                      "Republican"],
                              active=line_b,
                              name="Lines")

        lines.on_click(self.sp_lines_changed)

        d_le = Div(text="Note the lines have been normalized to exclude "
                        "undecided voters. This means the lines and the poll "
                        "responses won't line up.")

        # Layout
        w = widgetbox(states,
                      d_r,
                      responses,
                      d_l,
                      lines,
                      d_le,
                      width=int(self.page_width*c_w))

        l = row(w, p1)

        return Panel(child=l, title="State polls")

    def choropleth(self):

        """Chloropleth map of the US states, with AK and HI moved to display
        the states as they're typically shown on maps."""

        margin_df = self.states.get_latest_results()

        # Color scale
        # -----------
        # Limit is the maximum value of the margin, this is used to scale
        # the color palette
        limit = int(100*max([margin_df['Margin'].max(),
                            abs(margin_df['Margin'].min())]))

        r = get_palette('red', limit)
        b = get_palette('blue', limit)
        b.reverse()  # We want to go from dark red to dark blue through white
        palette = r + ['#ffffff'] + b  # This is our color palette

        # Load the chloropleth map data
        # -----------------------------
        # The state outlines
        state_j = json.load(open(os.path.join("USStatesJSON",
                                              "state.json"), 'r'))

        # The frame outlines
        frame_j = json.load(open(os.path.join("USStatesJSON",
                                              "frame.json"), 'r'))

        # 'Map' the state data to colors
        # ------------------------------
        # Note we have to be careful here, we have to use the state order
        # from the chloropleth maps
        colors = []
        margins = []
        for state in state_j['data']['name']:
            margin = 100*margin_df[margin_df['State'] == state]['Margin']
            margins.append(margin)
            color = int(margin) + limit
            colors.append(palette[color])

        # Set up the sources
        # ------------------
        # Set up the sources
        state_src = ColumnDataSource(data=dict(x=state_j['data']['x'],
                                               y=state_j['data']['y'],
                                               name=state_j['data']['name'],
                                               margin=margins,
                                               color=colors))

        # No name for the frame
        frame_src = ColumnDataSource(data=dict(x=frame_j['data']['x'],
                                               y=frame_j['data']['y']))

        # Draw the chart
        # --------------
        # Set up the figure - we'll add the hover later
        tools = "pan,wheel_zoom,box_zoom,reset,save"

        p = figure(title="US States: (Democratic - Republican) margin",
                   tools=tools,
                   x_axis_location=None,
                   y_axis_location=None,
                   plot_width=self.page_width,
                   plot_height=self.page_height)

        p.grid.grid_line_color = None

        # The states
        patches = p.patches('x',
                            'y',
                            source=state_src,
                            fill_color='color',
                            fill_alpha=1.0,
                            line_color="gray",
                            line_width=0.5)

        # The frame that separates AK, HI from the rest of the US
        p.multi_line('x',
                     'y',
                     source=frame_src,
                     line_color="gray",
                     line_width=1.0)

        # Now set up the hover tool - only for the states
        hover = HoverTool(point_policy="follow_mouse",
                          renderers=[patches],
                          tooltips=[("Name", "@name"),
                                    ("Margin %", "@margin{1.11}"), ])

        p.add_tools(hover)

        return Panel(child=p, title='Map')

    def margin_weight(self):

        """Shows the maring for each state."""

        margin = self.states.get_latest_results()
        margin_alloc = margin.merge(self.alloc)
        margin_alloc['Margin %'] = 100*margin_alloc['Margin']

        p1 = figure(plot_width=int(self.page_width),
                    plot_height=self.page_height,
                    title="Margin and Electoral College votes")

        p1.xaxis.axis_label = 'Margin %'
        p1.yaxis.axis_label = 'Electoral College votes'

        dem = ColumnDataSource(margin_alloc[margin_alloc['Winner'] == 'Dem'])

        p1.vbar(x='Margin %',
                width=0.5,
                bottom=0,
                top='Allocation',
                color='blue',
                source=dem,
                alpha=0.5)

        labels = LabelSet(x='Margin %',
                          y='Allocation',
                          x_offset=-8,
                          y_offset=5,
                          text='State',
                          text_font_size="8pt",
                          source=dem)

        p1.add_layout(labels)

        rep = ColumnDataSource(margin_alloc[margin_alloc['Winner'] == 'Rep'])

        p1.vbar(x='Margin %',
                width=0.5,
                bottom=0,
                top='Allocation',
                color='red',
                source=rep,
                alpha=0.5)

        labels = LabelSet(x='Margin %',
                          y='Allocation',
                          x_offset=-8,
                          y_offset=5,
                          text='State',
                          text_font_size="8pt",
                          source=rep)

        p1.add_layout(labels)

        rep = ColumnDataSource(margin_alloc[margin_alloc['Winner'] ==
                                            'TOO CLOSE'])

        p1.vbar(x='Margin %',
                width=0.5,
                bottom=0,
                top='Allocation',
                color='green',
                source=rep,
                alpha=0.5)

        labels = LabelSet(x='Margin %',
                          y='Allocation',
                          x_offset=-8,
                          y_offset=5,
                          text='State',
                          text_font_size="8pt",
                          source=rep)

        p1.add_layout(labels)

        l = row(p1)
        return Panel(child=l, title="Margin and EC")
