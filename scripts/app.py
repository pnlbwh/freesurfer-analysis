#!/usr/bin/env python

import base64, io
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash_table import DataTable
from dash.exceptions import PreventUpdate
from os.path import isfile, isdir, abspath, join as pjoin, dirname
from os import makedirs, getenv, remove
from scipy.spatial.distance import mahalanobis
from scipy.stats import scoreatpercentile
from sklearn.ensemble import IsolationForest

import pandas as pd
import numpy as np
import argparse
import logging

from subprocess import check_call

from _table_layout import plot_graph, show_table
from view_roi import load_lut, render_roi
from _compare_layout import plot_graph_compare, display_model

from util import delimiter_dict

SCRIPTDIR=dirname(abspath(__file__))

CONTAMIN=.05

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True,
                title='Outlier detection')
# log= logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

input_layout = html.Div(
    id= 'input_layout',
    children= [

        # style={'color':'purple'} does not work
        html.B('Mandatory inputs', id='m-inputs'),
        html.Div(id='input-section', children=[
        'Text file with rows for subjects and columns for features ',
        html.Br(),
        dcc.Upload(
            id='csv',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files'),
                html.Div(id='filename', className='filename-class'),
            ]),

            style={
                'width': '400px',
                'height': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',   # curvature of the border
                'textAlign': 'center',
                # 'margin': '10px',      # margin from left
                # 'lineHeight': '40px'   # height of a carriage return
            },
        ),

        html.Br(),
        'Output directory ',
        html.Br(),
        dcc.Input(
            value='',
            id='outDir',
            placeholder='Output directory ',
            debounce=True,
            style={
                'width': '20vw',
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
        )]),

        html.Br(),

        # style={'color':'darkgrey'} does not work
        html.B('Optional inputs', id='o-inputs'),
        html.Div(id='dgraph-section',
            children= html.Details(children=[
            html.Summary('Demographics'),
            html.Br(),
            'Text file with rows for subjects and columns for demographics ',
            html.Br(),
            dcc.Upload(
                id='participants',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files'),
                    html.Div(id='dgraph-filename', className='filename-class'),
                ]),

                style={
                    'width': '400px',
                    'height': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',  # curvature of the border
                    'textAlign': 'center',
                    # 'margin': '10px',      # margin from left
                    # 'lineHeight': '40px'   # height of a carriage return
                },
            ),

            html.Br(),
            'Control group',
            html.Br(),
            dcc.Input(
                id='control',
                style={
                    'width': '20vw',
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
                    'width': '20vw',
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
        ])
        ),

        html.Br(),
        html.Div([
            html.Button(id='analyze',
                        n_clicks_timestamp=0,
                        children='Analyze',
                        title='Analyze text file to detect outliers')],
            style={'float': 'center', 'display': 'inline-block'}),

        dcc.Loading(id='parse summary and compute zscore', fullscreen= True, debug=True, type='graph'),

        # Other dcc.Input()
        dcc.Store(id='df'),
        dcc.Store(id='subjects'),
        dcc.Store(id='dfcombined'),
        # other dcc.Store()

        html.Br(),
        html.Div(id='results', children=[
            html.Div('Analysis complete! Now you can browse through the summary below!', id='analyze-status'),
            html.Br(),
            dcc.Link('See outliers summary', href='/summary'),
            html.Br(),
            dcc.Link('See outliers in graphs and GLM fitting', id='compare-link', style={'display': 'none'}, href='/compare'),
            dcc.Link('See (raw) outliers in graphs', href='/graphs'),
            html.Br(),
            dcc.Link('See outliers in table', href='/zscores'),
            html.Br(),
            html.Br(),
            # using html.Button just for style's sake
            html.Div([
                html.Button(children=dcc.Link('Multivariate', href='/multivar'),
                            title='Direct to multivariate analysis')],
                style={'float': 'center', 'display': 'inline-block'})
        ], style={'display': 'none'})

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


compare_layout = html.Div(
    id= 'compare_layout',
    children= [

        dcc.Link('Go back to inputs', href='/user'),
        html.Br(),
        dcc.Link('See (raw) outliers in graphs', href='/graphs'),
        html.Br(),
        html.Br(),

        html.Div([
            dcc.Dropdown(
                id='region-compare',
            )
        ],
            style={'width': '48%', 'display': 'inline-block'}),


        html.Br(),
        'Corrected outliers, superimposed on the uncorrected ones, accounting for standard scores of the residuals:',
        dcc.Graph(id='stat-graph-compare'),
        dcc.Graph(id='model-graph'),
        html.Br(),
        dcc.Markdown(id='model-summary'),
        html.Br()
        ],

    style={'display': 'block', 'height': '0', 'overflow': 'hidden'}

)


table_layout= html.Div(
    id= 'table_layout',
    children= [

    dcc.Link('Go back to inputs', href='/user'),
    html.Br(),
    dcc.Link('See (raw) outliers in graphs', href='/graphs'),
    html.Br(),
    dcc.Link('See outliers summary', href='/summary'),
    html.Br(),

    html.H2('Standard scores of subjects for each feature'),
    html.Br(),
    dcc.Store(id='dfscores'),
    'Example: /data/pnl/HCP/derivatives/pnlpipe/sub-*/ses-01/anat/freesurfer',
    html.Br(),
    dcc.Input(
        value='',
        id='template',
        placeholder='freesurfer directory template',
        debounce=True,
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

    dcc.Loading(children=html.Div(id='generate table')),
    html.Div(id='table-content'),

    ],

    style={'display': 'block', 'height': '0', 'overflow': 'hidden'}
)


summary_layout = html.Div(
    id= 'summary_layout',
    children= [

        dcc.Link('Go back to inputs', href='/user'),
        html.Br(),
        dcc.Link('See (raw) outliers in graphs', href='/graphs'),
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
            dcc.Dropdown(
            id='multiv-method',
            options=[
                {'label': 'Isolation Forest', 'value': 'isf'},
                {'label': 'Mahalonobis distance', 'value': 'md'},
            ],
            value='isf'
            )],

        style={'width': '48%', 'display': 'inline-block'}),

        html.Br(),
        'Scores, calculated in the above method, falling outside [LOW,HIGH] percentiles are classified as outliers',
        html.Br(),
        'The defaults are: ',
        dcc.Input(
            value='',
            debounce=True,
            id='lower',
            # placeholder='LOW'
        ),

        dcc.Input(
            value='',
            debounce=True,
            id='higher',
            # placeholder='HIGH'
        ),
        html.Br(),
        html.Div([
            html.Button(id='multiv-button',
                        n_clicks_timestamp=0,
                        children='Perform multivariate analysis',
                        title='Perform multivariate analysis over all features together')],
            style={'float': 'center', 'display': 'inline-block'}),

        html.Br(),
        dcc.Loading(children=html.Div(id='isof-calculating')),
        html.Br(),

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

    # purpose of refresh is not understood
    html.Div(id='main-content',
             children=[input_layout, graph_layout, table_layout, summary_layout, multiv_layout, compare_layout]),
    dcc.Location(id='url', refresh=False),
    html.Br()
])



