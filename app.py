# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

import sqlite3
import pandas
from datetime import datetime


class Streak:
    """docstring for Streak."""

    def __init__(self, start, end, count):
        self.start = start
        self.end = end
        self.count = count

    def __repr__(self):
        return (self.start['show_month'] + "/" + self.start['show_year']
                + " and " + self.end['show_month'] + "/"
                + self.end['show_year'])


def streak_continues(last, row):
    ly = int(last['show_year'])
    lm = int(last['show_month'])
    ry = int(row['show_year'])
    rm = int(row['show_month'])
    return ((lm == rm - 1) or (lm == 12 and rm == 1 and ly == ry - 1))


def is_streak_ongoing(streak):
    currentMonth = datetime.now().month
    currentYear = datetime.now().year
    longestMonth = int(streak.end['show_month'])
    longestYear = int(streak.end['show_year'])
    if longestMonth == currentMonth and longestYear == currentYear:
        return True
    elif longestMonth == (currentMonth - 1) and longestYear == (currentYear - 1):
        return True
    elif longestMonth == 12 and currentMonth == 1 and longestYear == (currentYear -1):
        return True
    else:
        return False


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

conn = sqlite3.connect('thedatabase.sqlite3', check_same_thread=False)
c = conn.cursor()
appearances_df = pandas.read_sql_query('SELECT name, count(appearances.worker_id) AS \'appearances\' FROM appearances INNER JOIN workers on workers.worker_id = appearances.worker_id GROUP by appearances.worker_id', conn)
shows_df = pandas.read_sql_query('SELECT promotions.name, count(shows.promotion) AS \'att_shows\' FROM shows INNER JOIN promotions on promotions.promotion_id = shows.promotion GROUP by shows.promotion', conn)
year_counter_df = pandas.read_sql_query('SELECT strftime(\'%Y\', show_date) AS show_year, count(show_id) AS show_count FROM shows GROUP BY show_year', conn)
split_year_counter_df = pandas.read_sql_query('SELECT strftime(\'%Y\', show_date) AS show_year, promotions.name FROM shows INNER JOIN promotions on promotions.promotion_id = shows.promotion', conn)
year_name_count_df = pandas.read_sql_query('SELECT strftime(\'%Y\', shows.show_date) AS show_year, promotions.name, count(promotions.promotion_id) AS show_count FROM shows INNER JOIN promotions on promotions.promotion_id = shows.promotion GROUP BY show_year, promotions.name', conn)

shows_per_year_series = []
grouped = year_name_count_df.groupby(['name'])
for group_name, df_group in grouped:
    shows_per_year_series.append(
        go.Bar(x=df_group['show_year'],
               y=df_group['show_count'],
               name=group_name))

streaks_df = pandas.read_sql_query('SELECT strftime(\'%Y\', shows.show_date) AS show_year, strftime(\'%m\', shows.show_date) AS show_month FROM shows GROUP BY show_year, show_month ORDER BY show_year ASC, show_month ASC', conn)
last = None
streak_start = None
streak_end = None
streak_count = 1
longest_streak = None
for index, row in streaks_df.iterrows():
    if streak_start is None:
        streak_start = row
    else:
        if streak_continues(last, row):
            streak_count = streak_count + 1
        else:
            streak_end = last
            if longest_streak is None:
                longest_streak = Streak(streak_start, streak_end, streak_count)
            else:
                if streak_count >= longest_streak.count:
                    longest_streak = Streak(streak_start, streak_end, streak_count)
            streak_start = row
            streak_count = 1
    last = row

latest_streak = Streak(streak_start, last, streak_count)
if latest_streak.count >= longest_streak.count:
    longest_streak = latest_streak
current_streak = is_streak_ongoing(latest_streak)

streak_ps = []
if current_streak:
    streak_ps.append(html.P('You\'re on a ', style={'color': 'blue', 'fontSize': 14}))
    streak_ps.append(html.P(str(latest_streak.count), style={'color': 'black', 'fontSize': 16}))
    streak_ps.append(html.P(' month streak of at least one show per month!', style={'color': 'blue', 'fontSize': 14}))

streak_ps.append(html.P('Your longest streak was ', style={'color': 'blue', 'fontSize': 14}))
streak_ps.append(html.P(longest_streak.count, style={'color': 'black', 'fontSize': 14}))
streak_ps.append(html.P(' months of at least one show per month, between ' + str(longest_streak), style={'color': 'blue', 'fontSize': 14}))

app.layout = html.Div(children=[
    html.H1(children='graplist.fm', style={'fontFamily': 'Roboto Condensed'}),

    html.Div(streak_ps),

    dcc.Graph(
        id='appearances-pie',
        figure=go.Figure(
            data=[go.Pie(labels=appearances_df['name'],
                         values=appearances_df['appearances'])],
            layout=go.Layout(
                title='Appearances'
            )
        )
    ),

    dcc.Graph(
        id='shows-pie',
        figure=go.Figure(
            data=[go.Pie(labels=shows_df['name'],
                         values=shows_df['att_shows'])],
            layout=go.Layout(
                title='Shows'
            )
        )
    ),

    dcc.Graph(
        id='shows-per-year',
        figure=go.Figure(
            data=[go.Bar(x=year_counter_df['show_year'],
                         y=year_counter_df['show_count'])],
            layout=go.Layout(
                title='Shows/year'
            )
        )
    ),

    dcc.Graph(
        id='shows-per-year-stacked',
        figure=go.Figure(
            data=shows_per_year_series,
            layout=go.Layout(
                title='Shows/year', barmode='stack'
            )
        )
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
