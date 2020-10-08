#!/usr/bin/env python

import base64, io
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash_table import DataTable
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from os.path import isfile, isdir, abspath, join as pjoin, dirname, basename
from os import makedirs, getenv, chmod, remove
from subprocess import check_call

import pandas as pd
import numpy as np
import argparse
import logging

from analyze_stats_graphs import plot_graph, show_table
from view_roi import load_lut, render_roi
from _compare_layout import plot_graph_compare, display_model

from util import delimiter_dict

SCRIPTDIR=dirname(abspath(__file__))

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
# log= logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

input_layout = html.Div(
    id= 'input_layout',
    children= [

        'Summary csv file',
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
        'Demographic info csv file',
        html.Br(),
        dcc.Upload(
            id='participants',
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
        'Control group',
        html.Br(),
        dcc.Input(
            id='control',
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
            # value='checking_bin==3'
        ),

        html.Br(),
        'Predictor in regression',
        html.Br(),
        dcc.Input(
            id='effect',
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
            # value='checking_bin==3'
        ),


        html.Br(),
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
        dcc.Store(id='dfcombined'),
        # other dcc.Store()

        html.Div(id='user-inputs'),

        html.Br(),
        dcc.Link('See graphs', href='/graphs'),
        html.Br(),
        dcc.Link('See corrected graphs', href='/compare'),
        html.Br(),
        dcc.Link('See standard scores', href='/zscores'),
        html.Br(),
        dcc.Link('See summary', href='/summary'),

    ],
    style={'display': 'block', 'height': '0', 'overflow': 'hidden'}
)


graph_layout= html.Div(
    id= 'graph_layout',
    children= [

        dcc.Link('Go back to inputs', href='/user'),
        html.Br(),
        dcc.Link('See corrected graphs', href='/compare'),
        html.Br(),
        dcc.Link('See standard scores', href='/zscores'),
        html.Br(),
        dcc.Link('See summary', href='/summary'),
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
    dcc.Link('Go back to graphs', href='/graphs'),
    html.Br(),
    dcc.Link('See summary', href='/summary'),
    html.Br(),

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

    ],

    style={'display': 'block', 'height': '0', 'overflow': 'hidden'}
)


summary_layout = html.Div(
    id= 'summary_layout',
    children= [

        dcc.Link('Go back to inputs', href='/user'),
        html.Br(),
        dcc.Link('Go back to graphs', href='/graphs'),
        html.Br(),
        dcc.Link('Go back to standard scores', href='/zscores'),
        html.Br(),
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

    ],

    style={'display': 'block', 'height': '0', 'overflow': 'hidden'}
)

compare_layout = html.Div(
    id= 'compare_layout',
    children= [

        dcc.Link('Go back to inputs', href='/user'),
        html.Br(),
        dcc.Link('See uncorrected graphs', href='/graphs'),
        html.Br(),
        html.Br(),

        html.Div([
            dcc.Dropdown(
                id='region-compare',
                # options=[{'label': i, 'value': i} for i in regions if isfile(pjoin(outDir, f'.{i}.pkl'))],
                # value=regions[0]
            )
        ],
            style={'width': '48%', 'display': 'inline-block'}),

        # html.Br(),
        # html.Div([
        #     html.Button(id='regress',
        #                 n_clicks_timestamp=0,
        #                 children='Regress',
        #                 title='Run regression analysis')],
        #     style={'float': 'center', 'display': 'inline-block'}
        # ),

        html.Br(),
        'Corrected outliers, superimposed on the uncorrected ones, accounting for standard score of the residuals:',
        dcc.Graph(id='stat-graph-compare'),
        dcc.Graph(id='model-graph'),
        html.Br(),
        dcc.Markdown(id='model-summary'),
        html.Br()
        ],

    style={'display': 'block', 'height': '0', 'overflow': 'hidden'}

)



app.layout = html.Div([

    html.Div(id='main-content',
             children=[input_layout, graph_layout, table_layout, summary_layout, compare_layout]),
    dcc.Location(id='url', refresh=False),
    html.Br()
])


# # callback for input_layout
# @app.callback([Output('region', 'options'), Output('df', 'data'), Output('subjects','data')],
#               [Input('csv','contents'), Input('delimiter','value'), Input('analyze', 'n_clicks')])
# def update_dropdown(raw_contents, delimiter, analyze):
#     # print(analyze)
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
#     options = [{'label': i, 'value': i} for i in regions]
#
#     return (options, df.to_dict('list'), subjects)



# callback for regression analysis
@app.callback([Output('region', 'options'),
               Output('region-compare', 'options'), Output('df', 'data'),
               Output('subjects','data'), Output('dfcombined', 'data')],
              [Input('csv','contents'), Input('csv','filename'),
               Input('participants','contents'), Input('delimiter','value'),
               Input('outDir', 'value'),
               Input('effect','value'), Input('control','value'),
               Input('analyze', 'n_clicks')])
def update_dropdown(input_contents, filename, parti_contents, delimiter, outDir, effect, control, analyze):
    # print(analyze)
    if not analyze:
        raise PreventUpdate

    # df= pd.read_csv(r'C:\Users\tashr\Documents\diag-cte\asegstats.csv')

    # this block is also necessary in table layout since user may want to analyze raw summary only w/o demographics
    outDir= abspath(outDir)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True, mode=0o775)

    _, contents = input_contents.split(',')
    decoded = base64.b64decode(contents)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=delimiter_dict[delimiter])


    if parti_contents:
        summaryCsv= pjoin(outDir, filename)
        df.to_csv(summaryCsv, index= False)

        _, contents = parti_contents.split(',')
        decoded = base64.b64decode(contents)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=delimiter_dict[delimiter])
        partiCsv= pjoin(outDir, '.participants.csv')
        df.to_csv(partiCsv, index= False)

        exe= pjoin(SCRIPTDIR, 'combine_demography.py')
        cmd= f'python {exe} -i {summaryCsv} -o {outDir} -p {partiCsv} -c "{control}"'
        check_call(cmd, shell=True)


        # python scripts\correct_for_demography.py -i asegstats_combined.csv -c asegstats_control.csv -e age
        # -p participants.csv -o dem_corrected/
        prefix= filename.split('.csv')[0]
        outPrefix= pjoin(outDir, prefix)
        exe= pjoin(SCRIPTDIR, 'correct_for_demography.py')
        cmd= f'python {exe} -i {outPrefix}_combined.csv -c {outPrefix}_control.csv -p {partiCsv} -e "{effect}" ' \
             f'-o {outDir}'
        check_call(cmd, shell=True)

        exog = '_'.join(effect.split('+'))
        residuals= f'{outPrefix}_{exog}_residuals.csv'
        df= pd.read_csv(residuals)

        dfcombined= pd.read_csv(f'{outPrefix}_combined.csv')


    subjects = df[df.columns[0]].values
    regions = df.columns.values[1:]
    options = [{'label': i, 'value': i} for i in regions]


    if parti_contents:
        return (options, options, df.to_dict('list'), subjects, dfcombined.to_dict('list'))
    else:
        return (options, options, df.to_dict('list'), subjects, df.to_dict('list'))


