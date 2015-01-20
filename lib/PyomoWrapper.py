__author__ = 'K. Mohamed'

#from PyomoModel_2 import PyMode as model
from coopr.pyomo import *
from PyomoAppLib import ModelVarable
import os
import sys
import importlib
import pyutilib.component.core

def get_values(instance, var_, list_):
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
                varmodel=ModelVarable(var_, owner, desc)
                list_.append(varmodel)
            varmodel.add_data(value_)
        except:
            pass
    return list_

def runmodel(filename, modelfile):
    mname=os.path.dirname(modelfile)
    sys.path.append(mname)
    mm=importlib.import_module(os.path.basename(modelfile).split('.')[0])
    run_model=getattr(mm, 'run_model')
    res, instances=run_model(filename)
    return analyse_results (res, instances)

def analyse_results (res, instances):
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
            vars[var_]=get_values(instance, var_, list_)

        for var_ in instance.active_components(Objective):
            if var_ in objs.keys():
                 list_=objs[var_]
            else:
                list_=[]
            objs[var_]=get_obj_value(rs, var_, list_)
        time_step+=1
    return vars, objs

def get_obj_value(result, var_, list_):
    value_=result.solution[0].objective[1].Value
    varmodel=None
    for varmodel_ in list_:
        if varmodel_.name==var_ and varmodel_.owner=='Network':
            varmodel=varmodel_
            break
    if(varmodel==None):
        desc="Imported using Pyomo apps"
        varmodel=ModelVarable(var_, 'Network', desc)
        list_.append(varmodel)
    varmodel.add_data(value_)
    return list_