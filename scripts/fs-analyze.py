#!/usr/bin/env python

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

dff = pd.read_csv('C://Users/tashr/Documents/asegstats_lh.csv')

available_indicators = dff.columns.values[1:]

# acceptable range of standard deviation
NUM_STD= 1

app.layout = html.Div([

                html.Div([
                    dcc.Dropdown(
                        id='yaxis-column',
                        options=[{'label': i, 'value': i} for i in available_indicators],
                        value='Left-Lateral-Ventricle'
                    )
                ],
                style={'width': '48%', 'display': 'inline-block'}),

             dcc.Graph(id='indicator-graphic'),

            ])

@app.callback(
    Output('indicator-graphic', 'figure'),
    [Input('yaxis-column', 'value'),
     Input('indicator-graphic', 'hoverData')])
def update_graph(yaxis_column_name, hoverData):

    subjects = dff['Measure:volume'].values
    L= len(subjects)
    val_mean= dff[yaxis_column_name].values.mean()
    val_std= dff[yaxis_column_name].values.std()
    inliers= np.array([True if y<val_mean+val_std and y>val_mean-val_std
              else False for y in dff[yaxis_column_name].values])

    serial = np.arange(L)

    sub_id= subjects[hoverData['points'][0]['x']] if hoverData else subjects[0]

    return {
        'data': [
            # points
            dict(
                x=[i for i in range(L)],
                y=dff[yaxis_column_name].values,
                text= f'Sub: {sub_id}, {yaxis_column_name}',
                mode='markers',
                name='data',
                marker={
                    'size': 15,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'},
                    'color': ['blue' if y<val_mean+val_std and y>val_mean-val_std
                              else 'red' for y in dff[yaxis_column_name].values]
                }
            ),
            # mean
            dict(
                x=serial,
                y=L * [val_mean],
                mode='lines',
                line={'color': 'black', 'width':'4'},
                name='mean'
            ),
            # +1 SD
            dict(
                x=serial,
                y=L * [val_mean+val_std],
                mode='lines',
                line= {'dash': 'dash', 'color': 'green', 'width':'4'},
                name=f'mean + {NUM_STD} x std'
            ),
            # -1 SD
            dict(
                x=serial,
                y=L * [val_mean-val_std],
                mode='lines',
                line={'dash': 'dash', 'color': 'green', 'width':'4'},
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
        )
    }


if __name__ == '__main__':
    app.run_server(debug=True, port= 8040, host= 'localhost')
