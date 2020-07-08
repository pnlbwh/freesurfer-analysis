#!/usr/bin/env python

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
import statsmodels.api as sm
import plotly.graph_objects as go
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from statsmodels.graphics.gofplots import qqplot
from os.path import isfile, isdir, abspath, join as pjoin
from os import makedirs

import pandas as pd
from scipy.stats import zscore, chi2
import numpy as np
import argparse
import logging

# from util import delimiter_dict
# from verify_ports import get_ports
# compare_port= get_ports('compare_port')

NUM_POINTS=20

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
log= logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def plot_graph_compare(df, df_resid, region, NUM_STD=2):
    '''
    :param region:
    :param NUM_STD: acceptable range of standard deviation
    :return:
    '''

    subjects = df[df.columns[0]].values
    L = len(subjects)
    val_mean = df[region].values.mean()
    val_std = df[region].values.std()
    # we need val_mean and val_std anyway so no using scipy.stats.zscore function
    zscores = np.array([round((y - val_mean) / val_std, 4) if val_std else 0 for y in df[region].values])
    inliers = abs(zscores) <= NUM_STD

    serial = np.arange(L)

    # modify inliers according to df_resid
    corr_zscores= np.empty(zscores.shape)
    if df[region].any():
        corr_zscores= np.round(zscore(df_resid[region].values), 4)
        # correct outliers only, a few inliers would become outliers, some blues become reds
        # inliers_corrected= abs(zscore(df_resid[region].values)) <= NUM_STD
        # inliers= np.logical_and(inliers, inliers_corrected)

        # correct inliers only, a few outliers would become inliers, some reds become blues
        # outliers_corrected= abs(zscore(df_resid[region].values)) > NUM_STD
        # inliers = ~np.logical_and(~inliers, outliers_corrected)

        # correct both, change of some inliers and outliers
        # identifiable by color only, disregard the acceptable range of NUM_STD
        # original zscores are preserved
        # should be the best logic
        inliers= abs(zscore(df_resid[region].values)) <= NUM_STD

    fig = go.Figure({
        'data': [
            # inliers
            dict(
                x=serial[inliers],
                y=df[region].values[inliers],
                text=[f'Sub: {id}, zscore: {z}<br>Corrected zscore: {zc}'
                      for id, z, zc in zip(subjects[inliers], zscores[inliers], corr_zscores[inliers])],
                mode='markers',
                name='inliers',
                marker={
                    'size': 15,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'},
                }
            ),
            # outliers
            dict(
                x=serial[~inliers],
                y=df[region].values[~inliers],
                text=[f'Sub: {id}, zscore: {z}<br>Corrected zscore {zc}'
                      for id,z,zc in zip(subjects[~inliers],zscores[~inliers],corr_zscores[~inliers])],
                mode='markers',
                name='outliers',
                marker={
                    'size': 15,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'},
                    'color': 'red'
                }
            ),
            # mean
            dict(
                x=serial,
                y=L * [val_mean],
                mode='lines',
                line={'color': 'black', 'width': 4},
                name='mean'
            ),
            # mean+ NUM*std
            dict(
                x=serial,
                y=L * [val_mean + NUM_STD* val_std],
                mode='lines',
                line={'dash': 'dash', 'color': 'green', 'width': 4},
                name=f'mean + {NUM_STD} x std'
            ),
            # mean- NUM_STD*std
            dict(
                x=serial,
                y=L * [val_mean - NUM_STD* val_std],
                mode='lines',
                line={'dash': 'dash', 'color': 'green', 'width': 4},
                name=f'mean - {NUM_STD} x std'
            )
        ],
        'layout': dict(
            xaxis={
                'title': 'Index of subjects'
            },
            yaxis={
                'title': region
            },
            margin={'l': 50, 'b': 100, 't': 30, 'r': 0},
            hovermode='closest',
            height=500
        )
    })

    # out_html = pjoin(outDir,f'{region}.html')
    # if not isfile(out_html):
    #     fig.write_html(out_html, include_plotlyjs='directory')

    return (fig, inliers, zscores)

def calc_line(exog, intercept, slope):

    xline = np.linspace(exog[:, 1].min(), exog[:, 1].max(), NUM_POINTS)
    yline = [x * slope + intercept for x in xline]

    return xline, yline

