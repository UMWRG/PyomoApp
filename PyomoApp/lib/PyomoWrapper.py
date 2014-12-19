__author__ = 'K. Mohamed'

from PyomoModel_2 import PyMode as model
from coopr.pyomo import *

def getValues_(instance, var_, dicts):
    x_var = getattr(instance, var_)
    for xx in x_var:

        try:
            if type(xx) is str:
                name=xx
            else:
                name= "(" + ', '.join(map(str,xx)) + ")"
            if xx in dicts.keys():
                list=dicts[xx]
                list.append(x_var[xx].value)
                dicts[xx]=list
            else:
                list=[]
                list.append(x_var[xx].value)
                dicts[xx]=list
                return xx,  x_var[xx].value
            print "Name: ",name,", Value: ", x_var[xx].value
        except:
            pass

def runmodel(filename):
    pymodel=model()
    instances =pymodel.run(filename)
    vars={}
    objs={}
    for instance in instances:
        for var_ in instance.active_components(Var):
             getValues_(instance, var_, vars)

        for obj_ in instance.active_components(Objective):
             getValues_(instance, obj_, objs)
    print "Done ............................."





