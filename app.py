# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

import sqlite3
import pandas

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

conn = sqlite3.connect('thedatabase.sqlite3', check_same_thread=False)
c = conn.cursor()
appearances_df = pandas.read_sql_query('SELECT name, count(appearances.worker_id) AS \'appearances\' FROM appearances INNER JOIN workers on workers.worker_id = appearances.worker_id GROUP by appearances.worker_id', conn)
shows_df = pandas.read_sql_query('SELECT promotions.name, count(shows.promotion) AS \'att_shows\' FROM shows INNER JOIN promotions on promotions.promotion_id = shows.promotion GROUP by shows.promotion', conn)

app.layout = html.Div(children=[
    html.H1(children='graplist.fm', style={'fontFamily': 'Roboto Condensed'}),

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
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