# callback for uploaded file
@app.callback(Output('filename', 'children'),
              [Input('csv', 'filename')])
def upload(filename):
    if not filename:
        raise PreventUpdate

    return 'Loaded: '+filename

# callback for uploaded file
@app.callback(Output('dgraph-filename', 'children'),
              [Input('participants', 'filename')])
def upload(filename):
    if not filename:
        raise PreventUpdate

    return 'Loaded: '+filename


# callback for input_layout / GLM analysis
# df.data will hold residuals= predicted-given
# dfcombined.data will hold a combined DataFrame of given and demographics
@app.callback([Output('region', 'options'), Output('region-compare', 'options'),
               Output('df', 'data'), Output('dfcombined','data'), Output('subjects','data'),
               Output('parse summary and compute zscore', 'children'), Output('analyze-status', 'style')],
              [Input('csv','contents'), Input('csv','filename'),
               Input('participants','contents'), Input('delimiter','value'),
               Input('outDir', 'value'),
               Input('effect','value'), Input('control','value'),
               Input('analyze', 'n_clicks')])
def analyze(raw_contents, filename, dgraph_contents, delimiter, outDir, effect, control, analyze):

    if not analyze:
        raise PreventUpdate

    _, contents = raw_contents.split(',')
    decoded = base64.b64decode(contents)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=delimiter_dict[delimiter])

    outDir= abspath(outDir)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True)


    if dgraph_contents:
        summaryCsv= pjoin(outDir, filename)
        df.to_csv(summaryCsv, index= False)

        _, contents = dgraph_contents.split(',')
        decoded = base64.b64decode(contents)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=delimiter_dict[delimiter])
        partiCsv= pjoin(outDir, '.participants.csv')
        df.to_csv(partiCsv, index= False)

        exe= pjoin(SCRIPTDIR, 'combine_demography.py')
        cmd= f'python {exe} -i {summaryCsv} -o {outDir} -p {partiCsv} -c "{control}"'
        check_call(cmd, shell=True)


        # python scripts/correct_for_demography.py -i asegstats_combined.csv -c asegstats_control.csv -e age
        # -p participants.csv -o dem_corrected/
        prefix= filename.split('.csv')[0]
        outPrefix= pjoin(outDir, prefix)
        exe= pjoin(SCRIPTDIR, 'correct_for_demography.py')
        cmd= f'python {exe} -i {outPrefix}_combined.csv -c {outPrefix}_control.csv -p {partiCsv} -e "{effect}" ' \
             f'-o {outDir}'
        check_call(cmd, shell=True)

        exog = '_'.join(effect.split('+'))
        residuals= f'{outPrefix}_{exog}_residuals.csv'
        # raw_contents being overwritten by residuals, our new feature for further analysis
        df= pd.read_csv(residuals)

        dfcombined= pd.read_csv(f'{outPrefix}_combined.csv')


    subjects = df[df.columns[0]].values
    regions = df.columns.values[1:]
    options = [{'label': i, 'value': i} for i in regions]

    # df is reset to residuals
    filename= pjoin(outDir, 'zscores.csv')
    # this block has to be done after prediction and residuals
    df_scores= df.copy()
    for column_name in regions:
        print(column_name)
        _, inliers, zscores= plot_graph(df, column_name)

        # write outlier summary
        df_scores[column_name] = zscores


    df_scores.to_csv(filename, index=False)

    # df.data will hold residuals= predicted-given
    # dfcombined.data will hold a combined DataFrame of given and demographics
    if dgraph_contents:
        return (options, options,
                df.to_dict('list'), dfcombined.to_dict('list'), subjects,
                True, {'display': 'block'})
    else:
        return (options, options,
                df.to_dict('list'), df.to_dict('list'), subjects,
                True, {'display': 'block'})



