"""
Parses XML configuration files for Sea-Bird 911 CTD instruments.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

from munch import Munch, munchify


class Parameters(object):
    """Simple class to store parsed parameter names.
    """

    def __init__(self, parameters):
        self.parameters = parameters

    def create_dict(self):
        """
        Create a Munch class object to store parameter names.
        """
        munch = Munch()

        for name in self.parameters:
            munch[name] = []

        return munch


class ParserCommon(object):
    """
    Base class to prepare a calibration or data file for parsing by an individual
    instrument-specific subclass.
    """
    def __init__(self, infile, parameters=None):
        """
        Initialize with the input file and parameter names.
        """
        self.infile = infile
        if parameters is not None:
            data = Parameters(parameters)
            self.data = data.create_dict()
        else:
            self.data = None
        self.raw = None

    def load_ascii(self):
        """
        Create a buffered data object by opening the data file and reading in
        the contents
        """
        with open(self.infile, 'r') as f:
            self.raw = f.readlines()

    def load_xml(self):
        tree = ET.parse(self.infile)
        root = tree.getroot()
        self.raw = root


class Parser(ParserCommon):
    """
    Extension of base parser class to parse instrument-specific metadata
    and calibration coefficients from a Sea-Bird 911 xmlcon file.
    Includes methods to export configs and coeffs to JSON.
    """
    def __init__(self, infile):
        parameter_names = ['frequency_channels_sup',
                           'voltage_channels_sup',
                           'has_surfacepar',
                           'has_nmea_latlon',
                           'has_nmea_depth',
                           'has_nmea_time',
                           'has_time',
                           'sensors']
        self.cal_coeffs = Munch()
        super().__init__(infile, parameter_names)

    def parse_xml(self):
        instrument = self.raw[0]
        self.data.frequency_channels_sup = instrument.find('FrequencyChannelsSuppressed').text
        self.data.voltage_channels_sup = instrument.find('VoltageWordsSuppressed').text
        self.data.has_surfacepar = instrument.find('SurfaceParVoltageAdded').text
        self.data.has_nmea_latlon = instrument.find('NmeaPositionDataAdded').text
        self.data.has_nmea_depth = instrument.find('NmeaDepthDataAdded').text
        self.data.has_nmea_time = instrument.find('NmeaTimeAdded').text
        self.data.has_time = instrument.find('ScanTimeAdded').text
        self.data.sensors = [sensor.attrib for sensor in self.raw.iter('Sensor')]

    def parse_cal_coeffs(self):
        sensors = self.raw.findall('.//Sensor')
        for sensor in sensors:
            sensor_dict = nested_dict_from_xml(sensor, dict())
            sensor_type, sensor_coeffs = [item for item in sensor_dict.items()].pop()
            self.cal_coeffs[sensor.attrib['index']] = munchify({'sensor': sensor_type,
                                                                'coeffs': sensor_coeffs})

    def config_to_json(self, outdir, cast_no):
        outfile = Path(outdir, '%s_config.json' % cast_no)
        with open(outfile, 'w') as f:
            f.write(self.data.toJSON())

    def coeffs_to_json(self, outdir, cast_no):
        outfile = Path(outdir, '%s_coeffs.json' % cast_no)
        with open(outfile, 'w') as f:
            f.write(self.cal_coeffs.toJSON())


def nested_dict_from_xml(p, d):
    """
    Helper function for recursively parsing XML child elements into a nested
    dictionary.

    :param p: object: XML Tree iterable "parent" object
    :param d: dict
    :return: dict
    """
    for c in p:
        if not c:
            # Parent has no children, get element text and continue...
            d[c.tag] = c.text
        else:
            # Parent has a child element, call this function on a new empty
            # dict with the child now the parent...
            d[c.tag] = nested_dict_from_xml(c, dict())
    return d


def parse_xmlcon(infile):
    """
    Function to parse a single xmlcon file and return the Parser object

    :param infile: path of input file
    :return: Parser object
    """
    p = Path(infile)
    # cast_no = p.stem
    cast = Parser(p)
    cast.load_xml()
    cast.parse_xml()
    cast.parse_cal_coeffs()
    return cast


def get_sensors(infile):
    """
    Function to parse an XMLCON file and return only the list of sensorIDs.

    :param infile: path of input file
    :return:
    """
    cast = parse_xmlcon(infile)
    return cast.data.sensors
