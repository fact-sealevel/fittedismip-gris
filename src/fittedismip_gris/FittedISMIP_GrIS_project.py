import numpy as np
import argparse
import sys
import os
from netCDF4 import Dataset
import time
import xarray as xr
from scipy.stats import truncnorm

""" FittedISMIP_project_icesheet.py

Runs the FittedISMIP icesheet projection stage.

Parameters:
nsamps              Number of samples to produce
pyear_start			Projection start year
pyear_end			Projection end year
pyear_step			Stepping from projection year start to end
rngseed             Seed for the random number generator
pipeline_id         Unique identifier to attach to this pipeline

Note: 'pipeline_id' is a unique identifier that distinguishes it among other instances
of this module within the same workflow.

"""


def make_projection_ds(icesamps, icetype, data_years, scenario, pipeline_id, baseyear):
    data = np.asarray(icesamps)[:, :, np.newaxis]
    ds = xr.Dataset(
        data_vars={
            "sea_level_change": (
                ("samples", "years", "locations"),
                data,
                {
                    "units": "mm",
                },
            ),
            "lat": (
                ("locations",),
                np.array([np.float32(np.inf)], dtype=np.float32),
            ),
            "lon": (
                ("locations",),
                np.array([np.float32(np.inf)], dtype=np.float32),
            ),
        },
        coords={
            "years": (
                ("years",),
                data_years,
            ),
            "samples": (("samples"), np.arange(icesamps.shape[0])),
            "locations": (
                "locations",
                np.array([-1]),
            ),
        },
        attrs={
            "description": f"Global SLR contribution from {icetype} according to FittedISMIP-gris module workflow",
            "history": "Created " + time.ctime(time.time()),
            "scenario": scenario,
            "baseyear": baseyear,
        },
    )
    return ds


def FittedISMIP_project_icesheet(
    preprocess_dict,
    fit_dict,
    nsamps,
    pyear_start,
    pyear_end,
    pyear_step,
    cyear_start,
    cyear_end,
    baseyear,
    pipeline_id,
    rngseed,
    gris_global_out_file,
):
    years = preprocess_dict["years"]
    temp_data = preprocess_dict["temp_data"]
    scenario = preprocess_dict["scenario"]

    betas_dict = fit_dict["betas_dict"]
    sigmas_dict = fit_dict["sigmas_dict"]
    trend_mean = fit_dict["trend_mean"]
    trend_sd = fit_dict["trend_sd"]

    # Define the target projection years
    targyears = np.arange(pyear_start, pyear_end + 1, pyear_step)

    # Find the data years that overlap with the target projection years
    (_, datayr_idx, targyear_idx) = np.intersect1d(
        years, targyears, return_indices=True
    )

    # Zero out the temperature data to the base year (Fitted models have 0-forced intercept)
    baseyear_idx = np.flatnonzero(years == baseyear)
    if baseyear_idx.size == 0:
        raise ValueError(
            "baseyear is not found in temperature data. baseyear = {}".format(baseyear)
        )
    temp_data = temp_data - temp_data[:, baseyear_idx]

    # Set the seed for the

    rng = np.random.default_rng(rngseed)

    # Initialize the samples dictionary to pass to the post-processing stage
    samps_dict = {}

    # Generate the indices for the temperature samples
    temp_sample_idx = np.arange(nsamps)

    # Generate a list of quantiles for the trend samples
    trend_q = rng.random(nsamps)

    # Loop over the ice sources
    for icesource in ["GIS"]:
        # Calculate the trend contributions over time for this ice sheet component
        ice_trend = (
            truncnorm.ppf(
                trend_q,
                a=0.0,
                b=99999.9,
                loc=trend_mean[icesource],
                scale=trend_sd[icesource],
            )[:, np.newaxis]
            * (targyears - baseyear)[np.newaxis, :]
        )

        # Which model parameters do we need
        betas = betas_dict[icesource]
        sigmas = sigmas_dict[icesource]

        # Generate the indices for the model samples
        model_sample_idx = rng.choice(np.arange(betas.shape[0]), nsamps)

        # Loop over the number of samples we need
        samps = []

        for tidx, midx in zip(temp_sample_idx, model_sample_idx):
            # Generate a sample
            (this_sample, _, _, _) = my_model(
                temp_data[tidx, datayr_idx],
                betas[midx, :],
                sigmas[midx],
                targyears - baseyear,
                pyear_step,
                rng,
            )
            samps.append(this_sample)

        # Convert the sample array into a numpy array
        samps = np.array(samps)

        # Add the trend to the samples
        samps = samps + ice_trend

        # If the user wants to extrapolate projections based on rates, do so here
        if cyear_start or cyear_end:
            for i in np.arange(nsamps):
                samps[i, :] = ExtrapolateRate(
                    samps[i, :], targyears, cyear_start, cyear_end
                )

        # Add the total samples to the samples dictionary
        samps_dict[icesource] = samps

        make_projection_ds(
            samps, icesource, targyears[targyear_idx], scenario, pipeline_id, baseyear
        )
        # Write the global projections to output netCDF files
        gris_ds = make_projection_ds(
            samps,
            icesource,
            targyears[targyear_idx],
            scenario,
            pipeline_id,
            baseyear,
        )
        gris_ds.to_netcdf(gris_global_out_file)

    # Store the variables in a pickle
    output = {
        "samps_dict": samps_dict,
        "scenario": scenario,
        "targyears": targyears[targyear_idx],
        "baseyear": baseyear,
    }

    return output


