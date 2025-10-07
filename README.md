# fittedismip-gris

This module implemented the parametric fit to ISMIP6 Greenland Ice Sheet projections described in IPCC AR6 WG1 9.SM.4.4. As described therein:

A polynomial fit to the ISMIP6 results is employed to calculate rates of change. The parametric fit is a cubic fit to temperature and a quadratic fit over time:

$$ 𝜕𝑠/𝜕𝑡 =𝛽_0 +𝛽_1𝑇+𝛽_2𝑇^2+𝛽_3𝑇^3+𝛽_4𝑡+𝛽_5𝑡^2 $$

Where $s$ indicates the sea-level equivalent contribution in mm, $T$ is GSAT in °C, and $t$ is time in years. For the purposes of fitting this function, T and t are anomalies to their respective values in year 2015. Fitting is done using maximum a posteriori estimation.

>[!CAUTION]
> This is a prototype. It is likely to change in breaking ways. It might delete all your data. Don't use it in production.

## Example

### Setup

Clone the repository and create directories to hold input and output data. 

```shell
git clone git@github.com:fact-sealevel/fittedismip-gris.git
```

Download input data using the following Zenodo records:

```shell
# Input data we will pass to the container
mkdir -p ./data/input
curl -sL https://zenodo.org/record/7478192/files/FittedISMIP_icesheet_fit_data.tgz | tar -zx -C ./data/input

echo "New_York	12	40.70	-74.01" > ./data/input/location.lst

# Output projections will appear here
mkdir -p ./data/output
```

From the root directory, create a docker image that we will use to run the application:
```shell
docker build -t fittedismip-gris .
```

Create a container based on the image (`docker run --rm`), mount volumes for both the input and output data sub-directories and set the working directory to the location of the app in the container (`-w`). Then, call the application, passing the desired input arguments and making sure that the paths for each input argument are relative to the mounted volumes. Pass a full path for each output file that you would like the program to write. Output objects will only be written to file if a path is passed as an input argument. In the example below, all possible outputs (local and global projections for each ice sheet) are written:
