#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright 2013, 2014, 2015 University of Manchester\
#\
# PyomoWrapper is free software: you can redistribute it and/or modify\
# it under the terms of the GNU General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# PyomoWrapper is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU General Public License for more details.\
# \
# You should have received a copy of the GNU General Public License\
# along with PyomoWrapper.  If not, see <http://www.gnu.org/licenses/>\
#
__author__ = 'K. Mohamed'


from pyomo.environ import *
from pyomo.opt import SolverStatus, TerminationCondition

from HydraPyomoLib import ModelVarable
import os
import sys
import importlib
import pyutilib.component.core
from HydraLib.HydraException import HydraPluginError

import logging
log = logging.getLogger(__name__)

def get_values(instance, var_, list_, units):
    '''
    get variable value from model instance
    '''
    owner=[]
    x_var = getattr(instance, str(var_))
    for xx in x_var:
        value_=x_var[xx].value
        owner=[]
        try:
            if type(xx) is str:
                owner.append(xx)
            else:
                for mem in xx:
                    owner.append(mem)
            varmodel=None
            for varmodel_ in list_:
                if varmodel_.name==str(var_) and varmodel_.owner==owner:
                    varmodel=varmodel_
                    break
            if(varmodel==None):
                desc="Imported using Pyomo apps"
                if str(var_) in units.keys():
                    unit=units[str(var_)]
                else:
                    unit=None
                varmodel=ModelVarable(str(var_), owner, desc, unit)
                list_.append(varmodel)
            varmodel.add_data(value_)
        except:
            pass
    return list_

def run_model(filename, modelfile):
    '''
    Run the model file
    '''
    #Convert truncated file names, containing a "~1" into the full path
    if os.name == 'nt':
        import win32file
        modelfile = win32file.GetLongPathName(modelfile)
        
    mname=os.path.dirname(modelfile)
    sys.path.append(mname)
    log.info("Importing the model from %s ", modelfile)
    mm=importlib.import_module(os.path.basename(modelfile).split('.')[0])
    log.info("Importing the model %s", os.path.basename(modelfile).split('.')[0])
    run_model=getattr(mm, 'run_model')
    log.info("Model is imported.")
    res, instances=run_model(filename)
    for rs in res:
        #check solver status and termination conditions
        # and raise an error due to the termination and status code
        if(rs.solver.status == SolverStatus.unknown):
            raise HydraPluginError('Unknow error,(an uninitialized value)')
        elif (rs.solver.status != SolverStatus.warning):
            log.info("Solver status warnning")
        elif(rs.solver.status == SolverStatus.aborted):
            raise HydraPluginError('Terminated due to external conditions (e.g. interrupts)')
        elif(rs.solver.status == SolverStatus.error):
            raise HydraPluginError('Terminated internally with error')
        if rs.solver.termination_condition==TerminationCondition.unknown:
            raise HydraPluginError('solver termination with unknow error, this may indicate that the problem is infeasible')
        elif rs.solver.termination_condition==TerminationCondition.maxTimeLimit:
            raise HydraPluginError('Exceeded maximum time limit allowed ')
        elif rs.solver.termination_condition==TerminationCondition.maxIterations:
            raise HydraPluginError('Exceeded maximum number of iterations allowed ')
        elif rs.solver.termination_condition==TerminationCondition.minFunctionValue:
            raise HydraPluginError('Found solution smaller than specified function value')
        elif rs.solver.termination_condition==TerminationCondition.minStepLength:
            raise HydraPluginError('Step length is smaller than specified limit')
        elif rs.solver.termination_condition==TerminationCondition.maxEvaluations:
            raise HydraPluginError('Exceeded maximum number of problem evaluations (e.g., branch and bound nodes')
        elif rs.solver.termination_condition==TerminationCondition.other:
            raise HydraPluginError(' uncategorized normal termination')
        elif rs.solver.termination_condition==TerminationCondition.unbounded:
            raise HydraPluginError('Demonstrated that problem is unbounded')
        elif rs.solver.termination_condition==TerminationCondition.infeasible:
            raise HydraPluginError('Demonstrated that problem is infeasible')
        elif rs.solver.termination_condition==TerminationCondition.invalidProblem:
            raise HydraPluginError('The problem setup or characteristics are not valid for the solver')
        elif rs.solver.termination_condition==TerminationCondition.solverFailure:
            raise HydraPluginError('Solver failed to terminate correctly')
        elif rs.solver.termination_condition==TerminationCondition.internalSolverError:
            raise HydraPluginError('Internal solver error')
        elif rs.solver.termination_condition==TerminationCondition.error:
            raise HydraPluginError('Other error')
        elif rs.solver.termination_condition==TerminationCondition.userInterrupt:
            raise HydraPluginError('Interrupt signal generated by user')
        elif rs.solver.termination_condition==TerminationCondition.resourceInterrupt:
            raise HydraPluginError('Interrupt signal in resources used by the solver')
        #elif rs.solver.termination_condition==TerminationCondition.licensingProblem:
            #raise HydraPluginError('Problem accessing solver license')

    log.info("Model is running.")
    units=get_units(modelfile)
    return analyse_results (res, instances, units)

def get_units(modelfile):
    '''
    get variables units from model file
    '''
    units={}
    contents = open(modelfile, "r")
    for line in contents:
        line=line.strip()
        if line.startswith('model.')& (line.__contains__('Var') or line.__contains__('Objective')):
            lin = line.split("=")
            name=lin[0].replace('model.','')
            if line.__contains__('#*'):
                unit=line.split('#*')[1]
                units[name.strip()]=unit.strip()
    contents.close()
    return units

def analyse_results (res, instances, units):
    '''
    analyis the results to get variables values
    '''
    vars={}
    objs={}
    time_step=1
    for instance in instances:
        rs=res[time_step-1]
        for var_ in instance.component_objects(Var):
        #for var_ in instance.active_components(Var):
            if str(var_) in vars.keys():
                 list_=vars[str(var_)]
            else:
                list_=[]
            vars[str(var_)]=get_values(instance, var_, list_, units)


        for obj in instance.component_objects(Objective):
            if str(obj) in objs.keys():
                 list_=objs[str(obj)]
            else:
                list_=[]
            objs[str(obj)]=get_obj_value(rs, obj, list_, units)

        time_step+=1

    return vars, objs

def get_obj_value(result, obj, list_, units):
    '''
    get objectives values from the result
    '''
    value_= float(result.Solver[0]['Termination message'].split("=")[1])
     #value_=result.solution[0].objective[1].Value
    #zvalue_=result.objective[1].Value
    varmodel=None
    for varmodel_ in list_:
        if varmodel_.name==str(obj) and varmodel_.owner=='Network':
            varmodel=varmodel_
            break
    if(varmodel==None):
        desc="Imported using Pyomo apps"
        if str(obj) in units.keys():
            unit=units[str(obj)]
        else:
            unit=None
        varmodel=ModelVarable(str(obj), 'Network', desc, unit)
        list_.append(varmodel)
    varmodel.add_data(value_)
    return list_