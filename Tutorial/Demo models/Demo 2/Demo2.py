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
model.time_step = RangeSet(1, 6)

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

def current_flow_capacity_constraint(model, node, node2, ts):
    """
        Defining the flow lower and upper bound
    """
    return (model.flow_lower_bound[node, node2, ts],
            model.flow_upper_bound[node, node2, ts])

def current_storage_capacity_constraint(model, storage_nodes, ts):
    """
        Defining the storage lower and upper bound
    """
    return (model.storage_lower_bound[storage_nodes, ts],
            model.storage_upper_bound[storage_nodes, ts])

def current_cost(model, node, node2, ts):
    """
    """
    return model.cost[storage_nodes, ts]

def objective_function(model, ts):
    return summation(model.c, model.X)

def mass_balance(model, nonstorage_nodes, ts):
    """
        Mass balance for non-storage nodes:
    """

    # inflow
    term1 = model.inflow[nonstorage_nodes, ts]
    term2 = sum([model.X[node_in, nonstorage_nodes,ts]*model.flow_multiplier[node_in, nonstorage_nodes, ts] for node_in in model.nodes if (node_in, nonstorage_nodes) in model.links])
    
    # outflow
    term3 = model.consumption_coefficient[nonstorage_nodes, ts] * sum([model.X[node_in, nonstorage_nodes, ts]*model.flow_multiplier[node_in, nonstorage_nodes, ts] for node_in in model.nodes if (node_in, nonstorage_nodes) in model.links])
    term4 = sum([model.X[nonstorage_nodes, node_out, ts] for node_out in model.nodes if (nonstorage_nodes, node_out) in model.links])

    # inflow - outflow = 0:
    return (term1 + term2) - (term3 + term4) == 0

def storage_mass_balance(model, storage_nodes, ts):
    """
        Mass balance for storage nodes
    """
    # inflow
    term1 = model.inflow[storage_nodes, ts]
    term2 = sum([model.X[node_in, storage_nodes, ts]*model.flow_multiplier[node_in, storage_nodes, ts] for node_in in model.nodes if (node_in, storage_nodes) in model.links])

    # outflow
    term3 = sum([model.X[storage_nodes, node_out, ts] for node_out in model.nodes if (storage_nodes, node_out) in model.links])

    # storage
    term4 = model.initial_storage[storage_nodes, ts]
    term5 = model.S[storage_nodes, ts]

    # inflow - outflow = 0:
    return (term1 + term2 + term4) - (term3 + term5) == 0

##======================== running the model in a loop for each time step
def run():
    opt = SolverFactory("glpk")
    # Declaring decision variable X
    model.X = Var(model.links, model.time_step, domain=NonNegativeReals, bounds=current_flow_capacity_constraint)
    
    model.c = Var(model.links, model.time_step)

    # Declaring state variable S
    model.S = Var(model.storage_nodes, model.time_step, domain=NonNegativeReals, bounds=current_storage_capacity_constraint)
        
    model.Z = Objective(model.time_step, rule=objective_function, sense=minimize)

    model.mass_balance_const = Constraint(model.nonstorage_nodes, model.time_step, rule=mass_balance)

    model.storage_mass_balance_const = Constraint(model.storage_nodes, model.time_step, rule=storage_mass_balance)

    print ('========================================================')
    instance = model.create("Demo2.dat")
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
