#!/usr/bin/env python
# -*- coding: ascii -*-

"""
Electoral college predictions a la 538.
Based loosely on Nate Silver's methodology, described here:
http://fivethirtyeight.blogs.nytimes.com/methodology/

All data in 'data.txt' is scraped from:
http://realclearpolitics.com/epolls/latest_polls/president/

All data in 'election.txt' is from:
http://elections.nytimes.com/2012/electoral-map
"""

__author__ = 'Vedant Misra (vedantmisra.com)'
__copyright__ = 'Copyright (c) 2012 Vedant Misra'
__license__ = 'MIT'
__vcs_id__ = '$Id$'
__version__ = '0.1'

import datetime
import numpy

days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "Saturday", "Sunday"]
two_word_states = ["New", "North", "Rhode", "South", "West"]

TODAY = datetime.datetime(year=2012, month=11, day=4)
UNRELIABLE_POLLSTERS = ["Strategic Vision", "Research 2000", "Zogby"]
PARTISAN_POLLSTERS = []
LEFT_LEANING_POLLSTERS = {"Rasmussen": 2}
RIGHT_LEANING_POLLSTERS = {}

class Poll:
    """
    Poll class.
    Represents an individual poll's results.
    """
    def __init__(self, date, state, pollster, obama, romney):
        self.state = state
        self.date = date
        self.pollster = pollster
        self.obama = obama
        self.romney = romney
        self.obama_wins = True
        self.weight = 0
        self.sample_size = 1
        self.rating = 1
        if romney > obama:
            self.obama_wins = False
    def __cmp__(self, other):
        return cmp(self.date, other.date)

class State:
    """
    State class.
    Represents an individual state.
    """
    def __init__(self, name, votes, root):
        self.name = name
        self.votes = votes
        self.root = root
        if self.root == "Obama":
            self.obama_wins = True
        elif self.root == "Romney":
            self.obama_wins = False
        elif self.root == "Tossup":
            self.obama_wins = False
    def winner(self):
        if self.obama_wins:
            return "Obama"
        else:
            return "Romney"
    def __repr__(self):
        return self.name + " (" + str(self.votes) + "): " + self.winner()

def parse_electoral(filename):
    """ 
    Read electoral college votes, state names, and alignment from file.
    """
    states = {}
    f = open(filename, 'r')
    for row in f:
        row = row.strip().split()
        states[row[0]] = State(row[0], int(row[1]), row[2])
    return states

def parse_rcp_text(filename):
    polls = {}
    f = open(filename, 'r')
    for row in f:
        row = row.strip()
        row = row.split()
        if (len(row) != 0) and (row[0].split(",")[0] in days_of_week):
            curr_date = datetime.datetime.strptime(" ".join(row), "%A, %B %d")
            curr_date = curr_date.replace(year = 2012)
        elif (len(row) != 0) and ("Race" not in row[0]):
            ints = []
            for i in range(len(row)):
                try:
                    ints.append((int(row[i].strip(",")), i))
                except ValueError:
                    pass
            if row[ints[0][1] - 1] == "Obama":
                obama_val = ints[0][0]
                romney_val = ints[1][0]
            elif row[ints[0][1] - 1] == "Romney":
                romney_val = ints[0][0]
                obama_val = ints[1][0]
            two_word_state = False
            if row[0] in two_word_states:
                state = row[0] + row[1]
                two_word_state = True
            else:
                state = row[0]
            poll = " ".join(row[two_word_state + 1:ints[0][1] - 1])
            polls.setdefault(state, []).append(
                Poll(curr_date, state, poll, obama_val, romney_val))
    return polls

def compute(states):
    state_list = states.keys()
    state_list.sort()
    obama_count = 0
    romney_count = 0
    for state_name in state_list:
        state = states[state_name]
        print state_name, state.obama_score, state.romney_score
        if state.obama_score > state.romney_score:
            obama_count += state.votes
        else:
            romney_count += state.votes
    print "Votes for Mr. Obama", obama_count
    print "Votes for Mr. Romney", romney_count

def predict(states, polls):
    tossups = []
    state_list = states.keys()
    state_list.sort()
    obama = 0
    romney = 0
    for state_name in state_list:
        try:
            polls[state_name].sort()
            polls[state_name].reverse()
            for poll in polls[state_name]:
                # Exponentially decaying weight
                poll.weight = numpy.exp(-(TODAY - poll.date).days)
                # Adjust weight for sample size (unimplemented)
                poll.weight *= poll.sample_size
                # Adjust weight for historical pollster rating
                poll.weight *= poll.rating
                # Drop unreliable pollsters
                if poll.pollster in UNRELIABLE_POLLSTERS:
                    poll.weight = 0
                # Drop partisan pollsters
                if poll.pollster in PARTISAN_POLLSTERS:
                    poll.weight = 0
                # House effects adjustment
                if poll.pollster in LEFT_LEANING_POLLSTERS:
                    poll.obama -= LEFT_LEANING_POLLSTERS[poll.pollster]
                    poll.romney += LEFT_LEANING_POLLSTERS[poll.pollster]
                if poll.pollster in RIGHT_LEANING_POLLSTERS:
                    poll.romney -= RIGHT_LEANING_POLLSTERS[poll.pollster]
                    poll.obama += RIGHT_LEANING_POLLSTERS[poll.pollster]
                # Trendline adjustment
                # TODO
                # Likely voter adjustment
                # TODO
                # Regression
                # Todo
            obama_poll_sum = sum([p.weight * p.obama for p in polls[state_name]])/(
                100 * len(polls[state_name]))
            romney_poll_sum = sum([p.weight * p.romney for p in polls[state_name]])/(
                100 * len(polls[state_name]))
        except KeyError:
            if states[state_name].root == 'Obama':
                obama_poll_sum = 1
                romney_poll_sum = 0
            elif states[state_name].root == 'Romney':
                obama_poll_sum = 0
                romney_poll_sum = 1
        obama_score = obama_poll_sum / float(obama_poll_sum + romney_poll_sum)
        romney_score = romney_poll_sum / float(obama_poll_sum + romney_poll_sum)
        states[state_name].obama_score = obama_score
        states[state_name].romney_score = romney_score
    return compute(states)

if __name__ == "__main__":
    states = parse_electoral("electoral.txt")
    polls = parse_rcp_text("data.txt")
    predict(states, polls)
