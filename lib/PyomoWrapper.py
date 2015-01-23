__author__ = 'K. Mohamed'

#from PyomoModel_2 import PyMode as model
from coopr.pyomo import *
import coopr.environ
from PyomoAppLib import ModelVarable
import os
import sys
import importlib
import pyutilib.component.core

def get_values(instance, var_, list_, units):
    owner=[]
    x_var = getattr(instance, var_)
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
                if varmodel_.name==var_ and varmodel_.owner==owner:
                    varmodel=varmodel_
                    break
            if(varmodel==None):
                desc="Imported using Pyomo apps"
                if var_ in units.keys():
                    unit=units[var_]
                else:
                    unit="unit_less"
                varmodel=ModelVarable(var_, owner, desc, unit)
                list_.append(varmodel)
            varmodel.add_data(value_)
        except:
            pass
    return list_

def runmodel(filename, modelfile):
    mname=os.path.dirname(modelfile)
    sys.path.append(mname)
    print "Importing the mode...1"
    mm=importlib.import_module(os.path.basename(modelfile).split('.')[0])
    print "Importing the mode...2"
    run_model=getattr(mm, 'run_model')
    print "Mode is imported .."
    res, instances=run_model(filename)
    print "model is running "
    units=get_units(modelfile)
    return analyse_results (res, instances, units)

def get_units(modelfile):
    units={}
    contents = open(modelfile, "r")
    for line in contents:
        if line.startswith('model.')& (line.__contains__('Var') or line.__contains__('Objective')):
            lin = line.split("=")
            name=lin[0].replace('model.','')
            unit=line.split('#*')[1]
            units[name.strip()]=unit.strip()
    return units

def analyse_results (res, instances, units):
    vars={}
    objs={}
    time_step=1
    for instance in instances:
        rs=res[time_step-1]
        for var_ in instance.active_components(Var):
            if var_ in vars.keys():
                 list_=vars[var_]
            else:
                list_=[]
            vars[var_]=get_values(instance, var_, list_, units)

        for var_ in instance.active_components(Objective):
            if var_ in objs.keys():
                 list_=objs[var_]
            else:
                list_=[]
            objs[var_]=get_obj_value(rs, var_, list_, units)
        time_step+=1
    return vars, objs

def get_obj_value(result, var_, list_, units):
    value_=result.solution[0].objective[1].Value
    varmodel=None
    for varmodel_ in list_:
        if varmodel_.name==var_ and varmodel_.owner=='Network':
            varmodel=varmodel_
            break
    if(varmodel==None):
        desc="Imported using Pyomo apps"
        if var_ in units.keys():
            unit=units[var_]
        else:
            unit="unit_less"
        varmodel=ModelVarable(var_, 'Network', desc, unit)
        list_.append(varmodel)
    varmodel.add_data(value_)
    return list_