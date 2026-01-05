import logging

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s.%(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)

from eds_pie.eds_pie import CIP_EDS, __version__
from eds_pie.cip_eds_types import *

with open('demo.eds', 'rb') as srcfile:
    eds_content = srcfile.read()

print("eds_pie v{}".format(__version__))

eds = CIP_EDS(eds_content)
print("EDS Protocol: {}".format(eds.protocol or "Generic"))

# Extracting required information to establish a connection between client and server
trigger_transprot = eds.get_value("Connection Manager", "Connection1", 0)
connection_parameters = eds.get_value("Connection Manager", "Connection1", 1)
o2t_rpi_ref = eds.get_value("Connection Manager", "Connection1", 2)
o2t_format_ref = eds.get_value("Connection Manager", "Connection1", 4)
t2o_rpi_ref = eds.get_value("Connection Manager", "Connection1", 5)
t2o_format_ref = eds.get_value("Connection Manager", "Connection1", 7)

o2t_fixed_size = connection_parameters & 1
o2t_transfer_format = connection_parameters & 0x700

param = eds.get_entry("Params", o2t_rpi_ref)
o2t_rpi_min = param.get_value(9)
o2t_rpi_max = param.get_value(10)
o2t_rpi_default = param.get_value(11)

assem = eds.get_entry("Assembly", o2t_format_ref)
o2t_path = assem.get_value(1)
o2t_size = assem.get_value(2)

print("O->T:  RPI: {}uS, data path: {}, data size: {} byte(s)".format(o2t_rpi_default, o2t_path, o2t_size))

t2o_fixed_size = connection_parameters & 4
t2o_transfer_format = connection_parameters & 0x7000

param = eds.get_entry("Params", t2o_rpi_ref)
t2o_rpi_min = param.get_value(9)
t2o_rpi_max = param.get_value(10)
t2o_rpi_default = param.get_value(11)

assem = eds.get_entry("Assembly", t2o_format_ref)
t2o_path = assem.get_value(1)
t2o_size = assem.get_value(2)

print("T->O:  RPI: {}uS, data path: {}, data size: {} byte(s)".format(t2o_rpi_default, t2o_path, t2o_size))

