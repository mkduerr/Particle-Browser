# See README.md for more information on the usage
# stub01.csv -- stub-Info
# marker_pos.txt -- marker positions in mm
# Files to load
#
# ./thumbnails -- image thumbnails
# ./spc -- EDX data


import numpy as np
import pandas as pd
from os.path import join
from os import getcwd
from jinja2 import Template
import time

from bokeh.embed import file_html, components
from bokeh.resources import JSResources, CSSResources, INLINE

# import custom module for PA search
import process_PAsearch
import create_bokehplot


def create_imagelist(pd_dataframe, img_dir, ext):
    """
    Creates a list of image paths of the thumbnails

    Keyword arguments:
    pd_dataframe -- pandas DataFrame object containing the stub info

    stub_directory -- location of stub info files

    ext -- File extension of the thumbnail

    """
    imgs = []    # list of image paths

    fields = pd_dataframe.Field.unique()
    # Loop over fields
    for field_no, field in enumerate(fields):
        # fetch the index of particles on the field
        particles = pd_dataframe[
            pd_dataframe.loc[:, 'Field'] == field
        ].Part.values

        # Loop over particles
        for particle_no, particle in enumerate(particles):
            imgs.append('thumbnails/'
                        + '{:0>4d}'.format(int(field))
                        + '{:0>4d}'.format(int(particle_no)+1)
                        + ext)

    return imgs


root_dir = getcwd()

# Directory containing the stub data
directory = 'DemoData'

# Create the full path
wdir = join(root_dir, directory)
print(wdir)

# use function 'walk_stubdir' to extract the info
stub_loc = process_PAsearch.walk_stubdir(wdir)

#    --> only continue when one directory was found
if len(stub_loc['stub_dir']) > 1:
    print('More than one PA search found')

# Import the stub summary info
stub_summary = process_PAsearch.get_header_data(stub_loc['stub_dir'][0])

# Import the stub data
df_EDAX = process_PAsearch.get_stubinfo(stub_loc['EDAX_PAsearch'][0])

# Import IJ PA search data
df_IJ = process_PAsearch.import_IJfile(stub_loc['IJ_PAsearch'][0])

# Join the PA search data
df = process_PAsearch.match_EDAX_IJ_PAsearch(
    df_EDAX,
    df_IJ,
    match_dist=0.005)

# randomize the particle position to give a homogeneous distribution
# power distribution for the radius, unifomr for the azimuthal angle

radius = 12.2 * np.random.power(2, df_EDAX.size)
phi = 2*np.pi*np.random.random_sample(df_EDAX.size)

# Replace the positions
df_EDAX.StgX = pd.DataFrame(radius * np.cos(phi))
df_EDAX.StgY = pd.DataFrame(radius * np.sin(phi))

# ------------- Sample info -------------------------
sample_info = {
    'SAMPLE_ID': 'Particle Substrate No. 1',
    'CRM': 'NBL-129A',
    'REMARKS': 'Particles prepared from suspension',
    'UAMOUNT': 'xx',  # in pg
    # SEM Particle Search Parameters
    'MAGNIFICATION': stub_summary['Mag'],
    'VOLTAGE': stub_summary['Acc. Voltage'],
    'PARTICLES_COUNTED': stub_summary['Particles Counted'],
    'PARTICLES_ANALYZED': stub_summary['Particles Analyzed'],
    'DATE': time.strftime('%B %d, %Y')
}


# ------------- Preparations for bokeh plots --------

# Generate the list of filepaths for thumbnail view for hover tooltip

img_list = create_imagelist(df_EDAX, wdir, '.png')

# Import the markers from the file

import_marker = process_PAsearch.get_markerpos(stub_loc['stub_dir'][0])

df_MRK = pd.DataFrame.from_dict(import_marker, orient='index')
df_MRK.columns = ['StgX', 'StgY']  # add the column names

# ------------ Create the plots --------------
# Open our custom template
with open('PB_template.jinja', 'r') as f:
    template = Template(f.read())

# Use inline resources, render the html and open
bokehlayout = create_bokehplot.makelayout(df_EDAX, df_MRK, img_list)
title = 'Particle Search Results'
js_resources = JSResources(mode='cdn')
css_resources = CSSResources(mode='cdn')
html = file_html(bokehlayout,
                 resources=(js_resources, css_resources),
                 title=title, template=template,
                 template_variables=sample_info)

script, div = components(bokehlayout)

"""html = template.render(js_resources=js_resources,
                       css_resources=css_resources,
                       div=div)"""

output_file = directory + '.html'

with open(directory + '/' + output_file, mode='w', encoding='utf-8') as f:
    f.write(html)
