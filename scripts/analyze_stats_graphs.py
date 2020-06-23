#!/usr/bin/env python

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from dash_table import DataTable
from dash_table.Format import Format
import plotly.graph_objects as go
from os.path import isfile, isdir, abspath, join as pjoin
from os import makedirs

import pandas as pd
import numpy as np
import argparse
import logging

# from verify_ports import get_ports
# graphs_port= get_ports('graphs_port')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

graphs = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app= dash.Dash(__name__, external_stylesheets=external_stylesheets)
# log= logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

# df= pd.read_csv(r'C:\Users\tashr\Documents\diag-cte\asegstats.csv')
# regions = df.columns.values[1:]


def plot_graph(df, region, NUM_STD=2):
    '''
    :param region:
    :param NUM_STD: acceptable range of standard deviation
    :return:
    '''

    subjects = df[df.columns[0]].values
    L = len(subjects)
    val_mean = df[region].values.mean()
    val_std = df[region].values.std()
    # we need val_mean and val_std anyway so no using scipy.stats.zscore function
    zscores = np.array([round((y - val_mean) / val_std, 4) if val_std else 0 for y in df[region].values])
    inliers = abs(zscores) <= NUM_STD

    serial = np.arange(L)

    fig = go.Figure({
        'data': [
            # inliers
            dict(
                x=serial[inliers],
                y=df[region].values[inliers],
                text=[f'Sub: {id}, zscore: {z}' for id,z in zip(subjects[inliers],zscores[inliers])],
                mode='markers',
                name='inliers',
                marker={
                    'size': 15,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'},
                }
            ),
            # outliers
            dict(
                x=serial[~inliers],
                y=df[region].values[~inliers],
                text=[f'Sub: {id}, zscore: {z}' for id,z in zip(subjects[~inliers],zscores[~inliers])],
                mode='markers',
                name='outliers',
                marker={
                    'size': 15,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'},
                    'color': 'red'
                }
            ),
            # mean
            dict(
                x=serial,
                y=L * [val_mean],
                mode='lines',
                line={'color': 'black', 'width': 4},
                name='mean'
            ),
            # mean+ NUM*std
            dict(
                x=serial,
                y=L * [val_mean + NUM_STD* val_std],
                mode='lines',
                line={'dash': 'dash', 'color': 'green', 'width': 4},
                name=f'mean + {NUM_STD} x std'
            ),
            # mean- NUM_STD*std
            dict(
                x=serial,
                y=L * [val_mean - NUM_STD* val_std],
                mode='lines',
                line={'dash': 'dash', 'color': 'green', 'width': 4},
                name=f'mean - {NUM_STD} x std'
            )
        ],
        'layout': dict(
            xaxis={
                'title': 'Index of subjects'
            },
            yaxis={
                'title': region
            },
            margin={'l': 50, 'b': 40, 't': 30, 'r': 0},
            hovermode='closest',
            height=400
        )
    })

    # out_html = pjoin(outDir,f'{region}.html')
    # if not isfile(out_html):
    #     fig.write_html(out_html, include_plotlyjs='directory')

    return (fig, inliers, zscores)

def show_table(df, NUM_STD=2):

    subjects = df[df.columns[0]].values

    data_condition = [{
        'if': {'row_index': 'odd'},
        'backgroundColor': 'rgb(240, 240, 240)'
    }]

    for d in [{
        'if': {
            'column_id': c,
            'filter_query': f'{{{c}}} gt {NUM_STD}',
        },
        'backgroundColor': 'red',
        'color': 'black',
        'fontWeight': 'bold'
    } for c in df.columns[1:]]:
        data_condition.append(d)

    for d in [{
        'if': {
            'column_id': c,
            'filter_query': f'{{{c}}} lt -{NUM_STD}',
        },
        'backgroundColor': 'red',
        'color': 'black',
        'fontWeight': 'bold'
    } for c in df.columns[1:]]:
        data_condition.append(d)

    app.layout = html.Div([

        'Type of visual inspection upon selecting a cell: ',
        html.Div([
            dcc.Dropdown(
                id='view-type',
                options=[{'label': i, 'value': i} for i in ['snapshot', 'freeview']],
                value='snapshot'
            )
        ],
            style={'width': '20%', }),
        html.Br(),

        DataTable(
            id='table',
            columns=[{'name': f'\n{i}',
                      'id': i,
                      'hideable': True,
                      'type': 'numeric',
                      'format': Format(precision=4),
                      } for i in df.columns],
            data=df.to_dict('records'),
            filter_action='native',
            sort_action='native',
            style_data_conditional=data_condition,
            style_cell={
                'textAlign': 'left',
                'whiteSpace': 'pre-wrap',
                'minWidth': '100px'
            },

            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },

            tooltip_duration= None,
            tooltip_data=[{c:
                {
                    'type': 'text',
                    'value': f'{r}, {c}'
                } for c in df.columns
            } for r in subjects]
        ),
        html.Div(id='table-tooltip')
    ])

    return app.layout

# graphs.layout = html.Div([
#
#     html.Div([
#         dcc.Dropdown(
#             id='region',
#             options=[{'label': i, 'value': i} for i in regions],
#             value=regions[0]
#         )
#     ],
#         style={'width': '48%', 'display': 'inline-block'},
#     ),
#
#     dcc.Graph(id='stat-graph'),
#
# ])
#
#
# @app.callback(
#     Output('stat-graph', 'figure'),
#     [Input('region', 'value')])
# def update_graph(region):
#
#     # if not region:
#     #     raise PreventUpdate
#
#     fig, _, _ = plot_graph(region, EXTENT)
#
#     return fig


# if __name__ == '__main__':
#     graphs.run_server(debug=False, port= graphs_port, host= 'localhost')
