#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import argparse
from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET

import pandas as pd

from parse_ctd_911xmlcon import parse_xmlcon


class Sensor(object):
    def __init__(self, sensorid):
        self.id = sensorid
        self.ordinal = None
        self.calcid = None
        self.unitid = None
        self.coeffs = None

    def set_coeffs(self, coeffs):
        self.coeffs = coeffs

    def set_ordinal(self, sensors, index):
        # count if we've seen this sensor before
        self.ordinal = sensors[:index].count(self.id)

    def set_output_variables(self, variables):
        # retrieve all CalcID and UnitID for each sensor type
        v = variables.loc[variables["SensorID"] == self.id, ["CalcID", "UnitID"]]
        self.calcid = v["CalcID"].to_list()
        self.unitid = v["UnitID"].to_list()


def load_xml(infile):
    tree = ET.parse(infile)
    return tree


def main():
    parser = argparse.ArgumentParser(description="""Parses a SBE911 CTD configuration
                                     from its XMLCON file, and generates a DataConversion
                                     PSA setup file.""")
    parser.add_argument('infile', type=str,
                        help='path to the XMLCON file')
    parser.add_argument('-o', '--outdir', dest='outdir', type=str,
                        default='psa',
                        help='directory to save output files (default: ./psa)')
    args = parser.parse_args()
    if not args.infile:
        parser.print_help()
        return

    infile = Path(args.infile)
    outdir = Path(args.outdir)

    # Test for output directory...
    outdir.mkdir(exist_ok=True)

    # Get castid
    castid = infile.stem

    # reference table to match sensorID with all associated CalcIDs and UnitIDs
    variables_ref = pd.read_csv('variables_r2r_sbe911.csv')

    # load the psa template
    psa = load_xml('default.psa')
    calcarray = psa.getroot().find('.//CalcArray')

    # load the sensor reference template
    sensor_root = load_xml('sensors_all.xml').getroot()

    # parse the xmlcon file to get sensorID list and coeffs as needed
    cast = parse_xmlcon(infile)
    xmlcon_sensors = [int(sensor['SensorID']) for sensor in cast.data.sensors]

    # Add lat/lon first
    item = sensor_root.find(".//*[@CalcID='39']")
    item.set('index', '0')
    calcarray.append(item)
    item = sensor_root.find(".//*[@CalcID='40']")
    item.set('index', '1')
    calcarray.append(item)
    index = 2

    # Add sensors
    for i, sensorid in enumerate(xmlcon_sensors):
        if sensorid == 27:
            # skip over unused slots (id 27 is "Free")
            continue
        sensor = Sensor(sensorid)
        sensor.set_ordinal(xmlcon_sensors, i)
        sensor.set_output_variables(variables_ref)
        for ii, calcid in enumerate(sensor.calcid):
            item = sensor_root.find(".//*[@UnitID='%s']..[@CalcID='%s']" % (sensor.unitid[ii], calcid))
            item = deepcopy(item)
            item.set('index', str(index))
            item.find('Calc').set('Ordinal', str(sensor.ordinal))
            fullname = item.find('Calc/FullName')
            if sensor.ordinal == 0:
                fullname.set('value', fullname.attrib['value'].replace('$ordinal', ''))
            else:
                fullname.set('value', fullname.attrib['value'].replace('$ordinal', ', %s' % str(sensor.ordinal + 1)))
            if sensor.id == 80:  # user exponential have special names
                usrexpname = cast.cal_coeffs[str(i)].coeffs.SensorName
                usrexpunits = cast.cal_coeffs[str(i)].coeffs.SensorUnits
                if usrexpname is not None:
                    fullname.set('value', 'Uexpo %s, %s [%s]' % (sensor.ordinal + 1, usrexpname, usrexpunits))
                    item.find('Calc/CalcName').set('value', usrexpname)
                    item.find('Calc/CalcUnits').set('value', usrexpunits)
                else:
                    fullname.set('value', 'User Exponential, %s' % (sensor.ordinal + 1))
                    item.find('Calc/CalcName').set('value', '')
                    item.find('Calc/CalcUnits').set('value', '')
            if sensor.id == 61:  # user polynomial have special names
                usrpolyname = cast.cal_coeffs[str(i)].coeffs.SensorName
                if usrpolyname is not None:
                    fullname.set('value', 'Upoly %s, %s' % (sensor.ordinal + 1, usrpolyname))
                    item.find('Calc/CalcName').set('value', usrpolyname)
                else:
                    fullname.set('value', 'User Polynomial, %s' % (sensor.ordinal + 1))
                    item.find('Calc/CalcName').set('value', '')
            calcarray.append(item)
            index += 1

    # Add pumps last
    item = sensor_root.find(".//*[@CalcID='69']")
    item.set('index', str(index))
    calcarray.append(item)

    # update array size
    calcarray.set('Size', str(len(calcarray)))

    # write out PSA
    outfile = Path(outdir, '%s.psa' % castid)
    psa.write(outfile, xml_declaration=True, encoding='UTF-8')

if __name__ == '__main__':
    main()
