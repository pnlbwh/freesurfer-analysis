#!/usr/bin/env python

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from dash_table import DataTable
from dash.exceptions import PreventUpdate
import pandas as pd
import argparse
from os.path import isfile, isdir, abspath, dirname, join as pjoin
from os import makedirs, remove
import webbrowser
from glob import glob
from subprocess import Popen, check_call

PORT=8050
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# app = dash.Dash(__name__)

app.layout = html.Div([

        'Group outliers by: ',
        html.Div([
            dcc.Dropdown(
                id='group-by',
                options=[{'label': i, 'value': i} for i in ['subjects','regions']],
                value='subjects'
            ),
        ],
        style = {'width': '20%'}),

        html.Div([
            html.Button(id='show-stats-graphs',
                        n_clicks_timestamp=0,
                        children='Show stats graphs',
                        title='Show region-based outliers in graphs'),
            html.Button(id='show-stats-table',
                        n_clicks_timestamp=0,
                        children='Show stats table ',
                        title='Show all outliers in table')
            ],
            style = {'float': 'right', 'display':'inline-block'},
            id='main-program'),

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

@app.callback(Output('main-program', 'children'),
              [Input('show-stats-graphs', 'n_clicks_timestamp'),
               Input('show-stats-table', 'n_clicks_timestamp')])
def show_stats_table(graphs, table):
    if int(graphs)>int(table):
        # analyze-stats program have already been executed in the background
        # open localhost:8040
        url= 'http://localhost:8040'
        print(f'\n\nDisplaying graphs at {url}\n\n')
        webbrowser.open(url)
    elif int(table)>int(graphs):
        # execute show-stats-table program
        # open localhost:8030
        Popen(' '.join(['python', pjoin(dirname(abspath(__file__)), 'show-stats-table.py'),
                            '-i', outliers, '-t', args.template]), shell=True)
        url= 'http://localhost:8030'
        print(f'\n\nDisplaying table at {url}\n\n')
        webbrowser.open(url)


    raise PreventUpdate

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
        description='Detect and demonstrate outliers in FreeSurfer statistics')

    parser.add_argument('-i', '--input', required=False, help='a csv file containing region based statistics')
    parser.add_argument('-o', '--output', required=True, help='a directory where outlier analysis results are saved')
    parser.add_argument('-e', '--extent', type=int, default=2, help='values beyond mean \u00B1 e*STD are outliers, if e<5; '
                        'values beyond e\'th percentile are outliers, if e>70; default %(default)s')
    parser.add_argument('-c', '--caselist', required=False,
                        help='subject ids from the caselist are used in template to obtain valid freesurfer directory')
    parser.add_argument('-t', '--template', required=False,
                        help='freesurfer directory pattern i.e. /path/to/$/freesurfer or '
                             '/path/to/derivatives/pnlpipe/sub-$/anat/freesurfer, '
                             'where $ sign is the placeholder for subject id')

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

    # TODO
    # accept either summary table as args.input
    # or args.caselist with args.template and then generate args.input

    p= Popen(' '.join(['python', pjoin(dirname(abspath(__file__)), 'analyze-stats.py'),
                       '-i', abspath(args.input), '-o', outDir, '-e', str(args.extent)]), shell=True)

    while not isfile(outliers):
        p.poll()

    df= pd.read_csv(outliers)

    # webbrowser.open_new(f'http://localhost:{PORT}')
    app.run_server(debug=False, port= PORT, host= 'localhost')

