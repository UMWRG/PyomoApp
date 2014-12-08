# demo2.py
#Version: time-step by time-step
#Author: Majed Khadem

# Importing needed Packages

from coopr.pyomo import *
import coopr.environ
from coopr.opt import SolverFactory

# Declaring the model
model = AbstractModel()

# Declaring model indexes using sets
model.nodes = Set()
model.links = Set(within=model.nodes*model.nodes)
model.demand_nodes = Set()
model.nonstorage_nodes = Set()
model.storage_nodes = Set()
model.time_step = Set()
model.t = Set()

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

##======================== running the model in a loop for each time step
def run():
    opt = SolverFactory("glpk")
    instance = model.create("Demo2.dat")
    for t in instance.time_step:
        #model.t = Set([t])
        for link in model.links:
            model.c[link] = Param(model.links, model.t, initialize=instance.cost)
            model.flow_mult[link] = Param(model.links, model.t, initialize=instance.flow_multiplier)
            model.min_flow[link] = Param(model.links, model.t, initialize=instance.flow_lower_bound)
            model.max_flow[link] = Param(model.links, model.t, initialize=instance.flow_upper_bound)


        for node in model.nodes:
            model.Inflow[node] = Param(model.nodes, model.t, initialize=instance.inflow)
            model.cc[node] = Param(model.nodes, model.t, initialize=instance.consumption_coefficient)

        for s_node in model.storage_nodes:
            model.min_storage[s_node] = Param(model.storage_nodes, model.t, initialize=instance.storage_lower_bound)
            model.max_storage[s_node] = Param(model.storage_nodes, model.t, initialize=instance.storage_upper_bound)

##======================================== Declaring Variables (X and S)

        # Defining the flow lower and upper bound
        def current_flow_capacity_constraint(model, node, node2):
            return (model.min_flow[node, node2], model.max_flow[node, node2])

        # Defining the storage lower and upper bound
        def current_storage_capacity_constraint(model, storage_nodes):
            return (model.min_storage[storage_nodes], model.max_storage[storage_nodes])

        # Declaring decision variable X
        model.X = Var(model.links, domain=NonNegativeReals, bounds=current_flow_capacity_constraint)

        # Declaring state variable S
        model.S = Var(model.storage_nodes, domain=NonNegativeReals, bounds=current_storage_capacity_constraint)

##======================================== Declaring the objective function (Z)

        def objective_function(model):
            return summation(model.X, model.c)

        model.Z = Objective(model.links, rule=objective_function, sense=minimize)

##======================================== Declaring constraints

##------- Mass balance for non-storage nodes:

        def mass_balance(model, nonstorage_nodes):

    # inflow
            term1 = model.Inflow[nonstorage_nodes]
            term2 = sum([model.X[node_in, nonstorage_nodes]*model.flow_mult[node_in, nonstorage_nodes] for node_in in model.nodes if (node_in, nonstorage_nodes) in model.links])

    # outflow
            term3 = model.cc[nonstorage_nodes] * sum([model.X[node_in, nonstorage_nodes]*model.flow_mult[node_in, nonstorage_nodes] for node_in in model.nodes if (node_in, nonstorage_nodes) in model.links])
            term4 = sum([model.X[nonstorage_nodes, node_out] for node_out in model.nodes if (nonstorage_nodes, node_out) in model.links])

    # inflow - outflow = 0:
            return (term1 + term2) - (term3 + term4) == 0

        model.mass_balance_const = Constraint(model.nonstorage_nodes, rule=mass_balance)

##------- Mass balance for storage nodes:
        def storage_mass_balance(model, storage_nodes):

    # inflow
            term1 = model.inflow[storage_nodes]
            term2 = sum([model.X[node_in, storage_nodes]*model.flow_multiplier[node_in, storage_nodes] for node_in in model.nodes if (node_in, storage_nodes) in model.links])

    # outflow
            term3 = sum([model.X[storage_nodes, node_out] for node_out in model.nodes if (storage_nodes, node_out) in model.links])

    # storage
            term4 = model.new_init_S[storage_nodes]
            term5 = model.S[storage_nodes]

    # inflow - outflow = 0:
            return (term1 + term2 + term4) - (term3 + term5) == 0

        model.storage_mass_balance_const = Constraint(model.storage_nodes, rule=storage_mass_balance)

        print ('========================================================')
        res = opt.solve(instance)
        model.pprint()
        #instance.load(res)
        #res.write()
        #block.add_new_init_S = instance.S
        #block.del_S()
        #new_init_S = instance.S
        #model.S = Param(initialize=new_init_S)

if __name__ == '__main__':
    run()
