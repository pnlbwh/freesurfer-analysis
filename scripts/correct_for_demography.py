#!/usr/bin/env python

import argparse
from os.path import isfile, isdir, abspath, dirname, basename, join as pjoin, splitext
from os import makedirs
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


if __name__ == '__main__':

    parser= argparse.ArgumentParser(description='Correct the region based statistics accounting for demographic info. '
                                                'This program can be used after running combine_demography.py',
                                    formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-i', '--input', required=True,
                        help='a csv file containing region based statistics and demographic info')
    parser.add_argument('-c', '--control', required=True,
                        help='a csv file containing region based statistics and demographic info of the control group')
    parser.add_argument('-p', '--participants', required=True,
                        help='a csv file containing demographic info, demographic variable names are learnt from this file, '
                             'properties in the first row cannot have space or dash in them')
    parser.add_argument('-o', '--output', required=True, help='a directory where outlier analysis results are saved')
    parser.add_argument('-e', '--effect', required=True,
                        help='effect of demographic variable to be predicted, example:\n'
                             'age\n'
                             'age+eduyears\n'
                             'age+race\n')


    args= parser.parse_args()
    outDir= abspath(args.output)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True)

    df= pd.read_csv(abspath(args.input))
    df_demograph= pd.read_csv(abspath(args.participants))
    dfhealthy= pd.read_csv(abspath(args.control))
    df_corrected= df.copy()

    ids= df_demograph.iloc[:,0].values
    demographs= df_demograph.columns[1: ]

    regions= []
    for var in df.columns[1:]:
        if var not in demographs:
            regions.append(var)
        else:
            df_corrected.drop(var, axis=1, inplace= True)

    df_resid= df_corrected.copy()

    # model fitting and prediction
    exog= args.effect.split('+')
    for region in regions:
        print(region)

        formula = f'Q("{region}")~{args.effect}'
        endog_exog= [region]+ exog


        if dfhealthy[region].values.any():
            res = smf.glm(formula=formula, data=dfhealthy[endog_exog], family=sm.families.Gaussian()).fit()
            res.save(pjoin(outDir, f'.{region}.pkl'))
        else:
            continue

        print(res.summary())

        df_corrected[region]= res.predict(df[endog_exog])

        df_resid[region] = (df_corrected[region] - df[region]) ** 2

        print('\n')

    prefix= splitext(basename(args.input))[0].replace('_combined','')+ '_'+ '_'.join(exog)
    df_corrected.to_csv(pjoin(outDir, prefix + '_corrected.csv'), index=False)
    df_resid.to_csv(pjoin(outDir, prefix + '_residuals.csv'), index=False)