def display_model(region, outDir):

    print(f'\nDisplaying GLM fitting on {region}')

    res = sm.load_pickle(pjoin(outDir, f'.{region}.pkl'))

    fig = make_subplots(
        rows=2, cols=2,
    )

    X= res.model.exog[:,-1]
    Y= res.model.endog
    Yhat= res.mu

    line_fit = sm.OLS(Y, sm.add_constant(Yhat, prepend=True)).fit()


    # STY
    # all the go.Scatter() functions can accept
    # text=[f'Sub: {id}, zscore: {z}' for id, z in zip(subjects[inliers], zscores[inliers])]
    # for labelling each data point, however omitted, for brevity


    # endog vs exog
    if len(res.params)<=2:
        fig.add_trace(go.Scatter(x=X, y=Y,
                                 mode='markers', name=''), row=1, col=1)
        fig.update_layout(xaxis={'title': res.model.exog_names[-1]}, yaxis={'title': 'volume'})



    # Observed vs Fitted with line
    fig.add_trace(go.Scatter(x=Yhat, y=Y,
                             mode='markers', name=''), row=1, col=2)

    xline, yline= calc_line(line_fit.model.exog, line_fit.params[0], line_fit.params[1])
    fig.add_trace(go.Scatter(x=xline, y=yline,
                             mode='lines', name='OLS line',
                             line={'width': 3},
                             text=f'Slope={round(line_fit.params[1],3)}<br>Ideal slope=1.0'), row=1, col=2)
    fig.update_layout(xaxis2={'title': 'Fitted values'}, yaxis2={'title': 'Observed values'})



    # Residuals vs Fitted
    fig.add_trace(go.Scatter(x=Yhat, y=res.resid_pearson,
                             mode='markers', name=''), row=2, col=1)
    fig.add_trace(go.Scatter(x=np.linspace(Yhat.min(), Yhat.max(), NUM_POINTS), y=[0]*NUM_POINTS,
                             mode='lines', name='zero residual',
                             line={'width': 3}), row=2, col=1)
    fig.update_layout(xaxis3={'title': 'Fitted values'}, yaxis3={'title': 'Pearson residuals'})



    # Observed quantiles vs theoretical quantiles
    # Q-Q plot
    # https://en.wikipedia.org/wiki/Normal_probability_plot#Definition
    mpl_fig= plt.figure()
    ax= mpl_fig.gca()
    qqplot(res.resid_deviance, line='r', ax= ax)
    tempy= ax.lines[1].get_ydata()
    tempx= ax.lines[1].get_xdata()
    ols_slope= round((tempy[-1]-tempy[0]) / (tempx[-1]- tempx[0]),3)
    expected_slope= round(res.resid_deviance.std(),3)

    fig.add_trace(go.Scatter(x=ax.lines[0].get_xdata(), y=ax.lines[0].get_ydata(),
                             mode='markers', name=''), row=2, col=2)
    fig.add_trace(go.Scatter(x=ax.lines[1].get_xdata(), y=ax.lines[1].get_ydata(),
                             mode='lines', name='OLS line',
                             line={'width': 3},
                             text=f'Slope={ols_slope}<br>Ideal slope={expected_slope}'), row=2, col=2)
    fig.update_layout(xaxis4={'title': 'Quantiles of N(0,1)'}, yaxis4={'title': 'Deviance residual quantiles'})

    # close the figure to avoid freesurfer-analysis/issues/4
    plt.close(mpl_fig)

    # of the whole subplot
    fig.update_layout(title='Generalized linear model fitting on control group:')
    fig.update_layout(height=1000)

    # https://github.com/statsmodels/statsmodels/blob/160911ace8119eefe0e66998ea56d24e590fc415/statsmodels/base/model.py#L2457
    llr= -2*(res.llnull - res.llf)
    llr_pvalue= round(chi2.sf(llr, res.df_model),4)
    # https://stats.idre.ucla.edu/other/mult-pkg/faq/general/faq-what-are-pseudo-r-squareds/
    prsquared= round(1- res.llf/res.llnull,4)

    desc= f'''
##### Model summary
```
{str(res.summary())}
llr_pvalue: {llr_pvalue}
Psuedo R^2: {prsquared}
```

##### Interpretation
Direction for interpreting model (there is no single right answer)
* The lower the `llr_pvalue`, the better is the model fitting ~
* The higher the [`Psuedo R^2`](https://stats.idre.ucla.edu/other/mult-pkg/faq/general/faq-what-are-pseudo-r-squareds/), the better is the model fitting
* The lower the pvalue (`P>|z|`) of a particular coefficient, the more significant it is &#134
* The more compact a confidence interval `[0.025 0.975]` for a particular coefficient, the better is the estimation

~ Null hypothesis: fitted model is independent of the observation

&#134 Null hypothesis: the coefficient is zero based on the normal distribution
'''

    return (fig, desc)

# if __name__ == '__main__':
#
#     parser= argparse.ArgumentParser(
#         description='Visually compare raw outliers against demographic variable corrected ones')
#
#     parser.add_argument('-i', '--input', required=True, help='a csv/tsv file containing region based statistics')
#     parser.add_argument('-c', '--corrected', required=True,
#                         help='a *_residual.csv file that was obtained after correcting statistics for demographic variable(s)')
#     parser.add_argument('-p', '--participants', required=True,
#                         help='a csv file containing demographic info, demographic variable names are learnt from this file, '
#                              'properties in the first row cannot have space or dash in them')
#     parser.add_argument('-d', '--delimiter', default='comma', help='delimiter used between measures in the --input '
#                                                                    '{comma,tab,space,semicolon}, default: %(default)s')
#     parser.add_argument('-o', '--output', required=True, help='a directory where outlier analysis results are saved')
#     parser.add_argument('-e', '--extent', type= float, default=2, help='values beyond mean \u00B1 e*STD are outliers, if e<5; '
#                         'values beyond e\'th percentile are outliers, if e>70; default %(default)s')
#
#     args= parser.parse_args()
#     outDir= abspath(args.output)
#     if not isdir(outDir):
#         makedirs(outDir, exist_ok= True)
#
#     df = pd.read_csv(abspath(args.input),sep=delimiter_dict[args.delimiter])
#     df_demograph = pd.read_csv(abspath(args.participants))
#     demographs = df_demograph.columns[1:]
#
#     regions = [var for var in df.columns.values[1:] if var not in demographs]
#     subjects = df[df.columns[0]].values
#
#     df_resid= pd.read_csv(abspath(args.corrected))
#
#     # generate all figures
#     df_inliers= df.copy()
#     # the below overwrite is for debugging only
#     # regions=['CSF', 'Brain-Stem', 'Left-Accumbens-area']
#     for column_name in regions:
#         print(column_name)
#         _, inliers, zscores= plot_graph(column_name, args.extent)
#
#         # write outlier summary
#         df_inliers[column_name] = zscores
#
#
#     df_inliers.to_csv(pjoin(outDir, 'outliers.csv'), index=False)


