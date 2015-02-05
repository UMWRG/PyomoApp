#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright 2013, 2014, 2015 University of Manchester\
#\
# PyomoAutoRun is free software: you can redistribute it and/or modify\
# it under the terms of the GNU General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# PyomoAutoRun is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU General Public License for more details.\
# \
# You should have received a copy of the GNU General Public License\
# along with PyomoAutoRun.  If not, see <http://www.gnu.org/licenses/>\
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

-- model              -m    Pyomo model  Pyomo model file (*.py), needs to have a method called
                            file         run_model which takes the datafile as an argument and return
                                         2 lists containing results and model instances. Example is
                                         provided with the plugin

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

Specifying the time axis
~~~~~~~~~~~~~~~~~~~~~~~~

One of the following two options for specifying the time domain of the model is
mandatory:

**Option 1:**

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ======= ========== ======================================
--start-date            -st   START_DATE  Start date of the time period used for
                                          simulation.
--end-date              -en   END_DATE    End date of the time period used for
                                          simulation.
--time-step             -dt   TIME_STEP   Time step used for simulation. The
                                          time step needs to be specified as a
                                          valid time length as supported by
                                          Hydra's unit conversion function (e.g.
                                          1 s, 3 min, 2 h, 4 day, 1 mon, 1 yr)
====================== ======= ========== ======================================

**Option 2:**

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ======= ========== ======================================
--time-axis             -tx    TIME_AXIS  Time axis for the modelling period (a
                                          list of comma separated time stamps).
====================== ======= ========== ======================================

Examples:

-s 4 -t 4  -tx 2000-01-01, 2000-02-01, 2000-03-01, 2000-04-01, 2000-05-01, 2000-06-01  -m c:\\temp\\PyomoModel_2.py"
-o "c:\\temp\\input.dat"

-s 2 -t 2  -tx 2000-01-01, 2000-02-01, 2000-03-01, 2000-04-01, 2000-05-01, 2000-06-01  , 2000-07-01 , 2000-08-01 , 2000-09-01
-m c:\\temp\\model\\PyomoModel_3.py"
'''

import os
import sys

from HydraLib.HydraException import HydraPluginError


pythondir = os.path.dirname(os.path.realpath(__file__))
pyomolibpath=os.path.join(pythondir, '..', 'lib')
lib_path = os.path.realpath(os.path.abspath(pyomolibpath))
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

import argparse as ap
from PyomoAppLib import convert_to_int
from PyomoAppLib import read_inputData
from PyomoExporter import Exporter
from PyomoImporter import Importer
from PyomoWrapper import run_model
from HydraLib import PluginLib
from HydraLib.PluginLib import write_progress

steps=8

import logging
log = logging.getLogger(__name__)

def export_data(args):
    template_id = None
    if args.template_id is not None:
            template_id = int(args.template_id)
    write_progress(1, steps)
    exporter=Exporter(args.output, args.server_url, args.session_id)
    if args.start_date is not None and args.end_date is not None \
                and args.time_step is not None:
        exporter.write_time_index(start_time=args.start_date,
                                      end_time=args.end_date,
                                      time_step=args.time_step)
    elif args.time_axis is not None:
        exporter.write_time_index(time_axis=args.time_axis)
    else:
        raise HydraPluginError('Time axis not specified.')

    write_progress(2, steps)
    exporter.export_network(netword_id,  scenario_id, template_id)
    write_progress(3, steps)
    exporter.save_file()
    return exporter.net

def import_result(args, vars, objs, actual_time_steps):
    write_progress(4, steps)
    imp=Importer(vars, objs, actual_time_steps, args.server_url, args.session_id)
    write_progress(5, steps)
    imp.load_network(args.network, args.scenario)
    write_progress(6, steps)
    #imp.set_network(network)
    imp.import_res()
    write_progress(7, steps)
    imp.save()


def commandline_parser_auto():
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

    parser.add_argument('-m', '--model-file',
                        help='''Full path to the pyomo model (*.py) used for
                        the simulation.''')
    parser.add_argument('-o', '--output',
                        help='''Filename of the output file.''')

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
        #if output file is not provided, plug in use default one
        modelpath=os.path.dirname(args.model_file)
        args.output=os.path.join(modelpath,'input.dat')
        if args.output is None:
            raise HydraPluginError('No output file specified')
    elif os.path.exists(os.path.dirname(args.output))==False:
            raise HydraPluginError('output file directory: '+ os.path.dirname(args.output)+', is not exist')


if __name__ == '__main__':
    parser = commandline_parser_auto()
    args = parser.parse_args()
    try:

        check_args(args)
        netword_id=convert_to_int(args.network, "Network Id")
        scenario_id=convert_to_int(args.scenario, "scenario Id")
        network=export_data(args)
        vars, objs=run_model(args.output, args.model_file)
        actual_time_steps=read_inputData(args.output)
        import_result(args, vars, objs, actual_time_steps)
        write_progress(8, steps)
        message="Run successfully"
        print PluginLib.create_xml_response('PyomoAuto', args.network, [args.scenario], message=message)

    except HydraPluginError, e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        err = PluginLib.create_xml_response('PyomoAuto', args.network, [args.scenario], errors = [e.message])
        print err
    except Exception as e:
        errors = []
        if e.message == '':
            if hasattr(e, 'strerror'):
                errors = [e.strerror]
        else:
            errors = [e.message]

        import traceback
        traceback.print_exc(file=sys.stderr)
        err = PluginLib.create_xml_response('PyomoAuto', args.network, [args.scenario], errors = [e.message])
        print err

