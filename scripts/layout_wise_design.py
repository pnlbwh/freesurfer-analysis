#!/usr/bin/env python

import base64, io
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash_table import DataTable
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from os.path import isfile, isdir, abspath, join as pjoin, dirname
from os import makedirs
from subprocess import check_call

import pandas as pd
import numpy as np
import argparse
import logging

from analyze_stats_graphs import plot_graph, show_table

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
# log= logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

input_layout = html.Div(
    id= 'input_layout',
    children= [
        html.Br(),
        'Summary csv file',
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

        html.Br(),
        dcc.Input(
            id='outDir',
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
        'Extent of standard deviation ',
        dcc.Input(
            id='extent',
            # placeholder='Extent of standard deviation',
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
            value= 2,
            type= 'number'
        ),

        html.Br(),

        html.Div([
            html.Button(id='analyze',
                        n_clicks_timestamp=0,
                        children='Analyze summary',
                        title='Analyze summary to detect outliers')],
            style={'float': 'center', 'display': 'inline-block'}),


        # Other dcc.Input()

        dcc.Store(id='df'),
        dcc.Store(id='subjects'),
        # other dcc.Store()

        html.Div(id='user-inputs'),

        html.Br(),
        dcc.Link('See graphs', href='/graphs'),
        html.Br(),
        dcc.Link('See standard scores', href='/zscores'),
        html.Br(),
        dcc.Link('See summary', href='/summary'),

    ],
    style={'display': 'block', 'line-height': '0', 'height': '0', 'overflow': 'hidden'}
)


graph_layout= html.Div(
    id= 'graph_layout',
    children= [

        html.H2('Standard scores of subjects for each region'),
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

        html.Br(),
        dcc.Link('Go back to inputs', href='/user'),
        html.Br(),
        dcc.Link('See standard scores', href='/zscores'),
        html.Br(),
        dcc.Link('See summary', href='/summary'),

    ],

    style={'display': 'block', 'line-height': '0', 'height': '0', 'overflow': 'hidden'}
)


table_layout= html.Div(
    id= 'table_layout',
    children= [
    html.H2('Standard scores of subjects for each region'),
    html.Br(),
    dcc.Store(id='dfscores'),
    dcc.Input(
        id='template',
        placeholder='freesurfer directory template',
        style={
            'width': '50%',
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
    html.Div([
        html.Button(id='gen-table',
                    n_clicks_timestamp=0,
                    children='Generate table',
                    title='Generate table of standard scores')],
        style={'float': 'center', 'display': 'inline-block'}
    ),

    html.Div(id='table-content'),

    html.Br(),
    dcc.Link('Go back to inputs', href='/user'),
    html.Br(),
    dcc.Link('Go back to graphs', href='/graphs'),
    html.Br(),
    dcc.Link('See summary', href='/summary'),
    ],

    style={'display': 'block', 'line-height': '0', 'height': '0', 'overflow': 'hidden'}
)


summary_layout = html.Div(
    id= 'summary_layout',
    children= [

        'Group outliers by: ',
        html.Div([
            dcc.Dropdown(
                id='group-by',
                options=[{'label': i, 'value': i} for i in ['subjects','regions']],
                value='subjects'
            ),
        ],
        style = {'width': '20%'}),


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

        html.Br(),
        dcc.Link('Go back to inputs', href='/user'),
        html.Br(),
        dcc.Link('Go back to graphs', href='/graphs'),
        html.Br(),
        dcc.Link('Go back to standard scores', href='/zscores'),

    ],

    style={'display': 'block', 'line-height': '0', 'height': '0', 'overflow': 'hidden'}
)


app.layout = html.Div([

    html.Div(id='main-content',
             children=[input_layout, graph_layout, table_layout, summary_layout]),
    dcc.Location(id='url', refresh=False),
    html.Br()
])


# callback for input_layout
@app.callback([Output('region', 'options'), Output('df', 'data'), Output('subjects','data')],
              [Input('csv','contents'), Input('analyze', 'n_clicks')])
def update_dropdown(raw_contents, analyze):
    # print(analyze)
    if not analyze:
        raise PreventUpdate

    # df= pd.read_csv(r'C:\Users\tashr\Documents\diag-cte\asegstats.csv')

    _, contents = raw_contents.split(',')
    decoded = base64.b64decode(contents)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

    subjects = df[df.columns[0]].values
    regions = df.columns.values[1:]
    # do the analysis here
    options = [{'label': i, 'value': i} for i in regions]

    return (options, df.to_dict('list'), subjects)


# callback for graph_layout
@app.callback(
    Output('stat-graph', 'figure'),
    [Input('df','data'), Input('region','value'), Input('extent','value')])
def update_graph(df, region, extent):

    if not region:
        raise PreventUpdate

    fig, _, _ = plot_graph(pd.DataFrame(df), region, extent)

    return fig


# callback for table_layout
@app.callback([Output('table-content', 'children'), Output('dfscores','data')],
              [Input('df','data'),
               Input('gen-table','n_clicks'), Input('outDir', 'value')])
def show_stats_table(df, activate, outDir):
    # print(button)
    if not activate:
        raise PreventUpdate

    outDir= abspath(outDir)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True)

    # subject column is lost in the following conversion
    df= pd.DataFrame(df)

    regions = df.columns.values[1:]

    # generate all figures
    df_inliers= df.copy()

    for column_name in regions:
        print(column_name)
        _, inliers, zscores= plot_graph(df, column_name)

        # write outlier summary
        df_inliers[column_name] = zscores

    df_inliers.to_csv(pjoin(outDir, 'outliers.csv'), index=False)
    layout= show_table(df_inliers)

    return (layout, df_inliers.to_dict('list'))


# callback within table_layout
@app.callback(Output('table-tooltip', 'children'),
              [Input('table', 'selected_cells'),
               Input('view-type', 'value'),
               Input('template', 'value'),
               Input('subjects', 'data')])
def get_active_cell(selected_cells, view_type, template, subjects):

    if selected_cells:
        temp = selected_cells[0]
        print(temp)

        if not template:
            raise PreventUpdate
        # nilearn or freeview rendering
        fsdir= template.replace('$', str(subjects[temp['row']]))
        if isdir(fsdir):
            check_call(' '.join(['python', pjoin(dirname(abspath(__file__)), 'view-roi.py'),
                                 '-i', fsdir, '-l', temp['column_id'], '-v', view_type]), shell=True)

    raise PreventUpdate


# callback for summary_layout
@app.callback([Output('summary', 'data'),
               Output('summary', 'columns')],
              [Input('dfscores','data'), Input('outDir', 'value'),
               Input('extent','value'), Input('group-by', 'value')])
def update_summary(df, outDir, extent, group_by):

    if not df:
        raise PreventUpdate

    df= pd.DataFrame(df)

    if group_by=='subjects':
        dfs = pd.DataFrame(columns=['Subject ID', '# of outliers', 'outliers'])
        columns = [{'name': i,
                    'id': i,
                    'hideable': True,
                    } for i in dfs.columns]

        for i in range(len(df)):
            outliers=df.columns.values[1:][abs(df.loc[i].values[1:]) > extent]
            dfs.loc[i]=[df.loc[i][0], len(outliers), '\n'.join([x for x in outliers])]

    else:
        dfs = pd.DataFrame(columns=['Regions', '# of outliers', 'outliers'])
        columns = [{'name': i,
                    'id': i,
                    'hideable': True,
                    } for i in dfs.columns]
        
        for i,region in enumerate(df.columns[1:]):
            outliers= df[df.columns[0]].values[abs(df[region]) > extent]
            dfs.loc[i] = [region, len(outliers), '\n'.join([str(x) for x in outliers])]

    summary= f'group-by-{group_by}.csv'
    if not isfile(summary):
        dfs.to_csv(pjoin(outDir, summary), index=False)

    return [dfs.to_dict('records'), columns]



@app.callback([Output(page, 'style') for page in ['input_layout', 'graph_layout', 'table_layout', 'summary_layout']],
              [Input('url', 'pathname')])
def display_page(pathname):
    display_layout = [{'display': 'block', 'line-height': '0', 'height': '0', 'overflow': 'hidden'} for _ in range(4)]

    if pathname == '/graphs':
        display_layout[1] = {'display': 'auto'}
    elif pathname == '/zscores':
        display_layout[2] = {'display': 'auto'}
    elif pathname == '/summary':
        display_layout[3] = {'display': 'auto'}
    # elif pathname == '/user':
    else:
        display_layout[0] = {'display': 'auto'}

    return display_layout


if __name__=='__main__':
    app.run_server(debug=True, port=8050, host='localhost')
