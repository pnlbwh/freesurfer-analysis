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
from os import makedirs, getenv, remove
from subprocess import check_call
from scipy.spatial.distance import mahalanobis
from scipy.stats import scoreatpercentile
from sklearn.ensemble import IsolationForest

import pandas as pd
import numpy as np
import argparse
import logging

from subprocess import check_call

from analyze_stats_graphs import plot_graph, show_table
from view_roi import load_lut, render_roi

from util import delimiter_dict

PERCENT_LOW=3
PERCENT_HIGH=97
CONTAMIN=.05

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True,
                url_base_pathname='/dash/')
# log= logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

input_layout = html.Div(
    id= 'input_layout',
    children= [

        'Text file with rows for subjects and columns for features ',
        html.Br(),
        dcc.Upload(
            id='csv',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
            ]),

            style={
                'width': '30%',
                'height': '40px',       # height of the box
                'lineHeight': '40px',   # height of a carriage return
                'borderWidth': '1px',   # width of the border
                'borderStyle': 'dashed',
                'borderRadius': '5px',  # curvature of the border
                'textAlign': 'center',
                # 'margin': '10px'      # margin from left
            },
        ),

        html.Br(),
        dcc.Input(
            id='outDir',
            placeholder='Output directory ',
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
        html.Br(),
        'Acceptable zscore ',
        html.Br(),
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
        'Delimiter ',
        html.Br(),
        dcc.Input(
            id='delimiter',
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
            value= 'comma'
        ),

        html.Br(),
        html.Br(),
        html.Div([
            html.Button(id='analyze',
                        n_clicks_timestamp=0,
                        children='Analyze',
                        title='Analyze text file to detect outliers')],
            style={'float': 'center', 'display': 'inline-block'}),


        # Other dcc.Input()

        dcc.Store(id='df'),
        dcc.Store(id='subjects'),
        # other dcc.Store()

        html.Div(id='user-inputs'),

        html.Br(),
        dcc.Link('See outliers summary', href='/summary'),
        html.Br(),
        dcc.Link('See outliers in graphs', href='/graphs'),
        html.Br(),
        dcc.Link('See outliers in table', href='/zscores'),
        html.Br(),
        dcc.Link('Perform multivariate analysis', href='/multivar'),

    ],
    style={'display': 'block', 'height': '0', 'overflow': 'hidden'}
)


graph_layout= html.Div(
    id= 'graph_layout',
    children= [

        dcc.Link('Go back to inputs', href='/user'),
        html.Br(),
        dcc.Link('See outliers in table', href='/zscores'),
        html.Br(),
        dcc.Link('See outliers summary', href='/summary'),
        html.Br(),

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

    ],

    style={'display': 'block', 'height': '0', 'overflow': 'hidden'}
)


table_layout= html.Div(
    id= 'table_layout',
    children= [

    dcc.Link('Go back to inputs', href='/user'),
    html.Br(),
    dcc.Link('See outliers in graphs', href='/graphs'),
    html.Br(),
    dcc.Link('See outliers summary', href='/summary'),
    html.Br(),

    html.H2('Standard scores of subjects for each feature'),
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

    ],

    style={'display': 'block', 'height': '0', 'overflow': 'hidden'}
)


summary_layout = html.Div(
    id= 'summary_layout',
    children= [

        dcc.Link('Go back to inputs', href='/user'),
        html.Br(),
        dcc.Link('See outliers in graphs', href='/graphs'),
        html.Br(),
        dcc.Link('See outliers in table', href='/zscores'),
        html.Br(),
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

        dcc.Store(id='already-done')

    ],

    style={'display': 'block', 'height': '0', 'overflow': 'hidden'}
)


