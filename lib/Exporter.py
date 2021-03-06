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
from string import ascii_lowercase

from HydraLib.PluginLib import JsonConnection
from HydraLib.hydra_dateutil import guess_timefmt, date_to_string
from HydraLib.PluginLib import HydraNetwork
#from HydraLib.util import array_dim, parse_array
from HydraPyomoLib import get_link_name
from HydraPyomoLib import get_link_name_for_param
from HydraPyomoLib import translate_attr_name
from HydraPyomoLib import arr_to_matrix
from HydraLib.PluginLib import write_progress
from HydraLib.HydraException import HydraPluginError
from HydraLib.PluginLib import JSONPlugin
from HydraLib.hydra_dateutil import reindex_timeseries



import json
from dateutil.parser import parse
import logging
log = logging.getLogger(__name__)

class Exporter (JSONPlugin):

    def __init__(self, args, link_export_flag, steps):

        if link_export_flag == 'l':
            self.links_as_name = True
        else:
            self.links_as_name = False
        self.steps=steps

        self.use_gams_date_index=False
        self.network_id = int(args.network)
        self.scenario_id = int(args.scenario)
        self.template_id = int(args.template_id) if args.template_id is not None else None
        self.output_file = args.output
        self.export_by_type =args.export_by_type
        self.time_index = []
        write_progress(1, self.steps)
        self.output_file_contents=[];
        self.output_file_contents.append("#%s\n"%("*"*78,))
        self.output_file_contents.append("# Data exported from Hydra using PyomoPlugin.\n")
        self.output_file_contents.append("# (c) Copyright 2015, University of Manchester\n")
        self.time_index = {}
        self.connect(args)

    def export_network (self):
        '''
        export the network from Hydra
        '''
        write_progress(2, self.steps)
        net = self.connection.call('get_network', {'network_id':self.network_id,
                                                   'include_data': 'Y',
                                                   'template_id':self.template_id,
                                                   'scenario_ids':[self.scenario_id]})

        log.info("Network retrieved")
        attrs = self.connection.call('get_all_attributes', {})
        log.info("%s attributes retrieved", len(attrs))
        self.net=net
        self.network= HydraNetwork()
        self.network.load(net , attrs)
        log.info("Loading net into network.")
        nodes_map=dict ()
        for node in net.nodes:
            nodes_map[node.id]=node.name
        self.get_longest_node_link_name();
        write_progress(3, self.steps)
        self.output_file_contents.append("# Network-ID:  "+str(self.network_id));
        self.output_file_contents.append("\n# Scenario-ID: "+str(self.scenario_id));
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

        if self.export_by_type is True:
            self.export_data_using_types(nodes_types, links_types)
        else:
            self.export_data_using_attributes()

    def get_longest_node_link_name(self):
        '''
        get the length of longest node and link name to be used
         for file format
        '''
        node_name_len=0
        for node in self.network.nodes:
            if len(node.name)>node_name_len:
                node_name_len=len(node.name)

        self.ff='{0:<'+str(2*node_name_len+5)+'}'
        self.ff__=2*node_name_len+5

    def save_file(self):
        '''
        save output file
        '''
        write_progress(8, self.steps)
        log.info("writing data to file")
        file = open(self.output_file, "w")
        file.write("".join(self.output_file_contents))
        file.close()

    def write_nodes(self):
        '''
        write nodes to output file
        '''
        self.output_file_contents.append("\n\nset  nodes := ")
        for node in self.network.nodes:
            self.output_file_contents.append(" "+node.name)
        self.output_file_contents.append(';')

    def write_links(self, nodes_map):
        '''
        write links to output file
        '''
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
        self.time_table={}
        # Export node data for each node type
        self.export_parameters_using_types([self.network], "NETWORK", 'scalar')
        self.export_parameters_using_types([self.network], "NETWORK", 'descriptor')
        self.export_timeseries_using_types([self.network], "NETWORK")

        for node_type in nodes_types:
            nodes = self.network.get_node(node_type=node_type)
            self.export_parameters_using_types(nodes, node_type, 'scalar')
            self.export_parameters_using_types(nodes, node_type, 'descriptor')
            self.export_timeseries_using_types(nodes, node_type)
            self.export_arrays(nodes)

        for link_type in links_types:
            links = self.network.get_link(link_type=link_type)
            self.export_parameters_using_types(links, link_type, 'scalar', res_type='LINK')
            self.export_parameters_using_types(links, link_type,'descriptor', res_type='LINK')
            self.export_timeseries_using_types(links, link_type, res_type='LINK')
            self.export_arrays(links)
        #
    def export_data_using_attributes (self):
        log.info("Exporting data")
        # Export node data for each node type
        #for node_type in nodes_types:
        self.time_table={}
        self.export_parameters_using_attributes([self.network], 'scalar',  res_type='NETWORK')
        self.export_parameters_using_attributes([self.network],  'descriptor', res_type='NETWORK')
        self.export_timeseries_using_attributes([self.network], res_type='NETWORK')

        self.export_arrays(self.network.nodes)
        #nodes = self.network.get_node(node_type=node_type)
        self.export_parameters_using_attributes(self.network.nodes, 'scalar')
        self.export_parameters_using_attributes(self.network.nodes,  'descriptor')
        self.export_timeseries_using_attributes(self.network.nodes)
        self.export_arrays(self.network.nodes)

        #for link_type in links_types:
        #links = self.network.get_link(link_type=link_type)
        self.export_parameters_using_attributes(self.network.links, 'scalar', res_type='LINK')
        self.export_parameters_using_attributes(self.network.links, 'descriptor', res_type='LINK')
        self.export_timeseries_using_attributes(self.network.links,  res_type='LINK')
        self.export_arrays(self.network.links)
        #
    def export_parameters_using_types(self, resources, obj_type, datatype, res_type=None):
        """Export scalars or descriptors.        """
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
                    if attr is None or attr.value is None or  attr.dataset_type != datatype:
                        continue
                    if(res_type is None):
                        name=resource.name
                    elif islink is True and self.links_as_name is False:
                        name=get_link_name_for_param(resource)
                    else:
                        name=""

                    #self.output_file_contents.append("\n "+name+"  "+str(attr.value.values()[0][0]))
                    contents.append("\n "+self.ff.format(name)+self.ff.format(str(attr.value)))
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
                    if attr is None or attr.value is None or  attr.dataset_type != datatype:
                        continue
                    if res_type is None:
                        name=resource.name
                    elif islink is True and self.links_as_name is False:
                            name=get_link_name_for_param(resource)
                    else:
                        name=""

                    #self.output_file_contents.append("\n "+name+"  "+str(attr.value.values()[0][0]))
                    contents.append("\n "+self.ff.format(name)+self.ff.format(str(attr.value)))
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
                    if(self.time_index is None):
                         raise HydraPluginError("Missing time axis or start date, end date and time step or bad format")


                    attr.name = translate_attr_name(attr.name)
                    if attr.name not in attr_names:
                        attrb_tables[attr.name]=attr
                        attributes.append(attr)
                        attr_names.append(attr.name)

        if len(attributes) > 0:
            dataset_ids = []
            all_res_data={}

            #Identify the datasets that we need data for
            for attribute in attributes:
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is  None or attr.dataset_id is None:
                        continue
                    dataset_ids.append(attr.dataset_id)
                    value=json.loads(attr.value)
                    all_res_data[attr.dataset_id]=value


            #We need to get the value at each time in the specified time axis,
            #so we need to identify the relevant timestamps.
            soap_times = []
            for t, timestamp in enumerate(self.time_index.values()):
                soap_times.append(date_to_string(timestamp))

            #Get all the necessary data for all the datasets we have.
            #all_data = self.connection.call('get_multiple_vals_at_time',
            #                            {'dataset_ids':dataset_ids,
            #                             'timestamps' : soap_times})


            for attribute in attributes:
                self.output_file_contents.append("\nparam "+attribute.name+"_"+obj_type+":\n")
                self.output_file_contents.append(self.write_time())
                for resource in resources:
                    name=resource.name
                    if islink is True and self.links_as_name is False:
                        name=get_link_name(resource)
                    #self.output_file_contents.append("\n  "+name)
                    nname="\n  "+name
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is None or attr.dataset_id is  None or attr.dataset_type != 'timeseries':
                        continue
                    try:
                        all_data = self.get_time_value(attr.value, self.time_index.values())
                    except Exception, e:
                        log.exception(e)
                        all_data = None

                    if all_data is None:
                        raise HydraPluginError("Error finding value attribute %s on"
                                              "resource %s"%(attr.name, resource.name))
                    self.output_file_contents.append(self.ff.format(nname))

                    for timestamp in self.time_index.values():
                        tmp = all_data[timestamp]

                        if isinstance(tmp, list):
                            data="-".join(tmp)
                            ff_='{0:<'+self.array_len+'}'
                            data_str = ff_.format(str(data))
                        else:
                            data=str(tmp)
                            data_str = self.ff.format(str(float(data)))
                        self.output_file_contents.append(data_str)

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
                    if(len(self.time_index) is 0):
                         raise HydraPluginError("Missing time axis or start date, end date and time step or bad format")
                    attr.name = translate_attr_name(attr.name)
                    if attr.name not in attr_names:
                        attrb_tables[attr.name]=attr
                        attributes.append(attr)
                        attr_names.append(attr.name)

        if len(attributes) > 0:
            dataset_ids = []
            all_res_data={}

            #Identify the datasets that we need data for
            for attribute in attributes:
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is not None and attr.dataset_id is not None:
                        dataset_ids.append(attr.dataset_id)
                        value=json.loads(attr.value)
                        all_res_data[attr.dataset_id]=value

            #We need to get the value at each time in the specified time axis,
            #so we need to identify the relevant timestamps.
            soap_times = []
            for t, timestamp in enumerate(self.time_index.values()):
                soap_times.append(date_to_string(timestamp))

            #Get all the necessary data for all the datasets we have.
            #all_data = self.connection.call('get_multiple_vals_at_time',
             #                           {'dataset_ids':dataset_ids,
              #                           'timestamps' : soap_times})

            for attribute in attributes:
                self.output_file_contents.append("\nparam "+attribute.name+":\n")
                self.output_file_contents.append(self.write_time())
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is None or attr.dataset_id is  None or attr.dataset_type != 'timeseries':
                        continue

                    try:
                        all_data = self.get_time_value(attr.value, self.time_index.values())
                    except Exception, e:
                        log.exception(e)
                        all_data = None

                    if all_data is None:
                        raise HydraPluginError("Error finding value attribute %s on"
                                              "resource %s"%(attr.name, resource.name))

                    name=resource.name
                    if islink is True and self.links_as_name is False:
                        name=get_link_name(resource)
                    #self.output_file_contents.append("\n  "+name)
                    nname="\n  "+name;
                    self.output_file_contents.append(self.ff.format(nname))

                    for timestamp in self.time_index.values():
                        tmp = all_data[timestamp]

                        if isinstance(tmp, list):
                            data="-".join(tmp)
                            ff_='{0:<'+self.array_len+'}'
                            data_str = ff_.format(str(data))
                        else:
                            data=str(tmp)
                            data_str = self.ff.format(str(float(data)))
                        self.output_file_contents.append(data_str)


                self.output_file_contents.append(';\n')

    def get_time_value(self, value, timestamps):
        '''
            get data for timesamp

            :param a JSON string
            :param a timestamp or list of timestamps (datetimes)
            :returns a dictionary, keyed on the timestamps provided.
            return None if no data is found
        '''
        converted_ts = reindex_timeseries(value, timestamps)

        #For simplicity, turn this into a standard python dict with
        #no columns.
        value_dict = {}

        val_is_array = False
        if len(converted_ts.columns) > 1:
            val_is_array = True

        if val_is_array:
            for t in timestamps:
                value_dict[t] = converted_ts.loc[t].values.tolist()
        else:
            first_col = converted_ts.columns[0]
            for t in timestamps:
                value_dict[t] = converted_ts.loc[t][first_col]

        return value_dict
    def old_get_time_value(self, value, soap_time):
        '''
        get data for timesamp
        return None if no data is found
        '''
        data=None
        self.set_time_table(value.keys())
        soap_datetime = self.parse_date(soap_time)
        for date_time, item_value in value.items():
            if date_time.startswith("9999") or date_time.startswith('XXXX'):
                #copy the year from the soap time and put it as the first 4
                #characters of the seasonal datetime.
                value_datetime = self.parse_date(soap_time[0:4]+date_time[4:])
                if (value_datetime) == (soap_datetime):
                    data=item_value
                    break
            elif date_time==soap_time:
                data=item_value
                break
            else:
                if self.time_table[date_time]== soap_time:
                     data=item_value
                     break
                else:
                    pass
        if data is None:
            date=self.check_time( soap_time, sorted(value.keys()))
            if date is not None:
                data= value[date]
        if data is not None:
            if type(data) is list:
                new_data="["
                for v in data:
                    if new_data== "[":
                        new_data=new_data+str(v)
                    else:
                        new_data=new_data+" "+str(v)
                data=new_data+"]"
        return data

    def parse_date(self, date):
        """Parse date string supplied from the user. All formats supported by
        HydraLib.PluginLib.guess_timefmt can be used.
        """
        # Guess format of the string
        FORMAT = guess_timefmt(date)
        return datetime.strptime(date, FORMAT)


    def check_time(self, timestamp, times, key=None):
        '''
        check time
        if the timestamp is before the the earliest date
        it will retunn None
        '''
        for i in range (0, len(times)):
            if i==0:
                if parse(timestamp)<parse(self.time_table[times[0]]):
                     return None
            elif parse(timestamp)<parse(self.time_table[times[i]]):
                if  parse(timestamp)>parse(self.time_table[times[i-1]]):
                    return times[i-1]
        if(key is None):
            return self.get_last_valid_occurrence(timestamp, times)

    def get_last_valid_occurrence(self, timestamp, times):
        '''
        get the last occurrence
        '''
        for date_time in times:
            if self.time_table[date_time][5:] == timestamp[5:]:
                return date_time

        for date_time in times:
                time=self.time_table[date_time][:5]+timestamp  [5:]
                re_time=self.check_time(time,times, 0)
                if re_time is not None:
                    return re_time
        return None


    def set_time_table(self, times):
         for date_time in times:
             if  date_time in self.time_table:
                 pass
             else:
                 if date_time.startswith("XXXX"):
                     self.time_table[date_time]=date_to_string(parse(date_time.replace("XXXX","1900")))
                 elif date_time.startswith("9999"):
                     self.time_table[date_time]=date_to_string(parse(date_time.replace("9999","1900")))
                 else:
                     self.time_table[date_time]=date_to_string(parse(date_time))

    def write_time(self):
        '''
        Write time index to a string and returned to be witten in the input file
        '''
        time_string=self.ff.format("")
        for t in self.time_index.keys():
            time_string+=(self.ff.format(str(t)))
        time_string+=(':=')
        return time_string


    def get_time_index(self, start_time=None, end_time=None, time_step=None,
                         time_axis=None):
        '''
        get time index using either time axis provided or start, end time and time step
        '''
        try:
            log.info("Writing time index")
            time_axis = self.get_time_axis(start_time,
                                  end_time,
                                  time_step,
                                  time_axis=time_axis)
            t = 1
            for timestamp in time_axis:
                    self.time_index[t]=timestamp
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

    def get_dim(self, arr):
        dim = []
        if(type(arr) is list):
            for i in range(len(arr)):
                if(type(arr[i]) is list):
                    dim.append((len(arr[i])))
                else:
                    dim.append(len(arr))
                    break
        else:
             dim.append(len(arr))
        return dim

    def export_arrays(self, resources):
        """Export arrays.
        """
        attributes = []
        attr_names = []
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == 'array' and attr.is_var is False:
                    attr.name = translate_attr_name(attr.name)
                    if attr.name not in attr_names:
                        attributes.append(attr)
                        attr_names.append(attr.name)
        if len(attributes) > 0:
            # We have to write the complete array information for every single
            # node, because they might have different sizes.
            for resource in resources:
                # This exporter only supports 'rectangular' arrays
                for attribute in attributes:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is not None and attr.value is not None:
                        array=json.loads(attr.value)
                        dim = self.get_dim(array)
                        self.output_file_contents.append('# Array %s for node %s, ' % \
                            (attr.name, resource.name))
                        self.output_file_contents.append('dimensions are %s\n\n' % dim)
                        # Generate array indices
                        #self.output_file_contents.append('SETS:=\n\n')
                        indexvars = list(ascii_lowercase)
                        for i, n in enumerate(dim):
                            self.output_file_contents.append("set "+ indexvars[i] + '_' + \
                                resource.name + '_' + attr.name + \
                                '_'+str(i)+':=\n')
                            for idx in range(n):
                                self.output_file_contents.append(str(idx) + '\n')
                            self.output_file_contents.append(';\n\n')

                        self.output_file_contents.append('param ' + resource.name + '_' + \
                            attr.name + ':=')

                        ydim = dim[-1]

                        if len(dim)>1:
                            for y in range(ydim):
                                self.output_file_contents.append('{0:20}'.format(y))
                            self.output_file_contents.append('\n')

                        i=0
                        count=0
                        for item in array:
                            self.output_file_contents.append("\n")
                            self.output_file_contents.append('{0:20}'.format(""))
                            if(type(item) is list):
                                self.output_file_contents.append(format('['+str(i)+','+str(i)+']'))
                                i+=1
                                for value in item:
                                    self.output_file_contents.append(' {0:20}'.format(value))
                            else:
                                i+=1
                                self.output_file_contents.append('{0:20}'.format(item))
                            count+=1
                        self.output_file_contents.append(';\n')
                        self.output_file_contents.append('\n\n')

















