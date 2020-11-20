#!/usr/bin/env python

import argparse
from os.path import isfile, isdir, abspath, dirname, basename, join as pjoin, splitext
from os import makedirs, remove
from time import sleep
SCRIPTDIR=dirname(abspath(__file__))
from subprocess import check_call, Popen
from verify_ports import get_ports


if __name__ == '__main__':

    parser= argparse.ArgumentParser(description="""This is a wrapper for four scripts: '
combine_demography
correct_for_demography
generate-summary
compare-correction
In total, its purpose is to calculate outliers incorporating demographics and display them.""",
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
    parser.add_argument('--effect', required=True,
                        help='effect of demographic variable to be predicted, example:\n'
                             'age\n'
                             'age+eduyears\n'
                             'age+race\n')
    parser.add_argument('--extent', type=float, default=2, help='values beyond mean \u00B1 e*STD are outliers, if e<5; '
                        'values beyond e\'th percentile are outliers, if e>70; default %(default)s')
    parser.add_argument('-t', '--template', required=False,
                        help='freesurfer directory pattern i.e. /path/to/$/freesurfer or '
                             '/path/to/derivatives/pnlpipe/sub-$/anat/freesurfer, '
                             'where $ sign is the placeholder for subject id '
                             'ROI rendering is disabled if not provided')

    args = parser.parse_args()

    get_ports()

    # python scripts\combine_demography.py -i asegstats.csv -o dem_corrected/ -p participants.csv -c "checkin_bin==3"
    exe= pjoin(SCRIPTDIR, 'combine_demography.py')
    cmd= f'python {exe} -i {args.input} -o {args.output} -p {args.participants} -c "{args.control}"'
    check_call(cmd, shell=True)


    # python scripts\correct_for_demography.py -i asegstats_combined.csv -c asegstats_control.csv -e age
    # -p participants.csv -o dem_corrected/
    prefix= basename(args.input).split('.csv')[0]
    outPrefix= pjoin(args.output, prefix)
    exe= pjoin(SCRIPTDIR, 'correct_for_demography.py')
    cmd= f'python {exe} -i {outPrefix}_combined.csv -c {outPrefix}_control.csv -p {args.participants} -e "{args.effect}" ' \
         f'-o {args.output}'
    check_call(cmd, shell=True)

    exog = '_'.join(args.effect.split('+'))
    residuals= f'{outPrefix}_{exog}_residuals.csv'


    # python scripts\generate-summary.py -i asegstats_residuals.csv -o dem_corrected/
    exe= pjoin(SCRIPTDIR, 'generate-summary.py')
    cmd= f'python {exe} -i {residuals} -e {args.extent} -o {args.output} -t {args.template}'
    Popen(cmd, shell=True)


    # force the pipeline to wait because outlier.csv is required in the subsequent step
    # if not put to sleep, then it would progress to compare_correction right away
    # and raise EnvironmentError for compare_port
    sleep_time= 60
    print(f'\nWaiting {sleep_time} seconds for previous job to complete ...\n')
    sleep(sleep_time)
    while 1:
        if isfile(pjoin(args.output,'outliers.csv')):
            break


    # python scripts\compare_correction.py -i asegstats_combined.csv -c asegstats_age_residuals.csv
    # -p participants.csv -o dem_corrected/
    exe= pjoin(SCRIPTDIR, 'compare_correction.py')
    cmd= f'python {exe} -i {outPrefix}_combined.csv -c {residuals} -p {args.participants} ' \
         f'-e {args.extent} -o {args.output}'
    Popen(cmd, shell=True)

