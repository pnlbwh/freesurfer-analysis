delimiter_dict = {'comma': ',',
                  'tab': '\t',
                  'semicolon': ';',
                  'space': ' '}

from glob import glob
from os.path import join as pjoin, isdir

def _glob(dir):

    items= glob(pjoin(dir, '*'))
    filtered= []
    for item in items:
        if isdir(item) or sum([item.endswith(ext) for ext in ['.csv','.tsv','.txt']]):
            filtered.append(item)

    return filtered
    