multiv_layout = html.Div(
    id= 'multiv_layout',
    children= [

        dcc.Link('Go back to inputs', href='/user'),
        html.Br(),

        html.Div([
            html.Button(id='multiv-button',
                        n_clicks_timestamp=0,
                        children='Perform multivariate analysis',
                        title='Perform multivariate analysis over all features together')],
            style={'float': 'center', 'display': 'inline-block'}),

        DataTable(
            id='multiv-summary',
            filter_action='native',
            sort_action='native',

            style_data_conditional=[{
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(240, 240, 240)'
            }]+ [{
                    'if': {
                        'filter_query': f'{{Outlier}} eq X',
                    },
                    'backgroundColor': 'red',
                    'color': 'black',
                    'fontWeight': 'bold'
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

    ],

    style={'display': 'block', 'height': '0', 'overflow': 'hidden'}
)


app.layout = html.Div([

    html.Div(id='main-content',
             children=[input_layout, graph_layout, table_layout, summary_layout, multiv_layout]),
    dcc.Location(id='url', refresh=False),
    html.Br()
])



@app.callback([Output('region', 'options'), Output('df', 'data'), Output('subjects','data'),
               Output('summary', 'data'), Output('summary', 'columns')],
              [Input('csv','contents'), Input('delimiter','value'),
               Input('outDir', 'value'), Input('extent', 'value'),
               Input('analyze', 'n_clicks'), Input('group-by', 'value')])
def analyze(raw_contents, delimiter, outDir, extent, analyze, group_by):

    if not analyze:
        raise PreventUpdate

    _, contents = raw_contents.split(',')
    decoded = base64.b64decode(contents)
    df_raw = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=delimiter_dict[delimiter])

    subjects = df_raw[df_raw.columns[0]].values
    regions = df_raw.columns.values[1:]
    # do the analysis here
    options = [{'label': i, 'value': i} for i in regions]

    filename= pjoin(outDir, 'outliers.csv')
    if isfile(filename):
        df_inliers= pd.read_csv(filename)
    else:
        df_inliers= df_raw.copy()
        for column_name in regions:
            print(column_name)
            _, inliers, zscores= plot_graph(df_raw, column_name)

            # write outlier summary
            df_inliers[column_name] = zscores


        df_inliers.to_csv(filename, index=False)


    df= df_inliers.copy()
    if group_by == 'subjects':
        dfs = pd.DataFrame(columns=['Subject ID', '# of outliers', 'outliers'])
        columns = [{'name': i,
                    'id': i,
                    'hideable': True,
                    } for i in dfs.columns]

        for i in range(len(df)):
            outliers = df.columns.values[1:][abs(df.loc[i].values[1:]) > extent]
            dfs.loc[i] = [df.loc[i][0], len(outliers), '\n'.join([x for x in outliers])]

    else:
        dfs = pd.DataFrame(columns=['Regions', '# of outliers', 'outliers'])
        columns = [{'name': i,
                    'id': i,
                    'hideable': True,
                    } for i in dfs.columns]

        for i, region in enumerate(df.columns[1:]):
            outliers = df[df.columns[0]].values[abs(df[region]) > extent]
            dfs.loc[i] = [region, len(outliers), '\n'.join([str(x) for x in outliers])]

    summary = pjoin(outDir, f'group-by-{group_by}.csv')
    dfs.to_csv(summary, index=False)


    return (options, df_raw.to_dict('list'), subjects, dfs.to_dict('records'), columns)




# callback for input_layout
# @app.callback([Output('region', 'options'), Output('df', 'data'), Output('subjects','data')],
#               [Input('csv','contents'), Input('delimiter','value'),
#                Input('analyze', 'n_clicks')])
# def update_dropdown(raw_contents, delimiter, analyze):
#
#     if not analyze:
#         raise PreventUpdate
#
#     # df= pd.read_csv(r'C:\Users\tashr\Documents\diag-cte\asegstats.csv')
#
#     _, contents = raw_contents.split(',')
#     decoded = base64.b64decode(contents)
#     df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=delimiter_dict[delimiter])
#
#     subjects = df[df.columns[0]].values
#     regions = df.columns.values[1:]
#     # do the analysis here
#     options = [{'label': i, 'value': i} for i in regions]
#
#     return (options, df.to_dict('list'), subjects)


# callback for multiv_layout
@app.callback([Output('multiv-summary', 'data'), Output('multiv-summary', 'columns')],
              [Input('df','data'), Input('multiv-button','n_clicks'),
               Input('outDir', 'value'), Input('extent','value')])
def show_stats_table(df, activate, outDir, extent):

    if not activate:
        raise PreventUpdate

    outDir= abspath(outDir)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True)

    df= pd.DataFrame(df)
    regions = df.columns.values[1:]
    subjects = df[df.columns[0]].values
    L= len(subjects)

    columns= ['Subjects', 'Mahalonobis/IsoForest', 'Outlier']
    md= pd.DataFrame(columns=columns)

    X= df.values
    meanX= np.mean(X, axis=0)
    ind= np.where(meanX==0)

    X= np.delete(X, ind, axis=1)
    meanX= np.delete(meanX, ind)

    # Mahalanobis distance block =================================
    # Normalizing to avoid md^2 < 0
    X = X / np.max(X, axis=0)
    covX= np.cov(X, rowvar= False)
    icovX= np.linalg.inv(covX)
    MD= np.zeros((L,))
    for i in range(L):
        x= X[i,: ]
        MD[i]= mahalanobis(x, meanX, icovX)


    # IsolationForest block =================================
    rng = np.random.RandomState(123456)
    num_samples = len(subjects)
    iso_f = IsolationForest(max_samples=num_samples,
                            contamination=CONTAMIN,
                            random_state=rng)
    iso_f.fit(df)
    pred_scores = iso_f.decision_function(df)


    # Decision block
    measure= pred_scores
    h_thresh= scoreatpercentile(measure, PERCENT_HIGH)
    l_thresh = scoreatpercentile(measure, PERCENT_LOW)
    inliers= np.logical_and(measure <= h_thresh, measure >= l_thresh)

    for i in range(L):
        md.loc[i] = [subjects[i], round(measure[i], 3), '' if inliers[i] else 'X']
        if ~inliers[i]:
            pass
            # md.loc[i] = [subjects[i], round(measure[i],3), 'X']

    filename= pjoin(outDir, 'multiv_outliers.csv')
    md.to_csv(filename, index=False)

    return [md.to_dict('records'), [{'name': i, 'id': i} for i in columns]]


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

    # ENH show a dialogue box warning about duration

    outDir= abspath(outDir)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True)

    # subject column is lost in the following conversion
    df= pd.DataFrame(df)

    regions = df.columns.values[1:]

    # generate all figures
    filename = pjoin(outDir, 'outliers.csv')
    if isfile(filename):
        df_inliers= pd.read_csv(filename)

    else:
        df_inliers = df.copy()
        for column_name in regions:
            print(column_name)
            _, inliers, zscores= plot_graph(df, column_name)

            # write outlier summary
            df_inliers[column_name] = zscores

        df_inliers.to_csv(filename, index=False)

    layout= show_table(df_inliers)

    return (layout, df_inliers.to_dict('list'))


