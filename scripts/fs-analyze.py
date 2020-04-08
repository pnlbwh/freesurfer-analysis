#!/usr/bin/env python

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from os.path import isfile, join as pjoin

import pandas as pd
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# df = pd.read_csv('C://Users/tashr/Documents/asegstats_lh.csv')
df = pd.read_csv('C://Users/tashr/Documents/aparcstats_lh.csv')
outDir= 'C://Users/tashr/Documents/fs-stats-aparc/'

regions = df.columns.values[1:]
subjects = df[regions[0]].values

# acceptable range of standard deviation
NUM_STD= 2


def plot_graph(yaxis_column_name):
    L = len(subjects)
    val_mean = df[yaxis_column_name].values.mean()
    val_std = df[yaxis_column_name].values.std()
    inliers = np.array([True if y <= val_mean + NUM_STD* val_std and y >= val_mean - NUM_STD* val_std
                        else False for y in df[yaxis_column_name].values])

    zscores= np.array([round((y-val_mean)/val_std,4) if y else 0 for y in df[yaxis_column_name].values])

    serial = np.arange(L)

    fig = go.Figure({
        'data': [
            # inliers
            dict(
                x=serial[inliers],
                y=df[yaxis_column_name].values[inliers],
                text=[f'Subject: {id}' for id in subjects[inliers]],
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
                y=df[yaxis_column_name].values[~inliers],
                text=[f'Subject: {id}' for id in subjects[~inliers]],
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
                'title': yaxis_column_name
            },
            margin={'l': 50, 'b': 40, 't': 30, 'r': 0},
            hovermode='closest',
            height=400
        )
    })

    out_html = pjoin(outDir,f'{yaxis_column_name}.html')
    if not isfile(out_html):
        fig.write_html(out_html, include_plotlyjs='directory')

    return (fig, inliers, zscores)

app.layout = html.Div([

        html.Div([
            dcc.Dropdown(
                id='yaxis-column',
                options=[{'label': i, 'value': i} for i in regions],
                value=regions[0]
            )
        ],
        style={'width': '48%', 'display': 'inline-block'}),

     dcc.Graph(id='indicator-graphic'),

    ])

@app.callback(
    Output('indicator-graphic', 'figure'),
    [Input('yaxis-column', 'value')])
def update_graph(yaxis_column_name):

    fig, _, _= plot_graph(yaxis_column_name)

    return fig


if __name__ == '__main__':

    # save all figures
    df_inliers= df.copy()
    for column_name in regions:
        print(column_name)
        _, inliers, zscores= plot_graph(column_name)

        # write outlier summary
        # df_inliers[column_name]= ['x' if not id else '' for id in inliers]
        df_inliers[column_name] = zscores


    df_inliers.to_csv(pjoin(outDir, 'outliers.csv'), index=False)

    app.run_server(debug=True, port= 8060, host= 'localhost')
