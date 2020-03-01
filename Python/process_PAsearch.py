#!/usr/bin/python
# -*- coding: utf-8 -*-
# Processes the Raw data of a sample
# Following directory tree of the Particle Search:
#
#
# <sample_id>
#     |
#     |_____/cropped/
#     |_____/Reference Markers/
#     |_____/spc/
#     |_____/Stub Summary.txt
#     |_____/<stubinfo csv-File>
#

import pandas as pd
import numpy as np
from io import BytesIO
from skimage import io, transform
import os
import warnings


def get_header_data(dir_stub):
    """fetch the header info from 'Stub Summary.txt' """

    filename = os.path.join(dir_stub, 'Stub Summary.txt')

    # open the stub invo .csv file
    with open(filename, 'r') as f:
        file_inputdata = f.read()

    # extract the header-info from inp_data (first 14 lines)
    inp_header = file_inputdata.splitlines()

    dict_header = {}
    # Loop through the lines
    for line in inp_header:
        split_line = str.split(line, ':', maxsplit=1)
        if len(split_line) > 1:
            qualifier = split_line[0].strip()
            data = split_line[1].strip()
            dict_header[qualifier] = data
    return dict_header


def get_stubinfo(file_stub):
    """read the stub info file store PA search info in pandas Dataframe"""

    # open the stub invo .csv file
    with open(file_stub, 'r') as f:
        file_inputdata = f.read()

    # extract the PA data
    # gets the data from the .csv file generated from EDAX PA searc
    #
    # for python 3 the io needs to be handled correctly
    #
    # The csv files has \r newlines, which np.genfromtxt cannot handle (bug ?)
    #
    # The stream is opened in universal newl mode, converts the newlines to \n
    # inp_data is rewritten into a in memory bytestream for np.genfromtxt
    # comments is set to "//" to overide the default value "#"
    import_stub = np.genfromtxt(
        BytesIO(file_inputdata.encode()),
        delimiter=",", skip_header=14,
        names=True, autostrip=True, comments='//'
    )

    return pd.DataFrame(import_stub)


def import_IJfile(file, pixelsize=0.23142628587258555):
    """read the imageJ PA search csv file and store in dataframe"""
    import re

    with open(file, 'r') as f:
        inp_data = f.read()

    df = pd.read_csv(BytesIO(inp_data.encode()), sep=',')
    df.rename(columns={'Label': 'Field',
                       ' ': 'Part',
                       'X': 'X_cent',
                       'Y': 'Y_cent',
                       'Circ.': 'Circ'}, inplace=True)

    def stripper(x): return re.sub("[^0-9^.]", "", str(x))
    df.Field = pd.to_numeric(df.Field.apply(stripper))
    df['AvgDiam'] = df.loc(axis=1)['Major', 'Minor'].mean(1) * pixelsize

    return df


def get_ImageJPAsearchinfo(file_ImageJPAsearch):
    """read the ImageJ PA search file and store in pandas DataFrame"""

    with open(file_ImageJPAsearch, 'r') as f:
        inp_data = f.read()

    # extract the PA data
    import_ImageJPAsearch = np.genfromtxt(BytesIO(inp_data.encode()),
                                          delimiter=",", skip_header=0,
                                          names=True, autostrip=True,
                                          comments='#')

    return pd.DataFrame(import_ImageJPAsearch)


def get_markerpos(stub_dir):
    """load the marker positions from the file 'marker_pos.txt'"""

    from os.path import join

    file = join(stub_dir, 'refmarkers/marker_pos.txt')

    with open(file, 'r') as f:
        inp_data = f.read()

    marker_import = np.genfromtxt(BytesIO(inp_data.encode()), dtype=None,
                                  delimiter=",", skip_header=4, names=True,
                                  autostrip=True, comments='#', encoding=None)

    # Create a dictionary

    markers = {str(marker[0]):
               (marker[1], marker[2]) for marker in marker_import}

    return markers


def crop_img(image, center_x, center_y, size_x, size_y, edax_pasearch=True):
    """crops an image given the center and the width and height"""

    # The coordinates from the stub info has (0,0) in the bottom left
    # whereas skimage uses top left as origin
    # transformation using size of img
    imgsize_x = image.shape[1]
    imgsize_y = image.shape[0]

    if (edax_pasearch):
        center_y = imgsize_y - center_y

    y_down = center_y - int(np.abs(size_y/2))
    y_up = center_y + int(np.abs(size_y/2))
    x_down = center_x - int(np.abs(size_x/2))
    x_up = center_x + int(np.abs(size_x/2))

    # the window to be cropped should be within bounds of the image
    if x_down < 0:           # shift to positive x
        shift = np.abs(x_down)
        x_down += shift
        x_up += shift

    elif x_up > imgsize_x:   # shift to negative x
        shift = x_up - imgsize_x
        x_down -= shift
        x_up -= shift

    if y_down < 0:             # shift to positive y
        shift = np.abs(y_down)
        y_down += shift
        y_up += shift

    elif y_up > imgsize_y:     # shift to negative y
        shift = y_up - imgsize_y
        y_down -= shift
        y_up -= shift

    rescaled_cropped_img = transform.rescale(
        image[y_down:y_up, x_down:x_up],
        3,
        order=0
    )
    # exposure.rescale_intensity(cropped_img, out_range='uint8')

    # return the cropped image and resclaed image
    return rescaled_cropped_img


