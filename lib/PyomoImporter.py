#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright 2013, 2014, 2015 University of Manchester\
#\
# PyomoImporter is free software: you can redistribute it and/or modify\
# it under the terms of the GNU General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# PyomoImporter is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU General Public License for more details.\
# \
# You should have received a copy of the GNU General Public License\
# along with PyomoImporter.  If not, see <http://www.gnu.org/licenses/>\
#
__author__ = 'K. Mohamed'


from HydraLib.HydraException import HydraPluginError
from HydraLib.PluginLib import JsonConnection

import json
import logging
log = logging.getLogger(__name__)


class Importer:
    def __init__(self, vars, objs, actual_time_steps, url=None, session_id=None):
        self.vars=vars
        self.objs=objs
        self.actual_time_steps=actual_time_steps
        self.network_id = None
        self.scenario_id = None
        self.network = None
        self.res_scenario=None
        self.connection = JsonConnection(url)
        self.attrs = dict()
        self.time_axis = dict()
        if session_id is not None:
            log.info("Using existing session %s", session_id)
            self.connection.session_id = session_id
        else:
            self.connection.login()

    def load_network(self, network_id, scenario_id):
        """
         Load network and scenario from the server.
        """

        try:
            network_id = int(network_id)
        except (TypeError, ValueError):
            network_id = self.network_id
        if network_id is None:
            raise HydraPluginError("No network specified.")

        try:
            scenario_id = int(scenario_id)
        except (TypeError, ValueError):
            scenario_id = self.scenario_id
        if scenario_id is None:
            raise HydraPluginError("No scenario specified.")

        self.network = self.connection.call('get_network',
                                            {'network_id': int(network_id),
                                             'include_data': 'Y',
                                             'scenario_ids': [int(scenario_id)],
                                             'template_id': None})
        self.res_scenario = self.network.scenarios[0].resourcescenarios
        attrslist = self.connection.call('get_all_attributes', {})
        for attr in attrslist:
            self.attrs.update({attr.id: attr.name})

    #####################################################
    def set_network(self, network):
        """
           Load network and scenario from the server.
        """
        self.network =network
        #self.res_scenario = self.network.scenarios[0].resourcescenarios
        attrslist = self.connection.call('get_attributes', {})
        for attr in attrslist:
            self.attrs.update({attr.id: attr.name})
    #####################################################

    def create_timeseries(self, data):
        timeseries = {'ts_values': []}
        counter=0
        for time_s in self.actual_time_steps:
            timeseries['ts_values'].append({'ts_time':
                                            time_s,
                                            'ts_value':
                                            float(data[counter])
                                            })
            counter+=1
        return timeseries

    def create_scalar(self, value):
        return dict(param_value = value)

    def create_array(self, index, data):
        pass

    def create_descriptor(self, value):
        descriptor = dict(desc_val = value)
        return descriptor

    def save(self):
        self.network.scenarios[0].resourcescenarios = self.res_scenario
        self.connection.call('update_scenario', {'scen':self.network.scenarios[0]})

    def import_res(self):
        self.import_vars()
        self.import_objs()

    def import_vars(self):
        nodes = dict()
        for node in self.network.nodes:
            nodes.update({node.id: node.name})
        for var in self.vars.keys():
            for varModel in self.vars[var]:
                for link in self.network.links:
                    #print "Owner: ", type(varModel.owner)
                    fromnode = nodes[link.node_1_id]
                    tonode = nodes[link.node_2_id]
                    if fromnode in varModel.owner and tonode in varModel.owner:
                        # "It is here, link Var: ",var,": ",varModel.owner, ": ", varModel.data_set
                        for attr in link.attributes:
                            if self.attrs[attr.attr_id] == varModel.name:
                                if attr.attr_is_var == 'Y':
                                    dataset = dict(name = 'Pyomo import - ' + link.name + ' ' \
                                            + varModel.name)
                                dataset['unit'] = varModel.unit
                                if len(varModel.data_set)>1:
                                    dataset['type'] = 'timeseries'
                                    dataset['value'] = self.create_timeseries(varModel.data_set)
                                elif len(varModel.data_set) == 1:
                                     try:
                                        data = float(varModel.data_set [0])
                                        dataset['type'] = 'scalar'
                                        dataset['value'] = \
                                            self.create_scalar(data)
                                     except ValueError:
                                        dataset['type'] = 'descriptor'
                                        dataset['value'] = self.create_descriptor(varModel.data_set [0])
                                #print "link attr is added"
                                res_scen = dict(resource_attr_id = attr.id,
                                                                attr_id = attr.attr_id,
                                                                value = dataset)
                                self.res_scenario.append(res_scen)

                for node in self.network.nodes:
                    if node.name in varModel.owner and len(varModel.owner)==1:
                        # "node Var: ", var, ": ", varModel.owner,": ", varModel.data_set
                        for attr in node.attributes:
                            if self.attrs[attr.attr_id] == varModel.name:
                                if attr.attr_is_var == 'Y':
                                    dataset = dict(name = 'Pyomo import - ' + node.name + ' ' \
                                        + varModel.name)
                                    dataset['unit'] = varModel.unit
                                    if len(varModel.data_set)>1:
                                        dataset['type'] = 'timeseries'
                                        dataset['value'] = self.create_timeseries(varModel.data_set)
                                    elif len(varModel.data_set) == 1:
                                         try:
                                            data = float(varModel.data_set [0])
                                            dataset['type'] = 'scalar'
                                            dataset['value'] = \
                                            self.create_scalar(data)
                                         except ValueError:
                                            dataset['type'] = 'descriptor'
                                            dataset['value'] = self.create_descriptor(varModel.data_set [0])
                                    #print "node att is added"
                                    '''
                                    '''
                                    res_scen = dict(resource_attr_id = attr.id,
                                                    attr_id = attr.attr_id,
                                                    value = dataset)
                                    self.res_scenario.append(res_scen)
                                    # "Attr is added ...."

    def import_objs(self):
        for var in self.objs.keys():
            for varModel in self.objs[var]:
                for attr in self.network.attributes:
                    if attr.attr_is_var == 'Y':
                        if self.attrs[attr.attr_id] == varModel.name:
                            dataset = dict(name = 'Pyomo import - ' + self.network.name + ' ' \
                                            + varModel.name)
                            dataset['unit'] = varModel.unit
                            if len(varModel.data_set)>1:
                                dataset['type'] = 'timeseries'
                                dataset['value'] = self.create_timeseries(varModel.data_set)
                            elif len(varModel.data_set) == 1:
                                 try:
                                    data = float(varModel.data_set [0])
                                    dataset['type'] = 'scalar'
                                    dataset['value'] = \
                                    self.create_scalar(data)
                                 except ValueError:
                                    dataset['type'] = 'descriptor'
                                    dataset['value'] = self.create_descriptor(varModel.data_set [0])
                            '''
                            '''
                            res_scen = dict(resource_attr_id = attr.id,
                                            attr_id = attr.attr_id,
                                            value = dataset)
                            self.res_scenario.append(res_scen)
                            # "Network Attr is added ...."
