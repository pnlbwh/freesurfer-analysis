import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.graphics.api import abline_plot
from matplotlib import pyplot as plt
import numpy as np
from scipy import stats

RESID_TYPE= 'deviance'
NUM_STD=2
BINS= 7

# df= pd.read_csv(r'C:/Users/tashr/Documents/diag-cte/healthy.csv')
df= pd.read_csv(r'C:/Users/tashr/Documents/diag-cte/healthyaparc.csv')
# df= pd.read_csv(r'C:/Users/tashr/Documents/diag-cte/allcombined.csv')

regions = df.columns.values[1:]
subjects = df[df.columns[0]].values

for region in regions:
    print(region)

def display_graph():
    # actual volume
    fig, ax= plt.subplots(2,3)
    ax[0][0].grid()
    ax[0][0].set_xlabel('age')
    ax[0][0].set_ylabel('Volume')
    ax[0][0].set_title(region)
    ax[0][0].scatter(df['age'], df[region])

    # ax[0][1].set_ylim(ratio.min(), ratio.max())
    ax[0][1].grid()
    ax[0][1].set_xlabel('age')
    ax[0][1].set_ylabel('Ratio')
    ax[0][1].set_title(region)
    ax[0][1].scatter(df['age'], ratio)

    formula= f'Q("{region}")~age'


    res = smf.glm(formula=formula, data=dftemp[[region,'age']], family=sm.families.Gaussian()).fit()
    print(res.summary())

    y= dftemp[region]
    yhat= res.mu
    ax[1][0].scatter(yhat, y)
    line_fit = sm.OLS(y, sm.add_constant(yhat, prepend=True)).fit()
    abline_plot(model_results=line_fit, ax=ax[1][0], color= 'k')
    ax[1][0].set_xlim(yhat.min(), yhat.max())
    ax[1][0].set_ylim(y.min(), y.max())
    ax[1][0].grid()
    # ax[1][0].set_title('Model Fit Plot')
    ax[1][0].set_ylabel('Observed values')
    ax[1][0].set_xlabel('Fitted values')


    resid= eval(f'res.resid_{RESID_TYPE}')
    ax[1][1].scatter(yhat, resid)
    ax[1][1].hlines(0, yhat.min()*0.5, yhat.max()*1.5)
    ax[1][1].set_xlim(yhat.min(), yhat.max())
    ax[1][1].set_ylim(resid.min(), resid.max())
    ax[1][1].grid()
    # ax[1][1].set_title('Residual Dependence Plot')
    ax[1][1].set_ylabel(f'{RESID_TYPE} residuals')
    ax[1][1].set_xlabel('Fitted values')


    resid_std = stats.zscore(resid)
    ax[1][2].hist(resid_std, bins=BINS)
    ax[1][2].grid()
    ax[1][2].set_title('Histogram of residuals')
    ax[1][2].set_xlabel(f'zscore of {RESID_TYPE}')
    ax[1][2].set_ylabel('# of subjects')

    fig.show()

    print('\n')
    outliers= np.logical_or(resid_std>NUM_STD, resid_std<-NUM_STD)
    print(subjects[outliers])
    print('\n')


while 1:
# for region in regions:
    temp= input()
    region= temp
    if temp=='q':
        break

    try:
        ratio= df[region]/df['EstimatedTotalIntraCranialVol']
    except:
        ratio = df[region] / df['eTIV']

    dftemp= df.copy()
    display_graph()

    dftemp[region]= np.nan_to_num(ratio)
    display_graph()

