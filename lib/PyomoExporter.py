#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright 2013, 2014, 2015 University of Manchester\
#\
# PyomoExporter is free software: you can redistribute it and/or modify\
# it under the terms of the GNU General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# PyomoExporter is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU General Public License for more details.\
# \
# You should have received a copy of the GNU General Public License\
# along with PyomoExporter.  If not, see <http://www.gnu.org/licenses/>\
#
__author__ = 'K Mohamed'

import re

from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from HydraLib.PluginLib import JsonConnection
from HydraLib.dateutil import guess_timefmt, date_to_string
from HydraLib.PluginLib import HydraNetwork
from PyomoAppLib import get_link_name
from PyomoAppLib import get_link_name_for_param
from PyomoAppLib import translate_attr_name
from HydraLib.PluginLib import write_progress
from HydraLib.HydraException import HydraPluginError

import json
import logging
log = logging.getLogger(__name__)

class Exporter (object):

    def __init__(self, steps, output_file, link_export_flag,  url=None, session_id=None):
        self.steps=steps
        write_progress(1, self.steps)
        self.connection = JsonConnection(url)
        self.output_file=output_file
        self.output_file_contents=[];
        self.output_file_contents.append("#%s\n"%("*"*78,))
        self.output_file_contents.append("# Data exported from Hydra using PyomoPlugin.\n")
        self.output_file_contents.append("# (c) Copyright 2015, University of Manchester\n")
        self.time_index = {}

        if session_id is not None:
            log.info("Using existing session %s", session_id)
            self.connection.session_id=session_id
        else:
            self.connection.login()

        if link_export_flag == 'l':
            self.links_as_name = True
        else:
            self.links_as_name = False


    def export_network (self, network_id, scenario_id, template_id, export_by_type=False):
        write_progress(2, self.steps)
        net = self.connection.call('get_network', {'network_id':network_id,
                                                   'include_data': 'Y',
                                                   'template_id':template_id,
                                                   'scenario_ids':[scenario_id]})

        log.info("Network retrieved")
        attrs = self.connection.call('get_all_attributes', {})
        log.info("%s attributes retrieved", len(attrs))
        self.net=net
        self.network= HydraNetwork()
        self.template_id =template_id
        self.network.load(net , attrs)
        log.info("Loading net into network.")
        nodes_map=dict ()
        for node in net.nodes:
            nodes_map[node.id]=node.name
        self.get_longest_node_link_name();
        write_progress(3, self.steps)
        self.output_file_contents.append("# Network-ID:  "+str(network_id));
        self.output_file_contents.append("\n# Scenario-ID: "+str(scenario_id));
        self.output_file_contents.append("\n#" + "*"*100)

        self.write_nodes()
        write_progress(4, self.steps)
        self.write_links(nodes_map)
        write_progress(5, self.steps)
        self.export_node_groups()
        nodes_types=self.network.get_node_types(template_id=self.template_id)
        links_types=self.network.get_link_types(template_id=self.template_id)
        self.export_node_types(nodes_types)
        self.export_links_types(links_types)
        write_progress(6, self.steps)
        if len(self.time_index)>0:
            self.output_file_contents.append('\nset time_step:=')
            for timestep in self.time_index.keys():
                self.output_file_contents.append(" " +str(timestep))
            self.output_file_contents.append(';\n')

            self.output_file_contents.append('\nset actual_time_step:=')
            for timestep in self.time_index.values():
                self.output_file_contents.append(" " +str(timestep))
            self.output_file_contents.append(';\n')
        write_progress(7, self.steps)

        if export_by_type is True:
            self.export_data_using_types(nodes_types, links_types)
        else:
            self.export_data_using_attributes()

    def get_longest_node_link_name(self):
        node_name_len=0
        for node in self.network.nodes:
            if len(node.name)>node_name_len:
                node_name_len=len(node.name)

        self.ff='{0:<'+str(2*node_name_len+5)+'}'

    def save_file(self):
        write_progress(8, self.steps)
        log.info("writing data to file")
        file = open(self.output_file, "w")
        file.write("".join(self.output_file_contents))
        file.close()

    def write_nodes(self):
        self.output_file_contents.append("\n\nset  nodes := ")
        for node in self.network.nodes:
            self.output_file_contents.append(" "+node.name)
        self.output_file_contents.append(';')

    def write_links(self, nodes_map):
        self.output_file_contents.append("\n\nset  links:= ")
        for link in self.network.links:
             if self.links_as_name is False:
                 self.output_file_contents.append("\n"+ link.from_node+" "+link.to_node)
             else:
                self.output_file_contents.append("\n"+ link.name)

        self.output_file_contents.append(';\n')

    def export_node_groups(self):
        "Export node groups if there are any."
        node_groups = []
        self.output_file_contents.append("\n#Nodes groups\n")
        for group in self.network.groups:
            group_nodes = self.network.get_node(group=group.ID)
            if len(group_nodes) > 0:
                node_groups.append(group)
                self.output_file_contents.append("\nset  "+group.name+":= \n")
                for node in group_nodes:
                    self.output_file_contents.append(node.name+'\n')
                self.output_file_contents.append(';\n')

    def export_node_types(self, nodes_types):
        "Export node groups if there are any."
        self.output_file_contents.append("\n#Nodes types\n")
        for node_type in nodes_types:
            self.output_file_contents.append("\nset  "+node_type+":= \n")
            #for node in self.network.nodes:
            for node in self.network.get_node(node_type=node_type):
                self.output_file_contents += node.name + '\n'
            self.output_file_contents.append(';\n')

    def export_links_types(self, links_types):
            "Export node groups if there are any."
            for link_type in links_types:
                self.output_file_contents.append("\nset  "+link_type+":= \n")
                for link in self.network.get_link(link_type=link_type):
                     if self.links_as_name is False:
                         self.output_file_contents.append("\n"+ link.from_node+" "+link.to_node)
                     else:
                         self.output_file_contents.append("\n"+ link.name)
                self.output_file_contents.append(';\n')

    def export_data_using_types(self, nodes_types, links_types):
        log.info("Exporting data")
        # Export node data for each node type
        for node_type in nodes_types:
            nodes = self.network.get_node(node_type=node_type)
            self.export_parameters_using_types(nodes, node_type, 'scalar')
            self.export_parameters_using_types(nodes, node_type, 'descriptor')
            self.export_timeseries_using_types(nodes, node_type)

        for link_type in links_types:
            links = self.network.get_link(link_type=link_type)
            self.export_parameters_using_types(links, link_type, 'scalar', res_type='LINK')
            self.export_parameters_using_types(links, link_type,'descriptor', res_type='LINK')
            self.export_timeseries_using_types(links, link_type, res_type='LINK')
        #
    def export_data_using_attributes (self):
        log.info("Exporting data")
        # Export node data for each node type
        #for node_type in nodes_types:
        #nodes = self.network.get_node(node_type=node_type)
        self.export_parameters_using_attributes(self.network.nodes, 'scalar')
        self.export_parameters_using_attributes(self.network.nodes,  'descriptor')
        self.export_timeseries_using_attributes(self.network.nodes)

        #for link_type in links_types:
        #links = self.network.get_link(link_type=link_type)
        self.export_parameters_using_attributes(self.network.links, 'scalar', res_type='LINK')
        self.export_parameters_using_attributes(self.network.links, 'descriptor', res_type='LINK')
        self.export_timeseries_using_attributes(self.network.links,  res_type='LINK')
        #
    def export_parameters_using_types(self, resources, obj_type, datatype, res_type=None):
        """Export scalars or descriptors.
        """
        self.network.attributes
        islink = res_type == 'LINK'
        attributes = []
        attr_names = []
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == datatype and attr.is_var is False:
                    translated_attr_name = translate_attr_name(attr.name)
                    attr.name = translated_attr_name
                    if attr.name not in attr_names:
                        attributes.append(attr)
                        attr_names.append(attr.name)

        if len(attributes) > 0:
            for attribute in attributes:
                nname="\nparam "+attribute.name+"_"+obj_type+':='
                contents=[]
                #self.output_file_contents.append("\nparam "+attribute.name+':=')
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is None or attr.value is None:
                        continue

                    name=resource.name
                    if islink is True and self.links_as_name is False:
                        name=get_link_name_for_param(resource)

                    #self.output_file_contents.append("\n "+name+"  "+str(attr.value.values()[0][0]))
                    contents.append("\n "+self.ff.format(name)+self.ff.format(str(attr.value.values()[0][0])))
                if len(contents)>0:
                    self.output_file_contents.append(nname)
                    for st in contents:
                        self.output_file_contents.append(st)

                    self.output_file_contents.append(';\n')

    def export_parameters_using_attributes(self, resources, datatype, res_type=None):
        """
        Export scalars or descriptors.
        """
        islink = res_type == 'LINK'
        attributes = []
        attr_names = []
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == datatype and attr.is_var is False:
                    translated_attr_name = translate_attr_name(attr.name)
                    attr.name = translated_attr_name
                    if attr.name not in attr_names:
                        attributes.append(attr)
                        attr_names.append(attr.name)

        if len(attributes) > 0:
            for attribute in attributes:
                nname="\nparam "+attribute.name+':='
                contents=[]
                #self.output_file_contents.append("\nparam "+attribute.name+':=')
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is None or attr.value is None:
                        continue

                    name=resource.name
                    if islink is True and self.links_as_name is False:
                            name=get_link_name_for_param(resource)

                    #self.output_file_contents.append("\n "+name+"  "+str(attr.value.values()[0][0]))
                    contents.append("\n "+self.ff.format(name)+self.ff.format(str(attr.value.values()[0][0])))
                if len(contents)>0:
                    self.output_file_contents.append(nname)
                    for st in contents:
                        self.output_file_contents.append(st)

                    self.output_file_contents.append(';\n')



    def export_timeseries_using_types(self, resources, obj_type, res_type=None):
        """
        Export time series.
        """
        islink = res_type == 'LINK'
        attributes = []
        attr_names = []
        attrb_tables={}
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == 'timeseries' and attr.is_var is False:
                    attr.name = translate_attr_name(attr.name)
                    if attr.name not in attr_names:
                        attrb_tables[attr.name]=attr
                        attributes.append(attr)
                        attr_names.append(attr.name)

        if len(attributes) > 0:
            dataset_ids = []

            #Identify the datasets that we need data for
            for attribute in attributes:
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is not None and attr.dataset_id is not None:
                        dataset_ids.append(attr.dataset_id)
            
            #We need to get the value at each time in the specified time axis,
            #so we need to identify the relevant timestamps.
            soap_times = []
            for t, timestamp in enumerate(self.time_index.values()):
                soap_times.append(date_to_string(timestamp))

            #Get all the necessary data for all the datasets we have.
            all_data = self.connection.call('get_multiple_vals_at_time',
                                        {'dataset_ids':dataset_ids,
                                         'timestamps' : soap_times})

            for attribute in attributes:
                self.output_file_contents.append("\nparam "+attribute.name+"_"+obj_type+":\n")
                self.output_file_contents.append(self.write_time())
                for resource in resources:
                    name=resource.name
                    if islink is True and self.links_as_name is False:
                        name=get_link_name(resource)
                    #self.output_file_contents.append("\n  "+name)
                    nname="\n  "+name
                    contents=[]
                    for t, timestamp in enumerate(self.time_index.values()):
                        attr = resource.get_attribute(attr_name=attribute.name)
                        if attr is not None and attr.dataset_id is not None:
                            #Get the value at this time in the given timestamp
                            soap_time = date_to_string(timestamp)
                            data = json.loads(all_data["dataset_%s"%attr.dataset_id]).get(soap_time)

                            if data is None:
                                continue

                            data_str = self.ff.format(str(data))
                            #self.output_file_contents.append("   "+data_str)
                            contents.append(data_str)
                    if len(contents)>0:
                        self.output_file_contents.append(self.ff.format(nname))
                        for st in contents:
                            self.output_file_contents.append(st)
                self.output_file_contents.append(';\n')

    def export_timeseries_using_attributes(self, resources, res_type=None):
        """
        Export time series.
        """
        islink = res_type == 'LINK'
        attributes = []
        attr_names = []
        attrb_tables={}
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == 'timeseries' and attr.is_var is False:
                    attr.name = translate_attr_name(attr.name)
                    if attr.name not in attr_names:
                        attrb_tables[attr.name]=attr
                        attributes.append(attr)
                        attr_names.append(attr.name)

        if len(attributes) > 0:
            dataset_ids = []

            #Identify the datasets that we need data for
            for attribute in attributes:
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is not None and attr.dataset_id is not None:
                        dataset_ids.append(attr.dataset_id)

            #We need to get the value at each time in the specified time axis,
            #so we need to identify the relevant timestamps.
            soap_times = []
            for t, timestamp in enumerate(self.time_index.values()):
                soap_times.append(date_to_string(timestamp))

            #Get all the necessary data for all the datasets we have.
            all_data = self.connection.call('get_multiple_vals_at_time',
                                        {'dataset_ids':dataset_ids,
                                         'timestamps' : soap_times})

            for attribute in attributes:
                self.output_file_contents.append("\nparam "+attribute.name+":\n")
                self.output_file_contents.append(self.write_time())
                for resource in resources:
                    name=resource.name
                    if islink is True and self.links_as_name is False:
                        name=get_link_name(resource)
                    #self.output_file_contents.append("\n  "+name)
                    nname="\n  "+name;
                    contents=[]
                    for t, timestamp in enumerate(self.time_index.values()):
                        attr = resource.get_attribute(attr_name=attribute.name)
                        if attr is not None and attr.dataset_id is not None:
                            #Get the value at this time in the given timestamp
                            soap_time = date_to_string(timestamp)
                            data = json.loads(all_data["dataset_%s"%attr.dataset_id]).get(soap_time)

                            if data is None:
                                continue

                            data_str =self.ff.format(str(data))
                            #self.output_file_contents.append("   "+data_str)
                            contents.append(data_str)
                    if len(contents)>0:
                        self.output_file_contents.append(self.ff.format(nname))
                        for st in contents:
                            self.output_file_contents.append(st)
                self.output_file_contents.append(';\n')


    def write_time(self):
        time_string=self.ff.format("")
        for t in self.time_index.keys():
            time_string+=(self.ff.format(str(t)))
        time_string+=(':=')
        return time_string

    def write_time_index(self, start_time=None, end_time=None, time_step=None,
                         time_axis=None):
        try:
            log.info("Writing time index")

            if time_axis is None:
                start_date =datetime.strptime(start_time, guess_timefmt(start_time))
                end_date =datetime.strptime(end_time, guess_timefmt(end_time))

                delta_t, value, units = self.parse_time_step(time_step)

                t = 1
                while start_date <= end_date:
                    self.time_index[t]=start_date
                    if(units== "mon"):
                        start_date=start_date+relativedelta(months=value)
                    else:
                        start_date += timedelta(delta_t)

                    t += 1
            else:
                time_axis = ' '.join(time_axis).split(',')
                t = 1
                for timestamp in time_axis:
                    date = end_date =datetime.strptime(timestamp.strip(), guess_timefmt(timestamp.strip()))
                    self.time_index[t]=date
                    t += 1
        except Exception as e:
            raise HydraPluginError("Please check time-axis or start time, end times and time step.")

    def parse_time_step(self, time_step):
        """Read in the time step and convert it to days.
        """
        # export numerical value from string using regex
        value = re.findall(r'\d+', time_step)[0]
        valuelen = len(value)
        value = value
        units = time_step[valuelen:].strip()
        converted_time_step = self.connection.call('convert_units', {
            'values':[value], 'unit1':units, 'unit2':'day'})[0]
        return float(converted_time_step), value, units


















