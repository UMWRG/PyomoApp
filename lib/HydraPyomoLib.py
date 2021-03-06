#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright 2013, 2014, 2015 University of Manchester\
#\
# PyomoAppLib is free software: you can redistribute it and/or modify\
# it under the terms of the GNU General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# PyomoAppLib is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU General Public License for more details.\
# \
# You should have received a copy of the GNU General Public License\
# along with PyomoAppLib.  If not, see <http://www.gnu.org/licenses/>\
#

from HydraLib import PluginLib
from HydraLib.HydraException import HydraPluginError
__author__ = 'K. Mohamed'


import argparse as ap
import sys


def commandline_parser():
    parser = ap.ArgumentParser(
        description="""Export a network and a scenrio to a file, which can be imported into a Pyomo model.

Written by Khaled Mohamed <khaled.mohamed@manchester.ac.uk>
(c) Copyright 2015, Univeristy of Manchester.
        """, epilog="For more information visit www.hydraplatform.org",
        formatter_class=ap.RawDescriptionHelpFormatter)
    # Mandatory arguments
    #parser.add_argument('-p', '--project',
    #                    help='''ID of the project that will be exported.''')
    parser.add_argument('-t', '--network',
                        help='''ID of the network that will be exported.''')
    parser.add_argument('-s', '--scenario',
                        help='''ID of the scenario that will be exported.''')

    parser.add_argument('-tp', '--template-id',
                        help='''ID of the template to be used.''')

    parser.add_argument('-o', '--output',
                        help='''Filename of the output file.''')

    parser.add_argument('-m', '--model-file',
                        help='''Full path to the pyomo model (*.py) used for
                        the simulation.''')

    parser.add_argument('-tx', '--time-axis', nargs='+',
                        help='''Time axis for the modelling period (a list of
                        comma separated time stamps).''')

    parser.add_argument('-st', '--start-date',
                        help='''Start date of the time period used for
                        simulation.''')
    parser.add_argument('-en', '--end-date',
                        help='''End date of the time period used for
                        simulation.''')
    parser.add_argument('-dt', '--time-step',
                        help='''Time step used for simulation.''')
    parser.add_argument('-u', '--server_url',
                        help='''Specify the URL of the server to which this
                        plug-in connects.''')
    parser.add_argument('-c', '--session_id',
                        help='''Session ID. If this does not exist, a login will be
                        attempted based on details in config.''')
    return parser

def convert_to_int(value, type):
    '''
    convert value to integer
    it is used for both network id and scenario id
    '''
    try:
        value=int (value)
        return value
    except:
        message=[type+ " needs to be an integer, input is:  "+value]
        raise HydraPluginError('Time axis not specified.')

def get_link_name(link):
    '''
    get link name using its nodes names
    '''
    name='['+ link.from_node+','+link.to_node+']'
    return name

def get_link_name_for_param(link):
    '''
    get linke name to be used with parameter
    '''
    name= link.from_node+' '+link.to_node
    return name


def translate_attr_name(name):
    """
    Replace non alphanumeric characters with '_'. This function throws an
    error, if the first letter of an attribute name is not an alphabetic
    character.
    """
    if isinstance(name, str):
        translator = ''.join(chr(c) if chr(c).isalnum()
                             else '_' for c in range(256))
    elif isinstance(name, unicode):
        translator = UnicodeTranslate()
    name = name.translate(translator)
    return name

def read_inputData(datafile):
     '''
     read actual time steps from data file
     '''
     data = open(datafile, "r")
     actual_time_steps=[]
     for line in data:
         if(line.startswith('set actual_time_step:=')):
             line_=line.replace('set actual_time_step:=','')
             line_=line_.replace(';','')
             line_=line_.strip()
             time_steps=line_.split(" ")
             counter=1
             ste=''
             for step in time_steps:
                 if(counter==1):
                     ste=step
                     counter+=1
                 else:
                     ste=ste+" "+step
                     actual_time_steps.append(ste)
                     counter=1
     data.close()
     return actual_time_steps



class UnicodeTranslate(dict):
    """
    Translate a unicode attribute name to a valid variable.
    """
    def __missing__(self, item):
        char = unichr(item)
        repl = u'_'
        if item < 256 and char.isalnum():
            repl = char
        self[item] = repl
        return repl

def export_arrays(self, resources):
        """Export arrays.
        """
        attributes = []
        attr_names = []
        attr_outputs = []
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == 'array' and attr.is_var is False:
                    attr.name = translate_attr_name(attr.name)
                    if attr.name not in attr_names:
                        attributes.append(attr)
                        attr_names.append(attr.name)
        if len(attributes) > 0:
            # We have to write the complete array information for every single
            # node, because they might have different sizes.
            for resource in resources:
                # This exporter only supports 'rectangular' arrays
                for attribute in attributes:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is not None and attr.value is not None:
                        array_dict = attr.value['arr_data'][0]
                        array = parse_array(array_dict)
                        dim = array_dim(array)
                        attr_outputs.append('* Array %s for node %s, ' % \
                            (attr.name, resource.name))
                        attr_outputs.append('dimensions are %s\n\n' % dim)
                        # Generate array indices
                        attr_outputs.append('SETS\n\n')
                        indexvars = list(ascii_lowercase)
                        for i, n in enumerate(dim):
                            attr_outputs.append(indexvars[i] + '_' + \
                                resource.name + '_' + attr.name + \
                                ' array index /\n')
                            for idx in range(n):
                                attr_outputs.append(str(idx) + '\n')
                            attr_outputs.append('/\n\n')

                        attr_outputs.append('Table ' + resource.name + '_' + \
                            attr.name + '(')
                        for i, n in enumerate(dim):
                            attr_outputs.append(indexvars[i] + '_' + resource.name \
                                + '_' + attr.name)
                            if i < (len(dim) - 1):
                                attr_outputs.append(',')
                        attr_outputs.append(') \n\n')
                        ydim = dim[-1]
                        #attr_outputs.append(' '.join(['{0:10}'.format(y)
                        #                        for y in range(ydim)])
                        for y in range(ydim):
                            attr_outputs.append('{0:20}'.format(y))
                        attr_outputs.append('\n')
                        arr_index = create_arr_index(dim[0:-1])
                        matr_array = arr_to_matrix(array, dim)
                        for i, idx in enumerate(arr_index):
                            for n in range(ydim):
                                attr_outputs.append('{0:<10}'.format(
                                    ' . '.join([str(k) for k in idx])))
                                attr_outputs.append('{0:10}'.format(matr_array[i][n]))
                            attr_outputs.append('\n')
                        attr_outputs.append('\n\n')
        return attr_outputs

class ModelVarable:
    '''
    class to hold varaible data
    '''
    def __init__(self, name, owner, desc, unit, data_set=None, data_type=None):
        self.name=name
        self.dec=desc
        self.owner=owner
        self.unit=unit
        if(data_set!=None):
            self.data_set=data_set
        else:
            self.data_set=[]
        self.data_type=data_type

    def add_data(self, data):
        self.data_set.append(data)

def arr_to_matrix(arr, dim):
    """
    Reshape a multidimensional array to a 2 dimensional matrix.
    """
    tmp_arr = []
    for n in range(len(dim) - 2):
        for inner in arr:
            for i in inner:
                tmp_arr.append(i)
        arr = tmp_arr
        tmp_arr = []
    return arr
