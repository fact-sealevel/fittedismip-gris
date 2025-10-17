# fittedismip-gris

This module implementes the parametric fit to ISMIP6 Greenland Ice Sheet projections described in IPCC AR6 WG1 9.SM.4.4. As described therein:

A polynomial fit to the ISMIP6 results is employed to calculate rates of change. The parametric fit is a cubic fit to temperature and a quadratic fit over time:

$$ 𝜕𝑠/𝜕𝑡 =𝛽_0 +𝛽_1𝑇+𝛽_2𝑇^2+𝛽_3𝑇^3+𝛽_4𝑡+𝛽_5𝑡^2 $$

Where $s$ indicates the sea-level equivalent contribution in mm, $T$ is GSAT in °C, and $t$ is time in years. For the purposes of fitting this function, T and t are anomalies to their respective values in year 2015. Fitting is done using maximum a posteriori estimation.

>[!CAUTION]
> This is a prototype. It is likely to change in breaking ways. It might delete all your data. Don't use it in production.

## Example

### Setup

Clone the repository and create directories to hold input and output data. 

```shell
#git clone git@github.com:fact-sealevel/fittedismip-gris.git
# ^^ eventually, for now clone:
git clone --single-branch --branch package git@github.com:e-marshall/fittedismip-gris.git
```

Download input data using the following Zenodo records:

```shell
# Input data we will pass to the container
mkdir -p ./data/input
curl -sL https://zenodo.org/record/7478192/files/FittedISMIP_icesheet_fit_data.tgz | tar -zx -C ./data/input
# Fingerprint input data for postprocessing step
curl -sL https://zenodo.org/record/7478192/files/grd_fingerprints_data.tgz | tar -zx -C ./data/input

echo "New_York	12	40.70	-74.01" > ./data/input/location.lst

# Output projections will appear here
mkdir -p ./data/output
```

From the root directory, create a docker image that we will use to run the application:
```shell
docker build -t fittedismip-gris .
```

Create a container based on the image (`docker run --rm`), mount volumes for both the input and output data sub-directories and set the working directory to the location of the app in the container (`-w`). Then, call the application, passing the desired input arguments and making sure that the paths for each input argument are relative to the mounted volumes. Replace the paths for each mounted volume with the location of `data/input/` and `data/output/` on your machine.

>[!IMPORTANT]
> This module **requires** a `climate.nc` file that is the output of the FACTS FAIR module, which is created outside of this prototype. Before running the example, manually move the file into `./data/input` and ensure that the filename matches that passed to `climate-file`. The number of samples (`--nsamps`) drawn in the FAIR run must pass the number of samples specified in this run (default = 200). 


```shell
docker run --rm \
-v /path/to/data/input:/mnt/fittedismip_gris_data_input:ro \
-v /path/to/data/output:/mnt/fittedismip_gris_data_out \
ghcr.io/fact-sealevel/fittedismip-gris:edge \
--climate-file /mnt/fittedismip_gris_data_input/climate.nc \
--gris-parm-file /mnt/fittedismip_gris_data_input/FittedParms_GrIS_ALL.csv \
--wais-parm-file /mnt/fittedismip_gris_data_input/FittedParms_AIS_WAIS.csv \
--eais-parm-file /mnt/fittedismip_gris_data_input/FittedParms_AIS_EAIS.csv \
--pen-parm-file /mnt/fittedismip_gris_data_input/FittedParms_AIS_PEN.csv \
--gris-global-out-file /mnt/fittedismip_gris_data_out/gris_gslr.nc \
--gris-local-out-file /mnt/fittedismip_gris_data_out/gris_lslr.nc \
--locationfile /mnt/fittedismip_gris_data_input/location.lst \
--fp-dir /mnt/fittedismip_gris_data_input/FPRINT
```

## Features

```shell
Usage: fittedismip-gris [OPTIONS]

Options:
  --scenario TEXT              Emissions scenario of interest.  [default:
                               ssp585]
  --tlm-flag INTEGER           Use two-layer model temperature trajectories
                               [default = 1, do not use]  [default: 1]
  --climate-file TEXT          NetCDF4/HDF5 file containing surface
                               temperature data  [required]
  --pipeline-id TEXT           Unique identifier for this instance of the
                               module
  --gris-parm-file TEXT        File containing Greenland ice sheet model
                               parameters  [required]
  --wais-parm-file TEXT        File containing West Antarctic ice sheet model
                               parameters  [required]
  --eais-parm-file TEXT        File containing East Antarctic ice sheet model
                               parameters  [required]
  --pen-parm-file TEXT         File containing Antarctic Peninsula ice sheet
                               model parameters  [required]
  --nsamps INTEGER             Number of samples to draw  [default: 200]
  --pyear-start INTEGER        Projection start year  [default: 2020]
  --pyear-end INTEGER          Projection end year  [default: 2300]
  --pyear-step INTEGER         Projection year step  [default: 10]
  --cyear-start INTEGER        Constant rate calculation for projections
                               starts at this year
  --cyear-end INTEGER          Constant rate calculation for projections ends
                               at this year  [default: 2100]
  --baseyear INTEGER           Year to which projections are referenced
                               [default: 2005]
  --rngseed INTEGER            Random number generator seed  [default: 1234]
  --locationfile TEXT          File that contains name, id, lat, and lon of
                               points for localization
  --chunksize INTEGER          Number of locations to process at a time
                               [default: 50]
  --fp-dir TEXT                Directory that contains fingerprint files
  --gris-global-out-file TEXT  File name for global Greenland ice sheet
                               projections
  --gris-local-out-file TEXT   File name for local Greenland ice sheet
                               projections
  --help                       Show this message and exit.
```

See this help documentation by passing the `--help` flag when running the application, for example:

```shell
docker run --rm fittedismip-gris --help
```

## Build the container locally
You can build the container with Docker by running the following command from the repository root:

```shell
docker build -t deconto21-ais .
```

## Results
If this module runs successfully, two netCDF files containing projections of local and global sea level change due to contributions from the Greenland Ice Sheet will appear in `./data/output`.

## Support 
Source code is available online at https://github.com/fact-sealevel/fittedismip-gris. This software is open source, available under the MIT license.

Please file issues in the issue tracker at https://github.com/fact-sealevel/fittedismip-gris/issues.
