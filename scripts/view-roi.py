#!/usr/bin/env python

from nilearn.plotting import plot_roi
from nibabel import Nifti1Image
from nibabel.freesurfer import load as fsload
from nibabel.freesurfer import MGHImage
from matplotlib.colors import ListedColormap
from subprocess import check_call
from os.path import join as pjoin
import sys

# fsdir=''
# brain_mgh= pjoin(fsdir,'mri/brain.mgz')
# aseg_mgh= pjoin(fsdir,'mri/aseg.mgz')
brain_mgh= r'C:\\Users\\tashr\\Documents\brain.mgz'
aseg_mgh= r'C:\\Users\\tashr\\Documents\aseg.mgz'

roi_mgh= r'C:\\Users\\tashr\\Documents\roi.mgz'

lut= r'C:\\Users\\tashr\\Documents\ASegStatsLUT.txt'
region= 'Left-Lateral-Ventricle'
# region= 'Left-Thalamus-Proper'
snapshot= r'C:\\Users\\tashr\\Documents\snapshot.png'

def load_lut(lut):

    with open(lut) as f:
        content= f.read().split('\n')

    rows=[]
    for line in content:
        if line and '#' not in line:
            rows.append(line.split())

    return rows

rows= load_lut(lut)
for i in range(len(rows)):
    if rows[i][1]==region:
        color= ListedColormap([int(x)/255 for x in rows[i][2:-1]])
        label= int(rows[i][0])

brain= fsload(brain_mgh)
aseg= fsload(aseg_mgh)

brain_nifti= Nifti1Image(brain.get_fdata(), affine= brain.affine)

roi= (aseg.get_fdata()==label)*label
roi_nifti= Nifti1Image(roi, affine= brain.affine)
MGHImage(roi, affine= brain.affine, header= brain.header).to_filename(roi_mgh)

plot_roi(roi_nifti, bg_img= brain_nifti, cmap= color, output_file=snapshot)

# background brain.mgz
# foreground roi.mgz
check_call([f'freeview -v {brain_mgh} {roi_mgh}:colormap=lut:opacity=0.5'], shell=True)
