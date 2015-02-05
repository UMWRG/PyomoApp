#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright 2013, 2014, 2015 University of Manchester\
#\
# PyomoRunImport is free software: you can redistribute it and/or modify\
# it under the terms of the GNU General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# PyomoRunImport is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU General Public License for more details.\
# \
# You should have received a copy of the GNU General Public License\
# along with PyomoRunImport.  If not, see <http://www.gnu.org/licenses/>\
#
__author__ = 'K. Mohamed'
'''
    plugin_name: PyomoApp
  - Export a network from Hydra to a Pyomo input text file.
  - Run Pyomo model
  - Extrtact the parameters from resuly
  - Import the parameters to Hydra

mandatory_args
==============


====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--network              -t     NETWORK    ID of the network where results will
                                         be imported to. Ideally this coincides
                                         with the network exported to Pyomo.
--scenario            -s     SCENARIO    ID of the underlying scenario used for
                                          simulation
--template-id         -tp    TEMPLATE    ID of the template used for exporting
                                         resources. Attributes that don't
                                         belong to this template are ignored.
--output              -o    OUTPUT       Filename of the output file.

-- model              -m    Pyomo model  Pyomo model file (*.py), needs to implement a method called
                            file         run_model which takes a datafile as an argument and returns
                                         2 lists containing results and model instances. Example is
                                         distributed with the plugin

Server-based arguments
======================

====================== ====== ========== =========================================
Option                 Short  Parameter  Description
====================== ====== ========== =========================================
``--server_url``       ``-u`` SERVER_URL   Url of the server the plugin will 
                                           connect to.
                                           Defaults to localhost.
``--session_id``       ``-c`` SESSION_ID   Session ID used by the calling software
                                           If left empty, the plugin will attempt 
                                           to log in itself.
                                         
Example:

-s 4 -t 4  -o "c:\\temp\\input.dat"  -m c:\\temp\\PyomoModel_2.py"

-s 2 -t 2  -o "c:\\temp\\model\\input.dat"  -m c:\\temp\\PyomoModel_3.py"

'''

import os
import sys

from HydraLib.HydraException import HydraPluginError


pythondir = os.path.dirname(os.path.realpath(__file__))
pyomolibpath=os.path.join(pythondir, '..', 'lib')
lib_path = os.path.realpath(os.path.abspath(pyomolibpath))
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from PyomoAppLib import commandline_parser_run_import
from PyomoAppLib import convert_to_int
from PyomoAppLib import read_inputData
from PyomoExporter import Exporter
from PyomoImporter import Importer
from PyomoWrapper import runmodel
from HydraLib import PluginLib
from HydraLib.PluginLib import write_progress

import logging
log = logging.getLogger(__name__)

def import_result(args, vars, objs, actual_time_steps, url, session_id):
    imp=Importer(vars, objs, actual_time_steps, url, session_id)
    imp.load_network(args.network, args.scenario)
    imp.import_res()
    imp.save()

def check_args(args):
    try:
        int(args.network)
    except (TypeError, ValueError):
        raise HydraPluginError('No network is specified')
    try:
        int(args.scenario)
    except (TypeError, ValueError):
        raise HydraPluginError('No senario is specified')

    if args.model_file is None:
        raise HydraPluginError('model file is not specifed')
    elif os.path.isfile(args.model_file)==False:
        raise HydraPluginError('model file: '+args.model_file+', is not existed')
    elif args.output==None:
        raise HydraPluginError('No output file specified')
    elif os.path.exists(os.path.abspath(args.output))==False:
        raise HydraPluginError('output file directory '+ os.path.dirname(args.output)+' does not exist')
    elif os.path.isfile(args.output)==False:
        raise HydraPluginError('output file '+args.output+' does not exist')

if __name__ == '__main__':
    try:
        parser = commandline_parser_run_import()
        args = parser.parse_args()
        check_args(args)
        netword_id  = convert_to_int(args.network, "Network Id")
        scenario_id = convert_to_int(args.scenario, "scenario Id")
        vars, objs  = runmodel(args.output, args.model_file)
        actual_time_steps = read_inputData(args.output)
        import_result(args, vars, objs, actual_time_steps, url=args.server_url, session_id=args.session_id)
        message="Run successfully"
        print PluginLib.create_xml_response('PyomoRumImporter', args.network, [args.scenario], message=message)
    except HydraPluginError, e:
        log.exception(e)
        err = PluginLib.create_xml_response('PyomoRumImporter', args.network, [args.scenario], errors = [e.message])
        print err
    except Exception as e:
        log.exception(e)
        errors = []
        if e.message == '':
            if hasattr(e, 'strerror'):
                errors = [e.strerror]
        else:
            errors = [e.message]
        err = PluginLib.create_xml_response('PyomoRumImporter', args.network, [args.scenario], errors = [e.message])
        print err


