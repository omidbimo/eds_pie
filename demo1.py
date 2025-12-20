import logging

logging.basicConfig(level=logging.WARNING,
    format='%(asctime)s - %(name)s.%(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)

from eds_pie import CIP_EDS

with open('demo.eds', 'rb') as srcfile:
    eds_content = srcfile.read()

eds = CIP_EDS(eds_content)

#eds.list()
print(eds)