@app.callback([Output('results', 'style'), Output('compare-link', 'style')],
              [Input('participants','contents'), Input('dfcombined', 'data')])
def display_link(dgraph_contents, df):
    if dgraph_contents and df:
        return ({'display':'block'}, {'display':'block'})
    elif df:
        return ({'display':'block'}, {'display':'none'})
    else:
        raise PreventUpdate



# callback within multiv_layout
@app.callback([Output('lower', 'placeholder'), Output('higher', 'placeholder')],
               [Input('multiv-method', 'value')])
def show_multiv_summary(method):
    if method=='md':
        return ['0','80']
    elif method=='isf':
        return ['3','97']



# callback for multiv_layout
@app.callback([Output('multiv-summary', 'data'), Output('multiv-summary', 'columns'),
               Output('isof-calculating', 'children')],
              [Input('df','data'), Input('outDir', 'value'),
               Input('multiv-button','n_clicks'), Input('multiv-method', 'value'),
               Input('lower','value'), Input('higher','value')])
def show_multiv_summary(df, outDir, activate, method, PERCENT_LOW, PERCENT_HIGH):

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
    multiv_summary= pd.DataFrame(columns=columns)

    X= df.values
    meanX= np.mean(X, axis=0)
    ind= np.where(meanX==0)

    X= np.delete(X, ind, axis=1)
    meanX= np.delete(meanX, ind)

    if method=='md':
        PERCENT_LOW= int(PERCENT_LOW) if PERCENT_LOW else 0
        PERCENT_HIGH = int(PERCENT_HIGH) if PERCENT_HIGH else 80
        # Mahalanobis distance block =================================
        # Normalizing to avoid md^2 < 0
        X = X / np.max(X, axis=0)
        covX= np.cov(X, rowvar= False)
        icovX= np.linalg.inv(covX)
        MD= np.zeros((L,))
        for i in range(L):
            x= X[i,: ]
            MD[i]= mahalanobis(x, meanX, icovX)

        measure= MD

        # ENH could be done according to Chi2 probability, see draft/md_chi2_analysis.py

    elif method=='isf':
        PERCENT_LOW= int(PERCENT_LOW) if PERCENT_LOW else 3
        PERCENT_HIGH = int(PERCENT_HIGH) if PERCENT_HIGH else 97
        # IsolationForest block =================================
        rng = np.random.RandomState(123456)
        num_samples = len(subjects)
        iso_f = IsolationForest(max_samples=num_samples,
                                contamination=CONTAMIN,
                                random_state=rng)
        iso_f.fit(df)
        pred_scores = iso_f.decision_function(df)

        measure= pred_scores


    # Decision block
    h_thresh= scoreatpercentile(measure, PERCENT_HIGH)
    l_thresh = scoreatpercentile(measure, PERCENT_LOW)
    inliers= np.logical_and(measure <= h_thresh, measure >= l_thresh)

    for i in range(L):
        multiv_summary.loc[i] = [subjects[i], round(measure[i], 3), '' if inliers[i] else 'X']
        if ~inliers[i]:
            pass
            # md.loc[i] = [subjects[i], round(measure[i],3), 'X']

    filename= pjoin(outDir, 'outliers_multiv.csv')
    multiv_summary.to_csv(filename, index=False)

    return [multiv_summary.to_dict('records'), [{'name': i, 'id': i} for i in columns], True]



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
@app.callback([Output('table-content', 'children'),
               Output('generate table', 'children')],
               [Input('gen-table','n_clicks'), Input('outDir', 'value')])
