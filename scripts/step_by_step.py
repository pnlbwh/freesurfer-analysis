#!/usr/bin/env python

'''
# Some pros and cons discovered

* a property from app.layout is available to all sub layouts but not the other way around
* for making any property from a sub layout available to other sub layouts, it has to be relayed through app.layout
* a property in Output() should belong to the layouts from which Input() come, otherwise app won't recognize
* pages of a multi-page-app can be viewed by clicking dcc.Link( ), the pages are basically in the same page updating
    with different layouts being returned to the page
* debug=True must be on for debugging, many of the above discoveries were made from the debug message on the web page
* since clicking on dcc.Link() on the current layout X returns a new layout Y, values in old layout Y will generally be
    lost, however, if a value from layout X is carried over through app.layout, then that value will be
    available in layout Y

    because of this disadvantage, https://community.plotly.com/t/how-to-pass-values-between-pages-in-dash/33739/7 should
    be the best way to render a multi-page-app

# Output() rules
* try not to mix properties of different layouts
* if an Output() property is pertinent to app.layout, all Input()s are probably required
    to come from app.layout()/current layout
* but if none of the Output()s are from app.layout, Input()s can be mixed from app.layout+current layout

# life saver
* keep debug=True and it will tell you what to adjust
'''

import base64, io
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from os.path import isfile, isdir, abspath, join as pjoin, dirname
from os import makedirs
from subprocess import check_call

import pandas as pd
import numpy as np
import argparse
import logging

from util import delimiter_dict
from verify_ports import get_ports
from analyze_stats_graphs import plot_graph, show_table

graphs_port= get_ports('graphs_port')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
# log= logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

EXTENT=2
DELIM='comma'

app.layout = html.Div([

    html.Div(id='main-content'),
    html.Div(id='test-content'),
    html.Div(id='hidden-content', style={'display': 'none'}),
    dcc.Location(id='url', refresh=False),
    html.Br(),
    dcc.Link('Start the application', href='/app'),
    dcc.Store(id='subjects'),

])

input_layout = html.Div([

    html.H2('Input page'),
    html.Br(),
    # 'Summary csv file: ',

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

    html.Div([
        html.Button(id='analyze',
                    n_clicks_timestamp=0,
                    children='Analyze summary',
                    title='Analyze summary to detect outliers')],
        style={'float': 'center', 'display': 'inline-block'}),

    html.Br(),
    html.Br(),

    html.Div([
        html.Button(id='show-stats',
                    n_clicks_timestamp=0,
                    children='Show stats table',
                    title='See standard scores')],
        style={'float': 'center', 'display': 'inline-block'}),

    html.Br(),
    html.Br(),


    html.Div([

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

    ]),

    dcc.Store(id='df'),
    # dcc.Store(id='subjects'),

    html.Div(id='page-content'),

    html.Br(),
    dcc.Link('Go to table of standard scores', href='/table'),
    html.Br(),
    dcc.Link('Go back to main page', href='/'),

])


table_layout= html.Div([
    html.H2('Table page'),
    html.Br(),

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
        html.Button(id='see-table',
                    n_clicks_timestamp=0,
                    children='See table',
                    title='Button for table-page triggered callback')],
        style={'float': 'center', 'display': 'inline-block'}),
    html.Div(id='table-content'),
    html.Br(),
    dcc.Link('Go back to app page', href='/app'),

])


# callback for table_layout, through input_layout

# having table-content does not trigger the show-stats button let alone give any update/error, wired!
# maybe because input_layout + app.layout, from where the inputs come, don't have knowledge about 'table-content' property
# @app.callback(Output('table-content', 'children'),
# @app.callback([Output('test-content', 'children'),
#                Output('hidden-content', 'children')],
@app.callback(Output('hidden-content', 'children'),
              [Input('df','data'),
               Input('show-stats','n_clicks')])
               # Input('see-table', 'n_clicks')]) # input_layout does not know about see-table property from table_layout
def show_stats_table(df, button):
    # print(button)
    if not button:
        raise PreventUpdate

    df= pd.DataFrame(df)
    regions = df.columns.values[1:]

    # generate all figures
    df_inliers= df.copy()
    for column_name in regions:
        print(column_name)
        _, inliers, zscores= plot_graph(df, column_name)

        # write outlier summary
        df_inliers[column_name] = zscores

    # df_inliers.to_csv(pjoin(outDir, 'outliers.csv'), index=False)
    temp= show_table(df_inliers)

    # return (temp,temp)
    return temp

dummy_layout_for_testing_output_scope= html.Div(id='dummy-out-content')


# callback for table-layout
# @app.callback([Output('dummy-out-content', 'children'), # dummy_layout_for_testing_output_scope
@app.callback(Output('table-content', 'children'), # table_layout
              [Input('see-table', 'n_clicks'), # table_layout
               Input('hidden-content', 'children')]) # input_layout
def show_stats_table(button, content):
    # print(button)
    if not button:
        raise PreventUpdate

    # print(content)

    # NOTE this statement is ineffectual
    # in its absence, it was expected that content would remain hidden in table_layout, but it is not
    # content['style']= {}


    return content


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

    return (options, df.to_dict(), subjects)


@app.callback(
    Output('stat-graph', 'figure'),
    [Input('df','data'), Input('region', 'value')])
def update_graph(df, region):

    if not region:
        raise PreventUpdate

    fig, _, _ = plot_graph(pd.DataFrame(df), region)

    return fig


@app.callback(Output('table-tooltip', 'children'), # input_layout
              [Input('table', 'selected_cells'), # input_layout
               Input('view-type', 'value'), # input_layout
               Input('template', 'value'), # table_layout
               Input('subjects', 'data')]) # app.layout
def get_active_cell(selected_cells, view_type, template, subjects):
    if selected_cells:
        # subjects should be saved in a State variable in
        # subjects = df[df.columns[0]].values
        temp = selected_cells[0]
        print(temp)

        if not template:
            raise PreventUpdate
        # nilearn or freeview rendering
        fsdir= template.replace('$', str(subjects[temp['row']]))
        # print(fsdir)
        if isdir(fsdir):
            check_call(' '.join(['python', pjoin(dirname(abspath(__file__)), 'view-roi.py'),
                                 '-i', fsdir, '-l', temp['column_id'], '-v', view_type]), shell=True)

    raise PreventUpdate



@app.callback(Output('main-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/table':
        return table_layout
    elif pathname == '/app':
        return input_layout
    # else:
    #     return app.layout


if __name__=='__main__':
    app.run_server(debug=True, port=graphs_port, host='localhost')
