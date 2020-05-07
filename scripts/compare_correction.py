#!/usr/bin/env python

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
import statsmodels.api as sm
import plotly.graph_objects as go
from os.path import isfile, isdir, abspath, join as pjoin
from os import makedirs

import pandas as pd
from scipy.stats import zscore
import numpy as np
import argparse
import logging

from util import delimiter_dict
from ports import compare_port

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
    # we need val_mean and val_std anyway so no using scipy.stats.zscore function
    zscores = np.array([round((y - val_mean) / val_std, 4) if val_std else 0 for y in df[region].values])
    inliers = abs(zscores) <= NUM_STD

    zscores= np.array([round((y-val_mean)/val_std,4) if val_std else 0 for y in df[region].values])

    serial = np.arange(L)

    # modify inliers according to df_resid
    if df[region].any():
        inliers_corrected= zscore(df_resid[region].values) <= NUM_STD
        inliers= np.logical_and(inliers, inliers_corrected)

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
                'title': 'Subject ID'
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

def display_model(region):

    res = sm.load_pickle(pjoin(outDir, f'.{region}.pkl'))

    fig = make_subplots(
        rows=2, cols=2,
        vertical_spacing=0.3
    )

    X= res.model.exog[:,-1]
    Y= res.model.endog
    Yhat= res.mu

    fig.add_trace(go.Scatter(x=X, y=Y,
                             mode='markers'), row=1, col=1)

    fig.add_trace(go.Scatter(x=Yhat, y=Y,
                             mode='markers'), row=2, col=1)
    fig.update_layout(xaxis= {'title':res.model.exog_names[-1]}, yaxis= {'title': 'volume'})

    fig.add_trace(go.Scatter(x=Yhat, y=res.resid_deviance,
                             mode='markers'), row=2, col=2)
    fig.update_layout(xaxis3={'title': 'Fitted values'}, yaxis3={'title': 'Observed values'})

    fig.add_trace(go.Scatter(x=[Yhat.min(), Yhat.max()], y=[0,0],
                             mode='lines',
                             line={'color': 'black', 'width': 2}), row=2, col=2)
    fig.update_layout(xaxis4={'title': 'Fitted values'}, yaxis4={'title': 'Residuals'})

    fig.update_layout(title='Generalized linear model fitting on control group:')

    return fig

if __name__ == '__main__':

    parser= argparse.ArgumentParser(
        description='Visually compare raw outliers against demographic variable corrected ones')

    parser.add_argument('-i', '--input', required=True, help='a csv/tsv file containing region based statistics')
    parser.add_argument('-c', '--corrected', required=True,
                        help='a *_residual.csv file that was obtained after correcting statistics for demographic variable(s)')
    parser.add_argument('-p', '--participants', required=True,
                        help='a csv file containing demographic info, demographic variable names are learnt from this file, '
                             'properties in the first row cannot have space or dash in them')
    parser.add_argument('-d', '--delimiter', default='comma', help='delimiter used between measures in the --input '
                                                                   '{comma,tab,space,semicolon}, default: %(default)s')
    parser.add_argument('-o', '--output', required=True, help='a directory where outlier analysis results are saved')
    parser.add_argument('-e', '--extent', type= float, default=2, help='values beyond mean \u00B1 e*STD are outliers, if e<5; '
                        'values beyond e\'th percentile are outliers, if e>70; default %(default)s')

    args= parser.parse_args()
    outDir= abspath(args.output)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True)

    df = pd.read_csv(abspath(args.input),sep=delimiter_dict[args.delimiter])
    df_demograph = pd.read_csv(abspath(args.participants))
    demographs = df_demograph.columns[1:]

    regions = [var for var in df.columns.values[1:] if var not in demographs]
    subjects = df[df.columns[0]].values

    df_resid= pd.read_csv(abspath(args.corrected))

    # generate all figures
    df_inliers= df.copy()
    # the below overwrite is for debugging only
    regions=['Left-Lateral-Ventricle', 'Brain-Stem', 'Right-Amygdala']
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
        dcc.Graph(id='model-graph'),
    ])


    @app.callback(
         # return for stat-graph-model
        [Output('stat-graph', 'figure'),
         Output('model-graph', 'figure')],
        [Input('region', 'value')])
    def update_graph(region):

        fig, _, _ = plot_graph(region, args.extent)
        model= display_model(region)
        # also return png figure object
        return (fig,model)


    app.run_server(debug=True, port= compare_port, host= 'localhost')
