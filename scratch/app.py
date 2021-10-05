#!/usr/bin/env python

from glob import glob
import base64, io
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash_table import DataTable
from dash.exceptions import PreventUpdate
from os.path import isfile, isdir, abspath, join as pjoin, dirname, splitext, basename
from os import makedirs, getenv, remove, listdir
from scipy.spatial.distance import mahalanobis
from scipy.stats import scoreatpercentile
from sklearn.ensemble import IsolationForest

import pandas as pd
import numpy as np
import argparse
import logging
from tempfile import mkstemp

from subprocess import check_call

SCRIPTDIR=dirname(abspath(__file__))

CONTAMIN=.05

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True,
                title='Outlier detection')
# log= logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)


def _glob(dir):

    items= glob(pjoin(dir, '*'))
    filtered= []
    for item in items:
        if isdir(item) or item.endswith('.txt') or item.endswith('.csv'):
            filtered.append(item)

    return [pjoin(dir,item) for item in filtered]


df=pd.DataFrame(columns=['/'], data=_glob('/'))


app.layout = html.Div(
    children= [
        html.Div(children= [
        html.Img(src='https://raw.githubusercontent.com/pnlbwh/freesurfer-analysis/multi-user/docs/pnl-bwh-hms.png'),
        dcc.Markdown(
"""[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.3762476.svg)](https://doi.org/10.5281/zenodo.3762476) [![Python](https://img.shields.io/badge/Python-3.6-green.svg)]() [![Platform](https://img.shields.io/badge/Platform-linux--64%20%7C%20osx--64%20%7C%20win--64-orange.svg)]()

Billah, Tashrif; Bouix, Sylvain; *FreeSurfer outlier analysis tool*, https://github.com/pnlbwh/freesurfer-analysis, 2020, 
DOI: 10.5281/zenodo.3762476

---

**freesurfer-analysis** is an interactive statistics visualization tool. Assuming the statistics are normally distributed, 
elements in the statistics beyond ±2 standard deviations are classified as outliers. More details about the tool can be found [here](https://github.com/pnlbwh/freesurfer-analysis/blob/multi-user-dgraph/docs/description.pdf).
Input to the tool is a summary table with **rows for subjects** and **columns for regions** obtained from FreeSurfer statistics 
of a set of subjects. Although the tool is developed for analyzing FreeSurfer statistics, it can be readily employed with 
other statistics having a summary table such as those obtained from Tract-Based Spatial Statistics (TBSS) study.

* Input can be provided from PNL server or your computer. However, output is always written to PNL server.
    * When on a PNL workstation or HPC node through NoMachine, use **From PNL server** option
    * When data is totally in your laptop, use **From your computer** option
* If demographic information is provided, then outliers are corrected considering their effect.
* If FreeSurfer directory template is provided, static ROI snapshots are rendered.
"""),
        html.Hr(),], id='introduction'),


        # style={'color':'purple'} does not work
        html.B('Mandatory inputs', id='m-inputs'),
        html.Div(id='input-section', children=[

            'Text file with rows for subjects and columns for features',
            html.Br(),
            
            html.Summary('From PNL server'),

            html.Div(className='type-inst', children=[
                'Type in the box below--',
                html.Li('suggestion menu will update as you type'),
                html.Li('yet you must type up to the last directory'),
                html.Li('then select a file from the dropdown menu'),
            ]),

            dcc.Dropdown(
                id='filename-dropdown',
                options=[{'label': '', 'value': '/'}],
                value='',
                placeholder= '/abs/path/to/file (*csv,*tsv)',
                className= 'path-selector'
            ),

            html.Div(id='dropdown-select', className='filename-class'),

            html.Br(),

        html.Br(),
        html.Div([
            html.Button(id='analyze',
                        n_clicks_timestamp=0,
                        children='Analyze',
                        title='Analyze text file to detect outliers')],
            style={'float': 'center', 'display': 'inline-block'}),

        dcc.Loading(id='parse summary and compute zscore', fullscreen= True, debug=True, type='graph'),


        html.Br(),

    ]),
        
        html.Div(
            html.Button(id='up',
                        n_clicks_timestamp=0,
                        children='↑↑',
                        title='Go back one directory'),
                        style={'float': 'right', 'display': 'block'}
        ),
                
        html.Br(),
        html.Div(id= 'empty',
        children=[DataTable(
        id='table',
        columns=[{'name': f'{i}',
                  'id': i,
                  'hideable': False,
                  'type': 'text',
                  } for i in df.columns],
        data=df.to_dict('records'),
        filter_action='none',
        sort_action='none',
        style_cell={
            'textAlign': 'left',
            'whiteSpace': 'pre-wrap',
            'width': '20px'
        },

        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        })
        ])
        
        ]
        
)


@app.callback([Output('table', 'data'),Output('table', 'columns')],
              Input('table', 'selected_cells'))
def get_active_cell(selected_cells):

    if selected_cells:
        temp = selected_cells[0]
        # print(temp)
        
        old_dir= temp['column_id']
        old_list= _glob(old_dir)
        
        row= temp['row']
        
        new_dir= old_list[row]
        new_list= _glob(new_dir)

        # print(new_dir)
        
        df=pd.DataFrame(columns=[new_dir], data=new_list)
        
        columns=[{'name': new_dir,
                  'id': new_dir,
                  'hideable': True,
                  'type': 'text'
                  }]
        
        return df.to_dict('records'), columns

    raise PreventUpdate
    

@app.callback(Output('empty', 'children'),
              [Input('up', 'n_clicks'), Input('table','columns')])
def update_table(up, columns):

    changed = [item['prop_id'] for item in dash.callback_context.triggered][0]

    if 'up' in changed:
        
        # print(changed)
        
        old_dir= dirname(columns[0]['id'])
        df=pd.DataFrame(columns=[old_dir], 
            data=_glob(old_dir))
        
        return DataTable(
            id='table',
            columns=[{'name': f'{i}',
                      'id': i,
                      'hideable': False,
                      'type': 'text',
                      } for i in df.columns],
            data=df.to_dict('records'),
            filter_action='none',
            sort_action='none',
            style_cell={
                'textAlign': 'left',
                'whiteSpace': 'pre-wrap',
                'width': '20px'
            },

            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            )
    else:
        raise PreventUpdate
    


if __name__=='__main__':
    app.run_server(debug=True, host='localhost')
    
    
