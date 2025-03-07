# README

## r2r_tools

- `r2r_xmlcon_to_psa.py`: A Python utility to generate a SBE DataConversion program setup (PSA) file from a SBE 911 XMLCON configuration file.
- A SBE BinAverage PSA file to process converted SBE 911 data in 1 db pressure bins.
- A batch script file for use with the SBEBatch utility for Windows to automate the generation of full-resolution and binned converted data files.
- Reference files and templates:
  - `default.psa`: template DataConversion PSA file.
  - `sensors_all.xml`: sensor/variable array elements for building up the DataConversion template.
  - `variables_r2r_sbe911.csv`: magic lookup table for mapping XMLCON file elements to the corresponding PSA file elements.

## TODO

- Use outputs of R2R QA process to make a list of casts to process.
- Shell script to automate the Python PSA generator and to run SBEBatch data processing.

## r2r_xmlcon_to_psa.py

### Usage

`r2r_xmlcon_to_psa.py [-h] [-o OUTDIR] infile`

- infile: Path to XMLCON configuration file
- outdir: Output directory for generated PSA file. Defaults to `./psa`.

## parse_ctd_911xmlcon.py

Parses an XMLCON configuration file. Required XMLCON components are a list of SensorIDs as integers, and calibration coefficients as a nested munch object (dictionary).

This is adapted from code I wrote several years ago and used here as it was readily available. I have included it to get this project up and running as quickly as possible.

It may be retained here, or it may optionally be replaced with other new or existing code providing comparable functionality.