#!/usr/bin/env python

from tempfile import TemporaryDirectory, mkdtemp
from os.path import isdir, join as pjoin, abspath
from os import symlink, makedirs, environ
from subprocess import check_call, Popen
import argparse
from shutil import rmtree

def stats2table(caselist, template, outDir, measure='volume', delimiter='comma', parc='aparc'):

    tmpdir= mkdtemp()

    with open(caselist) as f:
        cases= [c.strip() for c in f.read().strip().split()]

    for c in cases:
        fsdir = template.replace('*', c)
        if isdir(fsdir):
            symlink(fsdir, pjoin(tmpdir, c))

    fsbin= environ['FREESURFER_HOME']+ '/bin'
    modified_env= environ.copy()
    modified_env['SUBJECTS_DIR']= tmpdir
    for hemi in ['lh', 'rh']:
        cmd = f'{fsbin}/aparcstats2table --subjectsfile={caselist} --hemi={hemi} -m {measure} -d {delimiter} ' \
              f'--skip -t {outDir}/aparcstats_{hemi}.csv --parc {parc}'
        check_call(cmd, shell=True, env=modified_env)


    cmd = f'{fsbin}/asegstats2table --subjectsfile={caselist} -m {measure} -d {delimiter} ' \
          f'--skip -t {outDir}/asegstats.csv'
    check_call(cmd, shell=True, env=modified_env)
    
    rmtree(tmpdir)


if __name__== '__main__':
    parser= argparse.ArgumentParser(
        description='Make symbolic links of freesurfer directories in one place and generate {aseg,aparc}stats2table')

    parser.add_argument('-c', '--caselist', required=False,
                        help='subject ids from the caselist are used in template to obtain valid freesurfer directory')
    parser.add_argument('-t', '--template', required=False,
                        help='freesurfer directory pattern enclosed in double quotes e.g. '
                             '"/path/to/*/freesurfer" or "/path/to/derivatives/pnlpipe/sub-*/anat/freesurfer", '
                             'where * is the placeholder for subject id')
    parser.add_argument('-o', '--output', required=True, help='a directory where outlier analysis results are saved')
    parser.add_argument('-p', '--parc', default='aparc',
                        help='parcellation stats to use with aparcstats2table (alternative is aparc.a2009s)')
    parser.add_argument('-d', '--delimiter', default='comma', help='delimiter to use between measures in the output table '
                                                                   '{comma,tab,space,semicolon}, default: %(default)s')

    parser.add_argument('-m', '--measure', default='volume',
                        help='measure extracted from stats/{asegstats,aparcstats_{lh,rh}}.tsv files, default: %(default)s. '
                             'See `asegstats2table -h` and `aparcstats2table -h` for supported measures')

    args= parser.parse_args()
    outDir= abspath(args.output)
    if not isdir(outDir):
        makedirs(outDir, exist_ok= True)
    
    stats2table(abspath(args.caselist), args.template, outDir, args.measure, args.delimiter, args.parc)