# callback for compare_layout
@app.callback(
    [Output('stat-graph-compare', 'figure'),
     Output('model-graph', 'figure'),
     Output('model-summary', 'children')],
    [Input('dfcombined','data'), Input('df','data'),
     Input('region-compare', 'value'), Input('extent', 'value'),
     Input('outDir','value')])
def update_graph(df, df_resid, region, extent, outDir):

    if not region:
        raise PreventUpdate

    df= pd.DataFrame(df)
    df_resid= pd.DataFrame(df_resid)

    fig, _, _ = plot_graph_compare(df, df_resid, region, extent)
    model, summary = display_model(region, outDir)


    return (fig, model, summary)


# callback for graph_layout
@app.callback(
    Output('stat-graph', 'figure'),
    [Input('dfcombined','data'), Input('region','value'), Input('extent','value')])
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

    # this block is also necessary in regression analysis since user may want to see corrected graphs first
    outDir= abspath(outDir)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True, mode=0o775)

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

    filename= pjoin(outDir, 'outliers.csv')
    df_inliers.to_csv(filename, index=False)
    chmod(filename,0o664)

    layout= show_table(df_inliers)

    return (layout, df_inliers.to_dict('list'))


# callback within table_layout
# @app.callback([Output('table-tooltip', 'children'), Output('roi', 'src')],
@app.callback(Output('roi', 'src'),
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
            render_roi(region, fsdir, lut, roi_png, view_type)
            if view_type=='snapshot':
                roi_base64 = base64.b64encode(open(roi_png, 'rb').read()).decode('ascii')
                remove(roi_png)

                return 'data:image/png;base64,{}'.format(roi_base64)

            # check_call(' '.join(['python', pjoin(dirname(abspath(__file__)), 'view-roi.py'),
            #                      '-i', fsdir, '-l', temp['column_id'], '-v', view_type]), shell=True)


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

    summary= pjoin(outDir, f'group-by-{group_by}.csv')
    dfs.to_csv(summary, index=False)

    chmod(summary, 0o664)

    return [dfs.to_dict('records'), columns]





@app.callback([Output(page, 'style') for page in
                  ['input_layout', 'graph_layout', 'table_layout', 'summary_layout', 'compare_layout']],
              [Input('url', 'pathname')])
def display_page(pathname):
    display_layout = [{'display': 'block', 'height': '0', 'overflow': 'hidden'} for _ in range(5)]

    if pathname == '/graphs':
        display_layout[1] = {'display': 'auto'}
    elif pathname == '/zscores':
        display_layout[2] = {'display': 'auto'}
    elif pathname == '/summary':
        display_layout[3] = {'display': 'auto'}
    elif pathname == '/compare':
        display_layout[4]= {'display': 'auto'}
    else:
        display_layout[0] = {'display': 'auto'}

    return display_layout


if __name__=='__main__':
    app.run_server(debug=True, port=8050, host='localhost')