def process_fields(df_field, directory, ext, edax_pasearch=True):
    """ Process fields and create cropped images

        df_field:   Pandas Dataframe object containing the field info

        directory:  path object for the sample directory

        ext:        String containing the extension
    """

    # if cropped files are present, ask if user really wants to reprocess

    # Create list of images to be loaded and cropped from stub data
    fields = df_field.Field
    img_list = [directory + '/fields/' +
                'fld' + '{:0>4d}'.format(int(field_no)) +
                ext for field_no in fields]
    coll = io.ImageCollection(img_list, conserve_memory=False)

    # Loop over fields
    for field_no, field in enumerate(fields):
        # fetch the image from the ic
        img = coll[field_no]

        # fetch the index of particles on the field
        particles = df_field[df_field.loc[:, 'Field'] == field].Part.values

        # Loop over particles
        for particle_no, particle in enumerate(particles):
            x_c, y_c = df_field.loc[df_field.loc[:, 'Part'] == particle,
                                    ['X_cent', 'Y_cent']].values.flatten()
            if (edax_pasearch):
                x_size, y_size = df_field.loc[
                    df_field.loc[:, 'Part'] ==
                    particle, ['X_width', 'Y_height']].values.flatten()
            else:
                x_size, y_size = 32, 25

            # crop image from collection
            cropped_img = crop_img(img, int(x_c), int(y_c),
                                   int(x_size), int(y_size),
                                   edax_pasearch)

            # save in '/cropped/part0000.png'
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                io.imsave(directory +
                          '/cropped/' +
                          '{:0>4d}'.format(int(field)) +
                          '{:0>4d}'.format(int(particle_no) + 1) +
                          ext, cropped_img
                          )


def walk_stubdir(path):
    """Walks the stub directory and extracts the locations."""

    """
    Keyword arguments:
    path -- the path searched for stub PA data


    returns dictionary with PA data locations as a list
    """

    # find the pa search directory
    # stub_dir  - stub directories
    # stub_info - .csv info files
    stub_dir = []
    EDAX_PAsearch = []
    IJ_PAsearch = []
    extension = []

    for root, dirs, files in os.walk(path):
        if 'Stub Summary.txt' in files:
            # Found directory with Stub Summary
            stub_dir.append(root)

            # Check is subdirectory 'cropped' exists, unless create
            if 'cropped' not in dirs:
                os.makedirs(os.path.join(root, 'cropped'))

            # Look for the .csv files containing the stub info
            for file in files:
                if file.endswith('stub01.csv'):
                    EDAX_PAsearch.append(os.path.join(root, file))
                if (file.endswith('.csv') & file.startswith('IJ')):
                    IJ_PAsearch.append(os.path.join(root, file))

    # file extension
    extension = '.png'

    datalocation = dict([('stub_dir', stub_dir),
                         ('EDAX_PAsearch', EDAX_PAsearch),
                         ('IJ_PAsearch', IJ_PAsearch),
                         ('extension', extension)])

    return datalocation


def match_EDAX_IJ_PAsearch(df_EDAX, df_IJ, match_dist=0.005,
                           size_x=2048, size_y=1600,
                           pixelsize=0.23142628587258555):

    if 'X_stage' in df_IJ.columns:
        return
    # pandas merge dataframes from ImageJ and edx PA search on Field
    df_IJ = pd.merge(
        df_EDAX[['Field', 'X_stage', 'Y_stage']].drop_duplicates(),
        df_IJ, left_on='Field', right_on='Field')

    df_IJ['StgX'] = (df_IJ['X_stage'] / 1000
                     + pixelsize / 1000
                     * (df_IJ['X_cent'] - size_x / 2))

    df_IJ['StgY'] = (df_IJ['Y_stage'] / 1000
                     + pixelsize / 1000
                     * (size_y - df_IJ['Y_cent'] - size_y / 2 - 160))

    matches = []
    for field in np.unique(df_EDAX.Field.values):
        edx_particles = df_EDAX[df_EDAX.Field == field].Part
        edx_data = df_EDAX[df_EDAX.Field == field]
        IJ_data = df_IJ[df_IJ.Field == field]
        for edx_particle in edx_particles:
            pos_edx = np.array(edx_data[edx_data.Part == edx_particle].StgX,
                               edx_data[edx_data.Part == edx_particle].StgY)

            # Loop to find a match in the IJ PA search
            for IJ_particle in IJ_data.Part:
                pos_IJ = np.array(IJ_data[IJ_data.Part == IJ_particle].StgX,
                                  IJ_data[IJ_data.Part == IJ_particle].StgY)
                dist = np.linalg.norm(pos_edx - pos_IJ)
                # The match condition is a distance of less than 5 µm
                if (dist < match_dist):
                    matches.append([edx_particle, IJ_particle])

    df_match = pd.DataFrame(matches, columns=['Part_edx', 'Part_IJ'])

    # create a df to align EDAX data using the matching particles
    drop_columns = ['Part_edx', 'Part', 'Field', 'X_cent', 'Y_cent',
                    'X_stage', 'Y_stage', 'AvgDiam', 'Area', 'Perim']
    new = pd.merge(df_EDAX, df_match, left_on='Part', right_on='Part_edx',
                   how='left').drop(drop_columns, axis=1)

    # align with the ImageJPAsearch file
    df_IJ = pd.merge(df_IJ, new, left_on='Part', right_on='Part_IJ',
                     copy='False', how='left')

    return df_IJ.rename(
        columns={'StgX_y': 'StgX',
                 'StgY_y': 'StgY'}).drop_duplicates(subset='Part')


if __name__ == "__main__":
    root_dir = os.getcwd()

    # Directory containing the stub data
    directory = 'DemoData/'

    # Create the full path
    wdir = os.path.join(root_dir, directory)

    # Retrieve the PA data locations
    if os.path.exists(wdir):
        data_loc = walk_stubdir(wdir)
    else:
        print('PA directory not found')

    # Retrieve the EDAX PA search info
    df = get_stubinfo(data_loc['EDAX_PAsearch'][0])

    # Process the images
    process_fields(df, data_loc['stub_dir'][0], data_loc['extension'][0])
