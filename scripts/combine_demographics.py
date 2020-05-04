#!/usr/bin/env python

import argparse
from os.path import isfile, isdir, abspath, dirname, join as pjoin
from os import makedirs, remove
import pandas as pd
import numpy as np


if __name__ == '__main__':

    parser= argparse.ArgumentParser(description='Detect and demonstrate outliers in FreeSurfer statistics',
                                    formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-i', '--input', required=True,
                        help='a csv file containing region based statistics, first column is subject ids')
    parser.add_argument('-p', '--participants', required=True,
                        help='a csv file containing demographic info, first column is subject ids, '
                             'properties in the first row cannot have space or dash in them'
                             'demographic info of matched subject ids are exported to output/combined.csv')
    parser.add_argument('-d', '--delimiter', default='comma', help='delimiter used between measures in the --input '
                                                                   '{comma,tab,space,semicolon}, default: %(default)s, '
                                                                   'same delimiter must be used for both -i and -p')
    parser.add_argument('-o', '--output', required=True, help='a directory where outlier analysis results are saved')
    parser.add_argument('-c', '--control', required=True,
                        help='healthy control subjects to filter from --participants, provide a mathematical expression '
                             'to filter subjects, see README.md for details, examples:\n'
                             'age>40 and age<50\n'
                             'age>50\n'
                             'race==\'hispanic\'\n'
                             'race==\'hispanic\' or (age>40 and age<50)\n'
                             'checkin_bin==3')

    # df = pd.read_csv('C://Users/tashr/Documents/fs-stats/outliers.csv')
    # outDir = 'C://Users/tashr/Documents/fs-stats/'

    args= parser.parse_args()
    outDir= abspath(args.output)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True)

    df= pd.read_csv(abspath(args.input))
    df_demograph= pd.read_csv(abspath(args.participants))
    dfcomb= pd.DataFrame(columns=df.columns)

    ids= df_demograph.iloc[:,0].values
    demographs= df_demograph.columns[1: ]

    # not all ids from participants can be in input, so the following complicated logic
    i=0
    for id in ids:
         dfcomb.loc[i]= df.loc[np.where(id==ids)[0][0]]
         i+=1

    for attr in demographs:
        temp= df_demograph[attr]
        dfcomb[attr]= temp.astype(temp.dtype)

    dfcomb.to_csv(pjoin(outDir, 'combined.csv'), index=False)


    # filter the controls
    dfhealthy= dfcomb.query(args.control)
    dfhealthy.to_csv(pjoin(outDir, 'control.csv'), index=False)
