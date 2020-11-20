#!/usr/bin/env python

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from dash_table import DataTable
from dash_table.Format import Format
import pandas as pd
import argparse
from os.path import isfile, isdir, abspath, dirname, join as pjoin
from os import makedirs, getenv
import webbrowser
from subprocess import check_call
import logging

from verify_ports import get_ports
table_port= get_ports('table_port')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
log= logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

if __name__ == '__main__':

    parser= argparse.ArgumentParser(description='Demonstrate outliers of FreeSurfer statistics in an interactive table')
    parser.add_argument('-i', '--input', required=True, help='a csv file containing region based zscores')
    parser.add_argument('-t', '--template',
                        help='freesurfer directory pattern i.e. /path/to/$/freesurfer or '
                             '/path/to/derivatives/pnlpipe/sub-$/anat/freesurfer, '
                             'where $ sign is the placeholder for subject id '
                             'ROI rendering is disabled if not provided')
    parser.add_argument('-e', '--extent', type= float, default=2, help='values beyond mean \u00B1 e*STD are outliers, if e<5; '
                        'values beyond e\'th percentile are outliers, if e>70; default %(default)s')

    args= parser.parse_args()
    df= pd.read_csv(abspath(args.input))
    subjects= df[df.columns[0]].values
    # df = pd.read_csv('C://Users/tashr/Documents/fs-stats-aparc/outliers.csv')

    data_condition = [{
        'if': {'row_index': 'odd'},
        'backgroundColor': 'rgb(240, 240, 240)'
    }]

    for d in [{
        'if': {
            'column_id': c,
            'filter_query': f'{{{c}}} gt {args.extent}',
        },
        'backgroundColor': 'red',
        'color': 'black',
        'fontWeight': 'bold'
    } for c in df.columns[1:]]:
        data_condition.append(d)

    for d in [{
        'if': {
            'column_id': c,
            'filter_query': f'{{{c}}} lt -{args.extent}',
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


    @app.callback(Output('table-tooltip', 'children'),
                  [Input('table', 'selected_cells'),
                   Input('view-type', 'value')])
    def get_active_cell(selected_cells, view_type):
        if selected_cells:
            temp = selected_cells[0]
            print(temp)

            if not args.template:
                return
            # nilearn or freeview rendering
            fsdir = args.template.replace('sub-*/', 'sub-{}/'.format(subjects[temp['row']]))
            if isdir(fsdir):
                check_call(' '.join(['python', pjoin(dirname(abspath(__file__)), 'view_roi.py'), '-o', dirname(args.input),
                                     '-i', fsdir, '-l', temp['column_id'], '-v', view_type]), shell=True)

    app.run_server(debug=False, port= table_port, host= 'localhost')

