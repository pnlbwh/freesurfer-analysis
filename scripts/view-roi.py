#!/usr/bin/env python

from matplotlib import pyplot
from nilearn.plotting import plot_roi
from nibabel import Nifti1Image
from nibabel.freesurfer import load as fsload
from nibabel.freesurfer import MGHImage
from matplotlib.colors import ListedColormap
from subprocess import check_call
from os.path import join as pjoin
from os import remove, close
from tempfile import mkstemp

OPACITY = 0.8

def load_lut(lut):

    with open(lut) as f:
        content= f.read().split('\n')

    lut_colors=[]
    for line in content:
        if line and '#' not in line:
            lut_colors.append(line.split())

    return lut_colors

def render_roi(table_header, fsdir, lut, method='snapshot'):

    # define files according to FreeSurfer structure
    brain_mgh= pjoin(fsdir, 'mri/brain.mgz')

    if 'lh' in table_header or 'rh' in table_header:
        hemis, ctx, _ = table_header.split('_')
        region = f'ctx-{hemis}-{ctx}'
        seg_mgh=pjoin(fsdir, 'mri/aparc+aseg.mgz')
        cortex= True
    else:
        seg_mgh = pjoin(fsdir, 'mri/aseg.mgz')
        region= table_header

    roi_mgh= mkstemp(suffix='.mgz', prefix=region+'-')


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
    MGHImage(roi, affine= seg.affine, header= seg.header).to_filename(roi_mgh[1])

    if method=='snapshot':
        plot_roi(roi_nifti, bg_img= brain_nifti, draw_cross=False, cmap= color)
        pyplot.show()
        # snapshot = mkstemp(suffix='.png', prefix=region+'-')
        # plot_roi(roi_nifti, bg_img=brain_nifti, draw_cross=False, cmap=color, output_file= snapshot[1])
        # close(snapshot[0])
        # remove(snapshot[1])
    elif method=='freeview':

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
            check_call([f'freeview -v {brain_mgh} '
                        f'{roi_mgh}:colormap=lut:opacity={OPACITY} '
                        f'{seg_mgh}:colormap=lut:opacity={OPACITY}'], shell=True)


    close(roi_mgh[0])
    remove(roi_mgh[1])

if __name__=='__main__':
    fsdir=r'C:\\Users\\tashr\\Documents\freesurfer'
    lut = r'C:\\Users\\tashr\\Documents\FreeSurferColorLUT.txt'

    lut_colors= load_lut(lut)
    table_header = 'Left-Thalamus-Proper'
    # table_header= 'Left-Lateral-Ventricle'
    # table_header = 'lh_transversetemporal_volume'
    table_header= 'rh_frontalpole_volume'
    render_roi(table_header, fsdir, lut_colors, method='snapshot')


