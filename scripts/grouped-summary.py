#!/usr/bin/env python

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_table
import pandas as pd

app = dash.Dash(__name__)

df= pd.read_csv(r'C:\Users\tashr\Documents\fs-stats\outliers.csv')
summary= r'C:\Users\tashr\Documents\fs-stats\grouped-by-subjects.csv'

app.layout = html.Div([

        'Group outliers by: ',
        html.Div([
            dcc.Dropdown(
                id='group-by',
                options=[{'label': i, 'value': i} for i in ['subjects','regions']],
                value='subjects'
            )
        ],
        style = {'width': '10%',}),
        html.Br(),

        dash_table.DataTable(
            id='summary',
            filter_action='native',
            sort_action='native',
            style_cell={'textAlign': 'left'},

            style_data_conditional=[{
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(240, 240, 240)'
            }],

            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
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
            dfs.loc[i]=[df.loc[i][0], len(outliers), ';'.join([x for x in outliers])]

    else:
        dfs = pd.DataFrame(columns=['Regions', '# of outliers', 'outliers'])
        columns = [{'name': i,
                    'id': i,
                    'hideable': True,
                    } for i in dfs.columns]

        for i,region in enumerate(df.columns[1:]):
            outliers= df[df.columns[0]].values[df[region]>2]
            dfs.loc[i] = [region, len(outliers), ';'.join([x for x in outliers])]


    return [dfs.to_dict('records'), columns]

if __name__ == '__main__':
    app.run_server(debug=True, port= 8020, host= 'localhost')


