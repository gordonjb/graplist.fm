# -*- coding: utf-8 -*-
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output

import plotly.graph_objs as go
import plotly.figure_factory as ff
import _annotated_heatmap

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


def streak_continues(last_row, current_row):
    ly = int(last_row['show_year'])
    lm = int(last_row['show_month'])
    ry = int(current_row['show_year'])
    rm = int(current_row['show_month'])
    return (lm == rm - 1) or (lm == 12 and rm == 1 and ly == ry - 1)


def is_streak_ongoing(streak):
    current_month = datetime.now().month
    current_year = datetime.now().year
    longest_month = int(streak.end['show_month'])
    longest_year = int(streak.end['show_year'])
    if longest_month == current_month and longest_year == current_year:
        return True
    elif longest_month == (current_month - 1) and longest_year == (current_year - 1):
        return True
    elif longest_month == 12 and current_month == 1 and longest_year == (current_year -1):
        return True
    else:
        return False


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.UNITED])

conn = sqlite3.connect('thedatabase.sqlite3', check_same_thread=False)
c = conn.cursor()

worker_count_query = "SELECT Count() FROM %s" % "workers"
c.execute(worker_count_query)
worker_count = c.fetchone()[0]
promotion_count_query = "SELECT Count() FROM %s" % "promotions"
c.execute(promotion_count_query)
promotion_count = c.fetchone()[0]
show_count_query = "SELECT Count() FROM %s" % "shows"
c.execute(show_count_query)
show_count = c.fetchone()[0]

appearances_df = pandas.read_sql_query('SELECT name, count(appearances.worker_id) AS \'appearances\' FROM appearances INNER JOIN workers on workers.worker_id = appearances.worker_id GROUP by appearances.worker_id  ORDER BY appearances DESC', conn)
shows_df = pandas.read_sql_query('SELECT promotions.name, count(shows.promotion) AS \'att_shows\' FROM shows INNER JOIN promotions on promotions.promotion_id = shows.promotion GROUP by shows.promotion', conn)
year_counter_df = pandas.read_sql_query('SELECT strftime(\'%Y\', show_date) AS show_year, count(show_id) AS show_count FROM shows GROUP BY show_year', conn)
split_year_counter_df = pandas.read_sql_query('SELECT strftime(\'%Y\', show_date) AS show_year, promotions.name FROM shows INNER JOIN promotions on promotions.promotion_id = shows.promotion', conn)
year_name_count_df = pandas.read_sql_query('SELECT strftime(\'%Y\', shows.show_date) AS show_year, promotions.name, count(promotions.promotion_id) AS show_count FROM shows INNER JOIN promotions on promotions.promotion_id = shows.promotion GROUP BY show_year, promotions.name', conn)
shows_heatmap_df = pandas.read_sql_query('SELECT strftime(\'%m\', shows.show_date) AS show_month, strftime(\'%Y\', shows.show_date) AS show_year, COUNT(*) AS show_number FROM shows GROUP BY show_year, show_month ORDER BY show_year ASC, show_month ASC', conn)

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

streak_string =""
if current_streak:
    streak_string = "You're on a " + str(latest_streak.count) + " month streak of at least one show per month!"

longest_streak_string = "Your longest streak was " + str(longest_streak.count) + " months of at least one show per month, between " + str(longest_streak)

top_page_size = 10


def shows_per_year_graph():
    return dcc.Graph(
        id='shows-per-year',
        figure=go.Figure(
            data=[go.Bar(x=year_counter_df['show_year'],
                         y=year_counter_df['show_count'])],
            layout=go.Layout(
                title='Shows/year'
            )
        )
    )


def shows_per_year_stacked_graph():
    return dcc.Graph(
        id='shows-per-year-stacked',
        figure=go.Figure(
            data=shows_per_year_series,
            layout=go.Layout(
                title='Shows/year', barmode='stack'
            )
        )
    )


def shows_pie_chart():
    return dcc.Graph(
        id='shows-pie',
        figure=go.Figure(
            data=[go.Pie(labels=shows_df['name'],
                         values=shows_df['att_shows'],
                         textinfo="none")],
            layout=go.Layout(
                margin=dict(t=50)
            )
        ),
        config={
            'displayModeBar': False
        }
    )


