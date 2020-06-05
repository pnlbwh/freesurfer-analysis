#!/usr/bin/env python

import argparse
from os.path import isfile, isdir, abspath, dirname, basename, join as pjoin, splitext
from os import makedirs, remove
import pandas as pd
import numpy as np
from util import delimiter_dict


if __name__ == '__main__':

    parser= argparse.ArgumentParser(description='Combine demographic info and region based statistics in one csv file',
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


    args= parser.parse_args()
    outDir= abspath(args.output)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True)

    df= pd.read_csv(abspath(args.input), sep=delimiter_dict[args.delimiter])
    df_demograph= pd.read_csv(abspath(args.participants), sep=delimiter_dict[args.delimiter])
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

    id_col_hdr= df.columns[0]
    dfcomb[id_col_hdr]= dfcomb[id_col_hdr].astype(df[id_col_hdr].dtype)

    prefix= splitext(basename(args.input))[0]
    dfcomb.to_csv(pjoin(outDir, prefix+'_combined.csv'), index=False)


    # filter the controls
    dfhealthy= dfcomb.query(args.control)
    dfhealthy.to_csv(pjoin(outDir, prefix+'_control.csv'), index=False)