# callback within table_layout
@app.callback([Output('roi', 'src'), Output('cmd', 'children'), Output('roi-loading', 'children')],
              [Input('table', 'selected_cells'),
               Input('view-type', 'value'),
               Input('template', 'value'),
               Input('subjects', 'data'),
               Input('outDir', 'value')])
def get_active_cell(selected_cells, view_type, template, subjects, outDir):

    if selected_cells:
        temp = selected_cells[0]
        print(temp)

        if not template:
            raise PreventUpdate
        # nilearn or freeview rendering
        fsdir= template.replace('$', str(subjects[temp['row']]))
        if isdir(fsdir):
            fshome = getenv('FREESURFER_HOME', None)
            if not fshome:
                raise EnvironmentError('Please set FREESURFER_HOME and then try again')
            lut = pjoin(fshome, 'FreeSurferColorLUT.txt')
            lut = load_lut(lut)

            region= temp['column_id']
            roi_png= pjoin(outDir,f'{region}.png')
            cmd= render_roi(region, fsdir, lut, outDir, view_type)
            if view_type=='snapshot':
                roi_base64 = base64.b64encode(open(roi_png, 'rb').read()).decode('ascii')
                # remove(roi_png)

                return ['data:image/png;base64,{}'.format(roi_base64),None,True]

            else:
                msg= ['Execute the following command in a terminal to see 3D rendering:', html.Br(), html.Br(), cmd]
                return [None,msg,True]



    raise PreventUpdate



# # callback for summary_layout
# @app.callback([Output('summary', 'data'),
#                Output('summary', 'columns')],
#               [Input('dfscores','data'), Input('outDir', 'value'),
#                Input('extent','value'), Input('group-by', 'value')])
# def update_summary(df, outDir, extent, group_by):
#
#     if not df:
#         raise PreventUpdate
#
#     df= pd.DataFrame(df)
#
#     if group_by=='subjects':
#         dfs = pd.DataFrame(columns=['Subject ID', '# of outliers', 'outliers'])
#         columns = [{'name': i,
#                     'id': i,
#                     'hideable': True,
#                     } for i in dfs.columns]
#
#         for i in range(len(df)):
#             outliers=df.columns.values[1:][abs(df.loc[i].values[1:]) > extent]
#             dfs.loc[i]=[df.loc[i][0], len(outliers), '\n'.join([x for x in outliers])]
#
#     else:
#         dfs = pd.DataFrame(columns=['Regions', '# of outliers', 'outliers'])
#         columns = [{'name': i,
#                     'id': i,
#                     'hideable': True,
#                     } for i in dfs.columns]
#
#         for i,region in enumerate(df.columns[1:]):
#             outliers= df[df.columns[0]].values[abs(df[region]) > extent]
#             dfs.loc[i] = [region, len(outliers), '\n'.join([str(x) for x in outliers])]
#
#     summary= pjoin(outDir, f'group-by-{group_by}.csv')
#     dfs.to_csv(summary, index=False)
#
#     return [dfs.to_dict('records'), columns]



@app.callback([Output(page, 'style') for page in ['input_layout', 'graph_layout', 'table_layout', 'summary_layout', 'multiv_layout']],
              [Input('url', 'pathname')])
def display_page(pathname):
    display_layout = [{'display': 'block', 'height': '0', 'overflow': 'hidden'} for _ in range(5)]

    if pathname == '/graphs':
        display_layout[1] = {'display': 'auto'}
    elif pathname == '/zscores':
        display_layout[2] = {'display': 'auto'}
    elif pathname == '/summary':
        display_layout[3] = {'display': 'auto'}
    elif pathname == '/multivar':
        display_layout[4] = {'display': 'auto'}
    else:
        display_layout[0] = {'display': 'auto'}

    return display_layout


if __name__=='__main__':
    app.run_server(debug=True, port=8051, host='localhost')