def appearances_pie_chart():
    return dcc.Graph(
        id='appearances-pie',
        figure=go.Figure(
            data=[go.Pie(labels=appearances_df['name'],
                         values=appearances_df['appearances'])],
            layout=go.Layout(
                title='Appearances'
            )
        )
    )


def top_wrestlers_table():
    return dash_table.DataTable(
        id='top-wrestlers',
        columns=[
            {"name": i, "id": i} for i in appearances_df.columns
        ],
        page_current=0,
        page_size=top_page_size,
        page_action='custom'
)


def top_promotions_table():
    return dash_table.DataTable(
        id='top-promotions',
        columns=[
            {"name": i, "id": i} for i in sorted(year_name_count_df.columns)
        ],
        page_current=0,
        page_size=top_page_size,
        page_action='custom'
    )


def shows_heatmap():
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    years = []
    last_year = 0
    shows = []
    yr = [None] * 12
    for i, r in shows_heatmap_df.iterrows():
        if int(r['show_year']) == last_year or last_year == 0:
            pass
        else:
            shows.append(yr)
            years.append(last_year)
            new_year = int(r['show_year'])
            last_year += 1
            while last_year < new_year:
                years.append(last_year)
                shows.append([None] * 12)
                last_year += 1
            yr = [None] * 12

        show_m_int = int(r['show_month'])
        yr[(show_m_int - 1)] = r['show_number']
        last_year = int(r['show_year'])
    shows.append(yr)
    years.append(last_year)

    fig = _annotated_heatmap.create_annotated_heatmap(z=shows,
                             y=years,
                             x=months,
                             xgap=5,
                             ygap=5,
                             hoverinfo="none",
                             connectgaps=False,
                             colorscale='Viridis')
    fig.layout.update(go.Layout(
                title='Number of events per year and month',
                yaxis=dict(autorange='reversed',
                           tickmode='linear',
                           showgrid=False),
                xaxis=dict(showgrid=False)
    ))
    return dcc.Graph(
        id='shows-heatmap',
        figure=fig
    )


navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Link", href="#")),
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label="Menu",
            children=[
                dbc.DropdownMenuItem("Entry 1"),
                dbc.DropdownMenuItem("Entry 2"),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem("Entry 3"),
            ],
        ),
    ],
    brand="graplist.fm",
    brand_href="#",
    sticky="top",
)

body = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2(str(worker_count), style={'text-align': 'center'}),
                        html.H2("Wrestlers", style={'text-align': 'center'}),
                    ],
                ),
                dbc.Col(
                    [
                        html.H2("You've seen", style={'text-align': 'center'}),
                        html.H2(str(show_count), style={'text-align': 'center'}),
                        html.H2("shows!", style={'text-align': 'center'}),

                    ],
                ),
                dbc.Col(
                    [
                        html.H2(str(promotion_count), style={'text-align': 'center'}),
                        html.H2("promotions", style={'text-align': 'center'}),
                    ],
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H4(streak_string, style={'text-align': 'center'}),
                        html.H4(longest_streak_string, style={'text-align': 'center'}),
                    ]
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Top Wrestlers seen", style={'text-align': 'center'}),
                        top_wrestlers_table(),
                    ]
                ),
                dbc.Col(
                    [
                        html.H5("Top Promotions seen", style={'text-align': 'center'}),
                        shows_pie_chart(),
                    ]
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        shows_heatmap(),
                    ]
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        top_promotions_table(),
                    ]
                ),
                dbc.Col(
                    [
                        shows_per_year_graph(),
                    ]
                ),
            ]
        )
    ],
    className="mt-4",
    fluid=True,
)

app.layout = html.Div([navbar, body])


@app.callback(
    Output('top-wrestlers', 'data'),
    [Input('top-wrestlers', "page_current"),
     Input('top-wrestlers', "page_size")])
def update_table(page_current,page_size):
    return appearances_df.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')


@app.callback(
    Output('top-promotions', 'data'),
    [Input('top-promotions', "page_current"),
     Input('top-promotions', "page_size")])
def update_table(page_current,page_size):
    return year_name_count_df.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True)