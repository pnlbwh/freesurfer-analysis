#!/usr/bin/env python

from nilearn.plotting import plot_roi
from nibabel import Nifti1Image
from nibabel.freesurfer import load as fsload
from nibabel.freesurfer import MGHImage
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot
from matplotlib.colors import ListedColormap
from subprocess import check_call
from os.path import join as pjoin, abspath, isfile
from os import remove, close, getenv
from tempfile import mkstemp, mkdtemp
from shutil import rmtree
import dash
import dash_html_components as html
import webbrowser
import argparse

OPACITY = 0.8

def load_lut(lut):

    with open(lut) as f:
        content= f.read().split('\n')

    lut_colors=[]
    for line in content:
        if line and '#' not in line:
            lut_colors.append(line.split())

    return lut_colors

def render_roi(table_header, fsdir, lut, outDir, method='snapshot'):

    # define files according to FreeSurfer structure
    brain_mgh= pjoin(fsdir, 'mri/brain.mgz')
    if not isfile(brain_mgh):
        print(brain_mgh, 'does not exist. Provide a valid freesurfer directory')
        exit()


    if 'lh' in table_header or 'rh' in table_header:
        hemis, ctx, _ = table_header.split('_')
        region = f'ctx-{hemis}-{ctx}'
        seg_mgh=pjoin(fsdir, 'mri/aparc+aseg.mgz')
        cortex= True
    else:
        region= table_header
        seg_mgh = pjoin(fsdir, 'mri/aseg.mgz')
        cortex= False

    roi_mgh= pjoin(outDir, region+'.mgz')


    invalid= True
    for i in range(len(lut)):
        if lut[i][1]==region:
            color= ListedColormap([int(x)/255 for x in lut[i][2:-1]])
            label= int(lut[i][0])
            invalid= False
            break

    if invalid:
        print(f'{region} is not a valid aparc or aseg segment')
        exit()


    brain= fsload(brain_mgh)
    seg= fsload(seg_mgh)

    brain_nifti= Nifti1Image(brain.get_fdata(), affine= brain.affine)

    roi= (seg.get_fdata()==label)*label
    roi_nifti= Nifti1Image(roi, affine= seg.affine)

    cmd = ''
    if method=='snapshot':
        plot_roi(roi_nifti, bg_img=brain_nifti, draw_cross=False, cmap=color, title=region,
                 output_file= pjoin(outDir, region+'.png'))
        # pyplot.show()


        # if a separate folder is not used as assets_folder, dash will try loading all its content
        # so create a tmpdir and save the snapshot there
        # problem with this approach:
        #       i. debug=False, no way to stop the server, plot does not refresh with selected cells on the web browser
        #       ii. debug=True, signal from opened pyplot does not mingle with callback signal
        #
        # tmpdir= mkdtemp()
        # plot_roi(roi_nifti, bg_img=brain_nifti, draw_cross=False, cmap=color, title=region, 
        #          output_file= tmpdir+ f'/{region}.png')

        # app = dash.Dash(__name__, assets_folder=tmpdir, assets_url_path='/')
        # app.layout = html.Div([
        #     html.Img(src=f'{region}.png')
        # ])
        # webbrowser.open('http://localhost:8010')
        # app.run_server(port=8010, host= 'localhost')
        # rmtree(tmpdir)

    elif method=='freeview':

        MGHImage(roi, affine=seg.affine, header=seg.header).to_filename(roi_mgh)

        if cortex:
            # show aparc+aseg
            # background brain.mgz
            # foreground roi.mgz and aparc+aseg.mgz
            # surfaces pial and white
            white_mgh= pjoin(fsdir, f'surf/{hemis}.white')
            pial_mgh= pjoin(fsdir, f'surf/{hemis}.pial')
            check_call([f'freeview -v {brain_mgh} '
                        f'{roi_mgh}:colormap=lut:opacity={OPACITY} '
                        f'{seg_mgh}:colormap=lut:opacity={OPACITY} '
                        f'-f {white_mgh}:edgecolor=red '
                        f'{pial_mgh}:edgecolor=yellow'], shell=True)

        else:
            # show aseg
            # background brain.mgz
            # foreground roi.mgz and aseg.mgz
            # check_call([f'freeview -v {brain_mgh} '
            #             f'{roi_mgh}:colormap=lut:opacity={OPACITY} '
            #             f'{seg_mgh}:colormap=lut:opacity={OPACITY}'], shell=True)
            cmd= ' '.join([f'freeview -v {brain_mgh} '
                           f'{roi_mgh}:colormap=lut:opacity={OPACITY} '
                           f'{seg_mgh}:colormap=lut:opacity={OPACITY} &'])
            print(cmd)


    # remove(roi_mgh)

    return cmd

if __name__=='__main__':
    # fsdir=r'C:\\Users\\tashr\\Documents\freesurfer'
    # lut = r'C:\\Users\\tashr\\Documents\FreeSurferColorLUT.txt'
    # lut_colors= load_lut(lut)
    # table_header = 'Left-Thalamus-Proper'
    # table_header= 'Left-Lateral-Ventricle'
    # table_header = 'lh_transversetemporal_volume'
    # table_header= 'rh_frontalpole_volume'
    # render_roi(table_header, fsdir, lut_colors, method='snapshot')

    parser= argparse.ArgumentParser(
        description='Render ROI overlaid on the brain, responds to selected cells in stats table')

    parser.add_argument('-i', '--input', help='freesurfer directory')
    parser.add_argument('-l', '--label', required=True, help='column header in the zscores table')
    parser.add_argument('-o', '--output', required=True, help='a directory where ROI files are written')
    parser.add_argument('-v', '--view-type', default='snapshot',
                        help='snapshot or freeview; method for rendering ROI; default %(default)s')

    args= parser.parse_args()

    fshome= getenv('FREESURFER_HOME', None)
    if not fshome:
        raise EnvironmentError('Please set FREESURFER_HOME and then try again')
    lut= pjoin(fshome, 'FreeSurferColorLUT.txt')
    lut_colors= load_lut(lut)

    render_roi(args.label, abspath(args.input), lut_colors, abspath(args.output), args.view_type)