def ExtrapolateRate(sample, targyears, cyear_start, cyear_end):
    # If only one of the constant rate years is provided, imply the other
    if cyear_start and not cyear_end:
        cyear_end = cyear_start + 20
    if cyear_end and not cyear_start:
        cyear_start = cyear_end - 20

    # Find the start and end projection values for the rate calculation
    proj_start = np.interp(cyear_start, targyears, sample)
    proj_end = np.interp(cyear_end, targyears, sample)

    # Calculate the rate
    rate = (proj_end - proj_start) / (cyear_end - cyear_start)

    # Make a new projection
    ext_sample = sample
    ext_sample[targyears >= cyear_end] = proj_end + (
        rate * (targyears[targyears >= cyear_end] - cyear_end)
    )

    # Return this sample
    return ext_sample


def my_model(temp, beta, sigma, dyears, delta_time, rng):
    # If the last temperature value is nan, replace it with a linear extrapolation
    if np.isnan(temp[-1]):
        temp[-1] = temp[-2] + (temp[-2] - temp[-3])

    # Produce a projection for this temperature trajectory
    # NOTE - The fitted rates are per year, so multiply by delta_time (pyear_step)
    # to produce the sample.
    dsle_hat_const = (np.ones(temp.shape) * beta[0]) * delta_time
    dsle_hat_temp = (
        beta[1] * temp + beta[2] * temp**2 + beta[3] * temp**3
    ) * delta_time
    dsle_hat_time = (beta[4] * dyears + beta[5] * dyears**2) * delta_time

    # Sum up the individual changes over time
    sle_hat_const = np.cumsum(dsle_hat_const)
    sle_hat_temp = np.cumsum(dsle_hat_temp)
    sle_hat_time = np.cumsum(dsle_hat_time)
    sle_hat = sle_hat_temp + sle_hat_time + sle_hat_const

    # Apply the error from the fit to this projection
    spread = (sigma * 0.0) / 100.0
    # spread = 0.75
    pct_error = rng.uniform(-spread, spread)
    sle_hat *= 1 + pct_error

    return (sle_hat, sle_hat_temp, sle_hat_time, sle_hat_const)


def WriteNetCDF(icesamps, icetype, data_years, scenario, pipeline_id, baseyear):
    # Write the total global projections to a netcdf file
    nc_filename = os.path.join(
        os.path.dirname(__file__), "{0}_{1}_globalsl.nc".format(pipeline_id, icetype)
    )
    rootgrp = Dataset(nc_filename, "w", format="NETCDF4")

    # Define Dimensions
    nsamps = icesamps.shape[0]

    # Populate dimension variables
    year_var = rootgrp.createVariable("years", "i4", ("years",))
    samp_var = rootgrp.createVariable("samples", "i8", ("samples",))
    loc_var = rootgrp.createVariable("locations", "i8", ("locations",))
    lat_var = rootgrp.createVariable("lat", "f4", ("locations",))
    lon_var = rootgrp.createVariable("lon", "f4", ("locations",))

    # Create a data variable
    samps = rootgrp.createVariable(
        "sea_level_change",
        "f4",
        ("samples", "years", "locations"),
        zlib=True,
        complevel=4,
    )

    # Assign attributes
    rootgrp.description = "Global SLR contribution from {} according to FittedISMIP icesheet workflow".format(
        icetype
    )
    rootgrp.history = "Created " + time.ctime(time.time())
    rootgrp.source = "FACTS: {0}".format(pipeline_id)
    rootgrp.scenario = scenario
    rootgrp.baseyear = baseyear
    samps.units = "mm"

    # Put the data into the netcdf variables
    year_var[:] = data_years
    samp_var[:] = np.arange(nsamps)
    samps[:, :, :] = icesamps[:, :, np.newaxis]
    lat_var[:] = np.inf
    lon_var[:] = np.inf
    loc_var[:] = -1

    # Close the netcdf
    rootgrp.close()

    return 0


if __name__ == "__main__":
    # Initialize the command-line argument parser
    parser = argparse.ArgumentParser(
        description="Run the FittedISMIP icesheet projection stage.",
        epilog="Note: This is meant to be run as part of the Framework for the Assessment of Changes To Sea-level (FACTS)",
    )

    # Define the command line arguments to be expected
    parser.add_argument(
        "--nsamps", help="Number of samples to draw ", default=10000, type=int
    )
    parser.add_argument(
        "--pyear_start", help="Projection year start ", default=2020, type=int
    )
    parser.add_argument(
        "--pyear_end", help="Projection year end", default=2300, type=int
    )  # prev 2100, in the f1 experiments config this is 2300
    parser.add_argument(
        "--crateyear_start",
        help="Constant rate calculation for projections starts at this year",
        default=None,
        type=int,
    )
    parser.add_argument(
        "--crateyear_end",
        help="Constant rate calculation for projections ends at this year",
        default=2300,
        type=int,
    )  # prev 2100, in the f1 experiments config this is 2300
    parser.add_argument(
        "--pyear_step", help="Projection year step [default=10]", default=10, type=int
    )
    parser.add_argument(
        "--baseyear",
        help="Year to which projections are referenced [default=2005]",
        default=2005,
        type=int,
    )
    parser.add_argument(
        "--seed",
        help="Seed for the random number generator [default = 1234]",
        default=1432,
        type=int,
    )
    parser.add_argument(
        "--pipeline_id", help="Unique identifier for this instance of the module"
    )

    # Parse the arguments
    args = parser.parse_args()

    # Run the projection stage with the provided arguments
    FittedISMIP_project_icesheet(
        args.nsamps,
        args.pyear_start,
        args.pyear_end,
        args.pyear_step,
        args.crateyear_start,
        args.crateyear_end,
        args.baseyear,
        args.pipeline_id,
        args.seed,
    )

    sys.exit()
