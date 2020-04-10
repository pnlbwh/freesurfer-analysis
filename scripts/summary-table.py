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
from view_roi import render_roi, load_lut

app = dash.Dash(__name__)

if __name__ == '__main__':

    parser= argparse.ArgumentParser(description='Demonstrate outliers in FreeSurfer statistics')
    parser.add_argument('-i', '--input', required=True, help='a csv file containing region based zscores')
    parser.add_argument('-t', '--template', required=True,
                        help='freesurfer directory pattern i.e. /path/to/$/freesurfer or '
                             '/path/to/derivatives/pnlpipe/sub-$/anat/freesurfer, '
                             'where $ sign is the placeholder for subject id')

    args= parser.parse_args()
    df= pd.read_csv(abspath(args.input))
    subjects= df[df.columns[0]].values
    # df = pd.read_csv('C://Users/tashr/Documents/fs-stats-aparc/outliers.csv')

    fshome= getenv('FREESURFER_HOME', None)
    fshome= 'C://Users/tashr/Documents/'
    if not fshome:
        raise EnvironmentError('Please set FREESURFER_HOME and then try again')
    lut= pjoin(fshome, 'FreeSurferColorLUT.txt')
    lut_colors= load_lut(lut)

    data_condition = [{
        'if': {'row_index': 'odd'},
        'backgroundColor': 'rgb(240, 240, 240)'
    }]

    for d in [{
        'if': {
            'column_id': c,
            'filter_query': f'{{{c}}} gt 2',
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
            style={'width': '10%', }),
        html.Br(),

        DataTable(
            id='table',
            columns=[{'name': i,
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
                'whiteSpace': 'pre-wrap'
            },

            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },

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

            # nilearn or freeview rendering
            fsdir= args.template.replace('$', subjects[temp['row']])
            # fsdir= r'C:\Users\tashr\Documents\freesurfer'
            if isdir(fsdir):
                render_roi(temp['column_id'], fsdir, lut_colors, view_type)


    app.run_server(debug=True, port= 8030, host= 'localhost')

