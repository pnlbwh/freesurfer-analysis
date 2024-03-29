#!/usr/bin/env python

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from os.path import isfile, isdir, abspath, join as pjoin
from os import makedirs

import pandas as pd
import numpy as np
import argparse
import logging

from util import delimiter_dict
from verify_ports import get_ports
graphs_port= get_ports('graphs_port')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
log= logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def plot_graph(region, NUM_STD=2):
    '''
    :param region:
    :param NUM_STD: acceptable range of standard deviation
    :return:
    '''

    L = len(subjects)
    val_mean = df[region].values.mean()
    val_std = df[region].values.std()
    # we need val_mean and val_std anyway so not using scipy.stats.zscore function
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


if __name__ == '__main__':

    parser= argparse.ArgumentParser(
        description='Detect outliers in FreeSurfer statistics and display them in graphs')

    parser.add_argument('-i', '--input', required=True, help='a csv/tsv file containing region based statistics')
    parser.add_argument('-d', '--delimiter', default='comma', help='delimiter used between measures in the --input '
                                                                   '{comma,tab,space,semicolon}, default: %(default)s')
    parser.add_argument('-o', '--output', required=True, help='a directory where outlier analysis results are saved')
    parser.add_argument('-e', '--extent', type= float, default=2, help='values beyond mean \u00B1 e*STD are outliers, if e<5; '
                        'values beyond e\'th percentile are outliers, if e>70; default %(default)s')

    args= parser.parse_args()
    outDir= abspath(args.output)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True)

    # df = pd.read_csv('C://Users/tashr/Documents/asegstats_lh.csv')
    # df = pd.read_csv('C://Users/tashr/Documents/aparcstats_lh.csv')
    # outDir = 'C://Users/tashr/Documents/fs-stats-aparc/'

    df = pd.read_csv(abspath(args.input),sep=delimiter_dict[args.delimiter])
    regions = df.columns.values[1:]
    subjects = df[df.columns[0]].values

    # generate all figures
    df_inliers= df.copy()
    for column_name in regions:
        print(column_name)
        _, inliers, zscores= plot_graph(column_name, args.extent)

        # write outlier summary
        df_inliers[column_name] = zscores

    df_inliers.to_csv(pjoin(outDir, 'outliers.csv'), index=False)

    app.layout = html.Div([

        html.Div([
            dcc.Dropdown(
                id='region',
                options=[{'label': i, 'value': i} for i in regions],
                value=regions[0]
            )
        ],
            style={'width': '48%', 'display': 'inline-block'}),

        dcc.Graph(id='stat-graph'),

    ])


    @app.callback(
        Output('stat-graph', 'figure'),
        [Input('region', 'value')])
    def update_graph(region):

        fig, _, _ = plot_graph(region, args.extent)

        return fig


    app.run_server(debug=False, port= graphs_port, host= 'localhost')
