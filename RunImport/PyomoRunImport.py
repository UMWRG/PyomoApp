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

-- model              -m    Pyomo model  Pyomo model file (*.py), it needs to implement method called
                            file         run_model which take datafile as arguments and return
                                         2 lists contain results and model instances. Example is
                                         distributed with the plugin

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

Example:

-s 4 -t 4  -o "c:\\temp\\input.dat"  -m c:\\temp\\PyomoModel_2.py"

'''

import os
import sys

from HydraLib.HydraException import HydraPluginError


pythondir = os.path.dirname(os.path.realpath(__file__))
pyomolibpath=os.path.join(pythondir, '..', 'lib')
lib_path = os.path.realpath(os.path.abspath(pyomolibpath))
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from PyomoAppLib import commandline_parser
from PyomoAppLib import cocnvert_to_int
from PyomoAppLib import read_inputData
from PyomoExporter import Exporter
from PyomoImporter import Importer
from PyomoWrapper import runmodel
from HydraLib import PluginLib


def import_result(args, vars, objs, actual_time_steps):
    imp=Importer(vars, objs, actual_time_steps)
    imp.load_network(args.network, args.scenario)
    #imp.set_network(network)
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
    elif os.path.exists(os.path.dirname(args.output))==False:
            raise HydraPluginError('output file directory: '+ os.path.dirname(args.output)+', is not exist')
    elif os.path.isfile(args.output)==False:
        raise HydraPluginError('output file: '+args.output+', is not existed')

if __name__ == '__main__':
    try:
        parser = commandline_parser()
        args = parser.parse_args()
        check_args(args)
        netword_id=cocnvert_to_int(args.network, "Network Id")
        scenario_id=cocnvert_to_int(args.scenario, "scenario Id")
        vars, objs=runmodel(args.output, args.model_file)
        actual_time_steps=read_inputData(args.output)
        import_result(args, vars, objs, actual_time_steps)
        message="Run successfully"
        print PluginLib.create_xml_response('PyomoRumImporter', args.network, [args.scenario], message=message)
    except HydraPluginError, e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        err = PluginLib.create_xml_response('PyomoRumImporter', args.network, [args.scenario], errors = [e.message])
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
        err = PluginLib.create_xml_response('PyomoRumImporter', args.network, [args.scenario], errors = [e.message])
        print err


