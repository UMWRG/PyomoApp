# demo2.py
#Version: time-step by time-step
#Author: Majed Khadem

# Importing needed Packages

from coopr.pyomo import *
import coopr.environ
from coopr.opt import SolverFactory

# Declaring the model
model = AbstractModel(name="demo2 model")

# Declaring model indexes using sets
model.nodes = Set()
model.links = Set(within=model.nodes*model.nodes)
model.demand_nodes = Set()
model.nonstorage_nodes = Set()
model.storage_nodes = Set()
model.time_step = Set()

# Declaring model parameters
model.inflow = Param(model.nodes, model.time_step)
model.consumption_coefficient = Param(model.nodes, model.time_step)
model.initial_storage = Param(model.storage_nodes, model.time_step)
model.cost = Param(model.links, model.time_step)
model.flow_multiplier = Param(model.links, model.time_step)
model.flow_lower_bound = Param(model.links, model.time_step)
model.flow_upper_bound = Param(model.links, model.time_step)
model.storage_lower_bound = Param(model.storage_nodes, model.time_step)
model.storage_upper_bound = Param(model.storage_nodes, model.time_step)

def current_flow_capacity_constraint(instance, node, node2):
    """
        Defining the flow lower and upper bound
    """
    return (instance.flow_lower_bound[node, node2, instance.t],
            instance.flow_upper_bound[node, node2, instance.t])

def current_storage_capacity_constraint(instance, storage_nodes):
    """
        Defining the storage lower and upper bound
    """
    return (instance.storage_lower_bound[storage_nodes, instance.t],
            instance.storage_upper_bound[storage_nodes, instance.t])

def objective_function(instance):
    return summation(instance.cost, instance.X)

def mass_balance(instance, nonstorage_nodes):
    """
        Mass balance for non-storage nodes:
    """

    # inflow
    term1 = instance.inflow[nonstorage_nodes, instance.t]
    term2 = sum([instance.X[node_in, nonstorage_nodes, instance.t]*instance.flow_multiplier[node_in, nonstorage_nodes, instance.t] for node_in in instance.nodes if (node_in, nonstorage_nodes) in instance.links])
    
    # outflow
    term3 = instance.consumption_coefficient[nonstorage_nodes, instance.t] * sum([instance.X[node_in, nonstorage_nodes, instance.t]*instance.flow_multiplier[node_in, nonstorage_nodes, instance.t] for node_in in instance.nodes if (node_in, nonstorage_nodes) in instance.links])
    term4 = sum([instance.X[nonstorage_nodes, node_out] for node_out in instance.nodes if (nonstorage_nodes, node_out) in instance.links])

    # inflow - outflow = 0:
    return (term1 + term2) - (term3 + term4) == 0

def storage_mass_balance(instance, storage_nodes):
    """
        Mass balance for storage nodes
    """
    # inflow
    term1 = instance.inflow[storage_nodes, instance.t]
    term2 = sum([instance.X[node_in, storage_nodes, instance.t]*instance.flow_multiplier[node_in, storage_nodes, instance.t] for node_in in instance.nodes if (node_in, storage_nodes) in instance.links])

    # outflow
    term3 = sum([instance.X[storage_nodes, node_out, instance.t] for node_out in instance.nodes if (storage_nodes, node_out) in instance.links])

    # storage
    term4 = instance.new_init_S[storage_nodes, instance.t]
    term5 = instance.S[storage_nodes, instance.t]

    # inflow - outflow = 0:
    return (term1 + term2 + term4) - (term3 + term5) == 0

##======================== running the model in a loop for each time step
def run():
    opt = SolverFactory("glpk")
    instance = model.create("Demo2.dat")
    for t in instance.time_step:
        instance.t = t

        # Declaring decision variable X
        instance.X = Var(instance.links, domain=NonNegativeReals, bounds=current_flow_capacity_constraint)

        # Declaring state variable S
        instance.S = Var(instance.storage_nodes, domain=NonNegativeReals, bounds=current_storage_capacity_constraint)

        # Declaring state variable S
        instance.c = Var(instance.nodes, domain=NonNegativeReals, bounds=current_cost)


        instance.Z = Objective(rule=objective_function, sense=minimize)


        instance.mass_balance_const = Constraint(instance.nonstorage_nodes, rule=mass_balance)

        instance.storage_mass_balance_const = Constraint(instance.storage_nodes, rule=storage_mass_balance)

        print ('========================================================')
        res = opt.solve(instance)
        instance.pprint()
        #instance.load(res)
        #res.write()
        #block.add_new_init_S = instance.S
        #block.del_S()
        #new_init_S = instance.S
        #instance.S = Param(initialize=new_init_S)

if __name__ == '__main__':
    run()
