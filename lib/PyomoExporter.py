#from ecdsa import keys

__author__ = 'K Mohamed'

#example
#

import re

from datetime import datetime
from datetime import timedelta

from HydraLib.PluginLib import JsonConnection
from HydraLib.dateutil import guess_timefmt, date_to_string
from HydraLib.PluginLib import HydraNetwork
from PyomoAppLib import get_link_name
from PyomoAppLib import translate_attr_name
import json
import logging
log = logging.getLogger(__name__)

class Exporter (object):

    def __init__(self, output_file, url=None, session_id=None):

        self.connection = JsonConnection(url)
        self.output_file=output_file
        self.output_file_contenets=[];
        self.time_index = {}

        if session_id is not None:
            log.info("Using existing session %s", session_id)
            self.connection.session_id=session_id
        else:
            self.connection.login()


    def expoty_network (self, network_id, scenario_id, template_id ):
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
        self.write_nodes()
        self.write_links(nodes_map)
        self.export_node_groups()
        if(len(self.time_index)>0):
            self.output_file_contenets.append('\nset time_step:=')
            for timestep in self.time_index.keys():
                self.output_file_contenets.append(" " +str(timestep))
            self.output_file_contenets.append(';\n')

            self.output_file_contenets.append('\nset actual_time_step:=')
            for timestep in self.time_index.values():
                self.output_file_contenets.append(" " +str(timestep))
            self.output_file_contenets.append(';\n')
        self.export_data()

    def save_file(self):
        log.info("writing data to file")
        file = open(self.output_file, "w")
        file.write("".join(self.output_file_contenets))
        file.close()


    def write_nodes(self):
        self.output_file_contenets.append("\n\nset  nodes := ")
        for node in self.network.nodes:
            self.output_file_contenets.append(" "+node.name)
        self.output_file_contenets.append(';')

    def write_links(self, nodes_map):
        self.output_file_contenets.append("\n\nset  links:= ")
        for link in self.network.links:
            self.output_file_contenets.append("\n"+ link.from_node+" "+link.to_node)
        self.output_file_contenets.append(';\n')

    def export_node_groups(self):
        "Export node groups if there are any."
        node_groups = []
        group_strings = []
        groups=""
        for group in self.network.groups:
            group_nodes = self.network.get_node(group=group.ID)
            if len(group_nodes) > 0:
                node_groups.append(group)
                self.output_file_contenets.append("\nset  "+group.name+":= \n")
                for node in group_nodes:
                    self.output_file_contenets.append(node.name+'\n')
                self.output_file_contenets.append(';\n')

    def export_data(self):
        log.info("Exporting data")
        # Export node data for each node type
        nodes_types= self.network.get_node_types(template_id=self.template_id)
        links_types=self.network.get_link_types(template_id=self.template_id)
        for node_type in nodes_types:
            nodes = self.network.get_node(node_type=node_type)
            self.export_parameters(nodes, node_type, 'scalar')
            self.export_parameters(nodes, node_type, 'descriptor')
            self.export_timeseries(nodes, node_type)

        for link_type in links_types:
            links = self.network.get_link(link_type=link_type)
            self.export_parameters(links, link_type, 'scalar', res_type='LINK')
            self.export_parameters(links, link_type,'descriptor', res_type='LINK')
            self.export_timeseries(links, link_type, res_type='LINK')
        #

    def export_parameters(self, resources, obj_type, datatype, res_type=None):
        """Export scalars or descriptors.
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
                #self.output_file_contenets.append("\nparam "+attribute.name+':=')
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is None or attr.value is None:
                        continue

                    name=resource.name
                    if islink:
                        name=get_link_name(resource)

                    #self.output_file_contenets.append("\n "+name+"  "+str(attr.value.values()[0][0]))
                    contents.append("\n "+name+"  "+str(attr.value.values()[0][0]))
                if len(contents)>0:
                    self.output_file_contenets.append(nname)
                    for st in contents:
                        self.output_file_contenets.append(st)

                    self.output_file_contenets.append(';\n')


    def export_timeseries(self, resources, obj_type, res_type=None):
        """
        Export time series.
        """
        islink = res_type == 'LINK'
        attributes = []
        attr_names = []
        attr_outputs = []
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
                self.output_file_contenets.append("\nparam "+attribute.name+":\n")
                self.output_file_contenets.append(self.write_time())
                for resource in resources:
                    name=resource.name
                    if(islink):
                        name=get_link_name(resource)
                    #self.output_file_contenets.append("\n  "+name)
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

                            data_str = ' %14f' % float(data)
                            #self.output_file_contenets.append("   "+data_str)
                            contents.append("   "+data_str)
                    if len(contents)>0:
                        self.output_file_contenets.append(nname)
                        for st in contents:
                            self.output_file_contenets.append(st)
                self.output_file_contenets.append(';\n')

    def write_time(self):
        time_string=""
        for t in self.time_index.keys():
            time_string+=("  "+ str(t))
        time_string+=(':=')
        return time_string

    def write_time_index(self, start_time=None, end_time=None, time_step=None,
                         time_axis=None):
        log.info("Writing time index")

        time_index = ['SETS\n\n', '* Time index\n','t time index /\n']

        if time_axis is None:
            start_date =datetime.strptime(start_time, guess_timefmt(start_time))
            end_date =datetime.strptime(end_time, guess_timefmt(end_time))

            delta_t = self.parse_time_step(time_step)

            t = 1
            while start_date < end_date:
                self.time_index[t]=start_date
                start_date += timedelta(delta_t)
                t += 1
        else:
            time_axis = ' '.join(time_axis).split(',')
            t = 1
            for timestamp in time_axis:
                date = end_date =datetime.strptime(timestamp.strip(), guess_timefmt(timestamp.strip()))
                self.time_index[t]=date
                t += 1

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
        return float(converted_time_step)


















