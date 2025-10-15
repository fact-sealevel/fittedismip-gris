from fittedismip_gris.FittedISMIP_GrIS_preprocess import (
    FittedISMIP_preprocess_icesheet,
)
from fittedismip_gris.FittedISMIP_GrIS_fit import (
    FittedISMIP_fit_icesheet,
)
from fittedismip_gris.FittedISMIP_GrIS_project import (
    FittedISMIP_project_icesheet,
)
from fittedismip_gris.FittedISMIP_GrIS_postprocess import (
    FittedISMIP_postprocess_icesheet,
)

import click


@click.command()
@click.option(
    "--scenario",
    envvar="FITTEDISMIP_GRIS_SCENARIO",
    default="ssp585",
    help="Emissions scenario of interest.",
    show_default=True,
    type=str,
)
@click.option(
    "--tlm-flag",
    envvar="FITTEDISMIP_GRIS_TLM_FLAG",
    default=1,  # this means do not use.
    help="Use two-layer model temperature trajectories [default = 1, do not use]",
    show_default=True,
    type=int,
)
@click.option(
    "--climate-file",
    envvar="FITTEDISMIP_GRIS_CLIMATE_FILE",
    required=True,  # true for now and must be a fair climate.nc
    help="NetCDF4/HDF5 file containing surface temperature data",
    type=str,
)
@click.option(
    "--pipeline-id",
    type=str,
    help="Unique identifier for this instance of the module",
    envvar="FITTEDISMIP_GRIS_PIPELINE_ID",
)
@click.option(
    "--gris-parm-file",
    type=str,
    help="File containing Greenland ice sheet model parameters",
    envvar="FITTEDISMIP_GRIS_GRIS_PARMS",
    required=True,
)
@click.option(
    "--wais-parm-file",
    type=str,
    help="File containing West Antarctic ice sheet model parameters",
    envvar="FITTEDISMIP_GRIS_WAIS_PARMS",
    required=True,
)
@click.option(
    "--eais-parm-file",
    type=str,
    help="File containing East Antarctic ice sheet model parameters",
    envvar="FITTEDISMIP_GRIS_EAIS_PARMS",
    required=True,
)
@click.option(
    "--pen-parm-file",
    type=str,
    help="File containing Antarctic Peninsula ice sheet model parameters",
    envvar="FITTEDISMIP_GRIS_PEN_PARMS",
    required=True,
)
@click.option(
    "--nsamps",
    type=int,
    default=200,
    help="Number of samples to draw",
    envvar="FITTEDISMIP_GRIS_NSAMPS",
    show_default=True,
)
@click.option(
    "--pyear-start",
    envvar="FITTEDISMIP_GRIS_PYEAR_START",
    default=2020,
    help="Projection start year",
    show_default=True,
    type=int,
)
@click.option(
    "--pyear-end",
    envvar="FITTEDISMIP_GRIS_PYEAR_END",
    default=2300,  # following experiments config in f1
    help="Projection end year",
    show_default=True,
    type=int,
)
@click.option(
    "--pyear-step",
    envvar="FITTEDISMIP_GRIS_PYEAR_STEP",
    default=10,
    help="Projection year step",
    show_default=True,
    type=int,
)
@click.option(
    "--cyear-start",
    envvar="FITTEDISMIP_GRIS_CYEAR_START",
    help="Constant rate calculation for projections starts at this year",
    required=False,
    type=int,
)
@click.option(
    "--cyear-end",
    envvar="FITTEDISMIP_GRIS_CYEAR_END",
    help="Constant rate calculation for projections ends at this year",
    default=2100,  # following defaults in f1 project script. note, this is required to match f1 experiment results
    show_default=True,
    type=int,
)
@click.option(
    "--baseyear",
    envvar="FITTEDISMIP_GRIS_BASEYEAR",
    help="Year to which projections are referenced",
    default=2005,
    show_default=True,
    type=int,
)
@click.option(
    "--rngseed",
    envvar="FITTEDISMIP_GRIS_RNGSEED",
    help="Random number generator seed",
    default=1234,
    show_default=True,
    type=int,
)
@click.option(
    "--locationfile",
    type=str,
    help="File that contains name, id, lat, and lon of points for localization",
    envvar="FITTEDISMIP_GRIS_LOCATIONFILE",
)
@click.option(
    "--chunksize",
    type=int,
    default=50,
    show_default=True,
    help="Number of locations to process at a time",
    envvar="FITTEDISMIP_GRIS_CHUNKSIZE",
)
@click.option(
    "--fp-dir",
    envvar="FITTEDISMIP_GRIS_FP_DIR",
    help="Directory that contains fingerprint files",
    type=str,
)
@click.option(
    "--gris-global-out-file",
    envvar="FITTEDISMIP_GRIS_GLOBAL_OUT_FILE",
    help="File name for global Greenland ice sheet projections",
    type=str,
)
@click.option(
    "--gris-local-out-file",
    envvar="FITTEDISMIP_GRIS_LOCAL_OUT_FILE",
    help="File name for local Greenland ice sheet projections",
    type=str,
)
def main(
    scenario,
    tlm_flag,
    climate_file,
    pipeline_id,
    gris_parm_file,
    wais_parm_file,
    eais_parm_file,
    pen_parm_file,
    nsamps,
    pyear_start,
    pyear_end,
    pyear_step,
    cyear_start,
    cyear_end,
    baseyear,
    rngseed,
    locationfile,
    chunksize,
    fp_dir,
    gris_global_out_file,
    gris_local_out_file,
):
    click.echo("Hello from FittedISMIP-GrIS!")
    # Preprocess
    preprocess_dict = FittedISMIP_preprocess_icesheet(
        scenario=scenario,
        tlm_flag=tlm_flag,
        pipeline_id=pipeline_id,
        climate_file=climate_file,
    )

    # Fit
    fit_dict = FittedISMIP_fit_icesheet(
        pipeline_id=pipeline_id,
        gris_parm_file=gris_parm_file,
        wais_parm_file=wais_parm_file,
        eais_parm_file=eais_parm_file,
        pen_parm_file=pen_parm_file,
    )

    # Project
    project_dict = FittedISMIP_project_icesheet(
        preprocess_dict=preprocess_dict,
        fit_dict=fit_dict,
        nsamps=nsamps,
        pyear_start=pyear_start,
        pyear_end=pyear_end,
        pyear_step=pyear_step,
        cyear_start=cyear_start,
        cyear_end=cyear_end,
        baseyear=baseyear,
        rngseed=rngseed,
        pipeline_id=pipeline_id,
        gris_global_out_file=gris_global_out_file,
    )

    # Postprocess
    FittedISMIP_postprocess_icesheet(
        projection_dict=project_dict,
        locationfile=locationfile,
        chunksize=chunksize,
        pipeline_id=pipeline_id,
        fpdir=fp_dir,
        gris_local_out_file=gris_local_out_file,
    )
