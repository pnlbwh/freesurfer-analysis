#!/usr/bin/env python

import base64, io
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from os.path import isfile, isdir, abspath, join as pjoin
from os import makedirs

import pandas as pd
import numpy as np
import argparse
import logging

from util import delimiter_dict
from verify_ports import get_ports
from analyze_stats_graphs import plot_graph, show_table

graphs_port= get_ports('graphs_port')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# log= logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

EXTENT=2
DELIM='comma'

app.layout = html.Div([

    # 'Summary csv file: ',

    dcc.Upload(
        id='csv',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),

        style={
            'width': '20%',
            # 'height': '40px',
            # 'lineHeight': '40x',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            # 'margin': '10px'
        },
    ),


    # html.Br(),
    dcc.Input(id='outDir',
              placeholder='Output directory',
              style={
                  'width': '20%',
                  # 'height': '40px',
                  # 'lineHeight': '40px',
                  'borderWidth': '1px',
                  # 'borderStyle': 'dashed',
                  'borderRadius': '5px',
                  'textAlign': 'center',
                  # 'margin': '10px'
              },
              ),

    html.Br(),
    html.Br(),

    html.Div([
        html.Button(id='analyze',
                    n_clicks_timestamp=0,
                    children='Analyze summary',
                    title='Analyze summary to detect outliers')],
        style={'float': 'center', 'display': 'inline-block'}),

    html.Br(),
    html.Br(),

    html.Div([
        html.Button(id='show-stats',
                    n_clicks_timestamp=0,
                    children='Show stats table',
                    title='See standard scores')],
        style={'float': 'center', 'display': 'inline-block'}),

    html.Br(),
    html.Br(),


    html.Div([

        html.Div([
            dcc.Dropdown(
                id='region',
                # options=[{'label': i, 'value': i} for i in regions],
                # value=regions[0]
            )
        ],
            style={'width': '48%', 'display': 'inline-block'},
        ),

        dcc.Graph(id='stat-graph'),

    ]),

    dcc.Store(id='df'),
    # dcc.Store(id='region')

    html.Div(id='page-content'),
])

# callback for stats table
@app.callback(Output('page-content', 'children'),
              [Input('df','data'), Input('show-stats','n_clicks')])
def show_stats_table(df, button):
    # print(button)
    if not button:
        raise PreventUpdate

    df= pd.DataFrame(df)
    regions = df.columns.values[1:]

    # generate all figures
    df_inliers= df.copy()
    for column_name in regions:
        print(column_name)
        _, inliers, zscores= plot_graph(df, column_name)

        # write outlier summary
        df_inliers[column_name] = zscores

    # df_inliers.to_csv(pjoin(outDir, 'outliers.csv'), index=False)


    return show_table(df_inliers)



@app.callback([Output('region', 'options'), Output('df', 'data')],
              [Input('csv','contents'), Input('analyze', 'n_clicks')])
def update_dropdown(raw_contents, analyze):
    # print(analyze)
    if not analyze:
        raise PreventUpdate

    # df= pd.read_csv(r'C:\Users\tashr\Documents\diag-cte\asegstats.csv')

    _, contents = raw_contents.split(',')
    decoded = base64.b64decode(contents)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

    regions = df.columns.values[1:]
    # do the analysis here
    options = [{'label': i, 'value': i} for i in regions]

    return (options, df.to_dict())


@app.callback(
    Output('stat-graph', 'figure'),
    [Input('df','data'), Input('region', 'value')])
def update_graph(df, region):

    if not region:
        raise PreventUpdate

    fig, _, _ = plot_graph(pd.DataFrame(df), region)

    return fig


if __name__=='__main__':
    app.run_server(debug=False, port=graphs_port, host='localhost')