def show_stats_table(activate, outDir):
    # print(button)
    if not activate:
        raise PreventUpdate

    outDir= abspath(outDir)

    filename= pjoin(outDir, 'zscores.csv')
    df_scores= pd.read_csv(filename)
    layout= show_table(df_scores)

    return (layout, True)



'''
Automatically opening an ROI image in a different tab is just not possible
https://community.plotly.com/t/trigger-a-click-on-html-a-from-callback/13234

@app.server.route() could have been a solution in the following ways:
  - Serving a static html with potential JavaScript coding for local image loading
    https://community.plotly.com/t/serve-static-html-to-new-tab/17383/2
  - Displaying local image
    https://github.com/plotly/dash/issues/71#issuecomment-313222343

Both the two approaches are curbed by display_page() callback
which would prevent rendering an image or html under http://localhost:8050
'''
# callback within table_layout
@app.callback([Output('roi-x', 'src'), Output('roi-y', 'src'), Output('roi-z', 'src'),
               Output('cmd', 'children'), Output('render ROI on brain', 'displayed'),
               Output('roi-markdown', 'href')],
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
        fsdir= template.replace('sub-*/', 'sub-{}/'.format(subjects[temp['row']]))
        if isdir(fsdir):
            fshome = getenv('FREESURFER_HOME', None)
            if not fshome:
                raise EnvironmentError('Please set FREESURFER_HOME and then try again')
            lut = pjoin(fshome, 'FreeSurferColorLUT.txt')
            lut = load_lut(lut)

            region= temp['column_id']
            cmd= render_roi(region, fsdir, lut, outDir, view_type)
            if view_type=='snapshot':
                roi_base64=['','','']
                for i, m in enumerate(['x', 'y', 'z']):
                    roi_png = pjoin(outDir, f'{region}_{m}.png')
                    roi_base64[i] = base64.b64encode(open(roi_png, 'rb').read()).decode('ascii')

                msg = ['Execute the following command in a terminal to open images in separate windows:',
                       html.Br(), html.Br(), cmd]
                return ['data:image/png;base64,{}'.format(roi_base64[0]),
                        'data:image/png;base64,{}'.format(roi_base64[1]),
                        'data:image/png;base64,{}'.format(roi_base64[2]),
                        msg,True,'/zscores#cmd']

            else:
                msg= ['Execute the following command in a terminal to see 3D rendering:',
                      html.Br(), html.Br(), cmd]
                return [None,None,None,msg,True,'/zscores#cmd']



    raise PreventUpdate



# callback for summary_layout
@app.callback([Output('summary', 'data'),
               Output('summary', 'columns')],
               [Input('subjects', 'data'), Input('outDir', 'value'),
               Input('extent','value'), Input('group-by', 'value')])
def update_summary(subjects, outDir, extent, group_by):

    # subjects only serve as a control for firing this callback
    if not subjects:
        raise PreventUpdate

    filename = pjoin(outDir, 'zscores.csv')
    df= pd.read_csv(filename)
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

    summary= pjoin(outDir, f'outliers-by-{group_by}.csv')
    dfs.to_csv(summary, index=False)

    return [dfs.to_dict('records'), columns]



@app.callback([Output(page, 'style') for page in ['input_layout', 'graph_layout', 'table_layout', 'summary_layout',
                                                  'multiv_layout', 'compare_layout']],
              [Input('url', 'pathname')])
def display_page(pathname):
    display_layout = [{'display': 'block', 'height': '0', 'overflow': 'hidden'} for _ in range(6)]

    if pathname == '/graphs':
        display_layout[1] = {'display': 'auto'}
    elif '/zscores' in pathname:
        display_layout[2] = {'display': 'auto'}
    elif pathname == '/summary':
        display_layout[3] = {'display': 'auto'}
    elif pathname == '/multivar':
        display_layout[4] = {'display': 'auto'}
    elif pathname == '/compare':
        display_layout[5] = {'display': 'auto'}
    else:
        display_layout[0] = {'display': 'auto'}

    return display_layout


if __name__=='__main__':
    app.run_server(debug=True, host='localhost')
