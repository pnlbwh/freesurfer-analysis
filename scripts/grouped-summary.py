#!/usr/bin/env python

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from dash_table import DataTable
import pandas as pd
import argparse
from os.path import isfile, isdir, abspath, dirname, join as pjoin
from os import makedirs, remove
import webbrowser
from glob import glob
from subprocess import Popen

PORT=8050
app = dash.Dash(__name__)

app.layout = html.Div([

        'Group outliers by: ',
        html.Div([
            dcc.Dropdown(
                id='group-by',
                options=[{'label': i, 'value': i} for i in ['subjects','regions']],
                value='subjects'
            )
        ],
        style = {'width': '20%',}),
        html.Br(),

        DataTable(
            id='summary',
            filter_action='native',
            sort_action='native',

            style_data_conditional=[{
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(240, 240, 240)'
            }],

            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },

            style_cell={
                'textAlign': 'left',
                'whiteSpace': 'pre-wrap'
            },

        ),

])


@app.callback([Output('summary', 'data'),
               Output('summary', 'columns')],
              [Input('group-by', 'value')])
def update_summary(group_by):

    if group_by=='subjects':
        dfs = pd.DataFrame(columns=['Subject ID', '# of outliers', 'outliers'])

        columns = [{'name': i,
                    'id': i,
                    'hideable': True,
                    } for i in dfs.columns]

        for i in range(len(df)):
            outliers=df.columns.values[1:][df.loc[i].values[1:] > 2]
            dfs.loc[i]=[df.loc[i][0], len(outliers), '\n'.join([x for x in outliers])]

    else:
        dfs = pd.DataFrame(columns=['Regions', '# of outliers', 'outliers'])
        columns = [{'name': i,
                    'id': i,
                    'hideable': True,
                    } for i in dfs.columns]

        for i,region in enumerate(df.columns[1:]):
            outliers= df[df.columns[0]].values[df[region]>2]
            dfs.loc[i] = [region, len(outliers), '\n'.join([x for x in outliers])]

    summary= f'group-by-{group_by}.csv'
    if not isfile(summary):
        dfs.to_csv(pjoin(outDir, summary), index=False)

    return [dfs.to_dict('records'), columns]

if __name__ == '__main__':


    parser= argparse.ArgumentParser(
        description='Detect outliers in FreeSurfer statistics')

    parser.add_argument('-i', '--input', required=True, help='a csv file containing region based statistics')
    parser.add_argument('-o', '--output', required=True, help='a directory where outlier analysis results are saved')
    parser.add_argument('-e', '--extent', type=int, default=2, help='values beyond mean \u00B1 e*STD are outliers, if e<5; '
                        'values beyond e\'th percentile are outliers, if e>70; default %(default)s')

    # df = pd.read_csv('C://Users/tashr/Documents/fs-stats/outliers.csv')
    # outDir = 'C://Users/tashr/Documents/fs-stats/'

    args= parser.parse_args()
    outDir= abspath(args.output)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True)

    # delete any previous summary
    for file in glob(outDir+ '/*csv'):
        remove(file)
    outliers= pjoin(outDir, 'outliers.csv')

    p= Popen(' '.join(['python', pjoin(dirname(abspath(__file__)), 'fs-analyze.py'),
                       '-i', abspath(args.input), '-o', outDir, '-e', str(args.extent)]), shell=True)

    while not isfile(outliers):
        p.poll()

    df= pd.read_csv(outliers)

    webbrowser.open_new(f'http://localhost:{PORT}')
    app.run_server(debug=False, port= PORT, host= 'localhost')

