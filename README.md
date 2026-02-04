# ORACLE
I present a neural temporal point process (NTPP) framework that can forecast the rate of induced seismicity, called ORACLE.  This repository is related to a study about the same topic [Schultz & Wiemer, 2026].  The code here is modified from a past work [Dascher-Cousineau et al., 2023].

References:

            R. Schultz, & S. Wiemer (2026)
            Forecasting the rate of induced seismicity as a neural temporal point process
            Journal of Geophysical Research: Machine Learning & Computation, xx, XXX.
            doi: xxx.

            K. Dascher‐Cousineau, O. Shchur, E.E. Brodsky, & S. Günnemann (2023). 
            Using deep learning for flexible and scalable earthquake forecasting.
            Geophysical Research Letters, 50(17), e2023GL103909.
            doi: 10.1029/2023GL103909.


The code includes:

1. Model definitions for both ETAS and ORACLE implementations in the `IS-ntpp/eq` Python library. 
2. Scripts for model training and recreation of results in `Python/`.
3. The trained models in `Python/models/`.
4. Datasets for training that are callable from the eq Python library.
5. Scripts to reproduce paper Figures in `Python/`.
6. Scripts to pre-process datasets in a sequence format for forecasting with a NTPP in `Matlab/`.

## Installation
The code has been tested on Linux (Ubuntu 20.04) and MacOS.
1. Make sure you have the latest version of [`conda`](https://docs.conda.io/en/latest/miniconda.html) installed.
2. Install the dependencies and create a new conda environment.
    ```bash
    cd IS-ntpp
    conda env create -f environment.yml
    conda activate eq
    ```
   I trained without GPU resources, so the line below is commented out. 
    ```
      - cudatoolkit=11.3
    ```
   from the file `environment.yml` before executing the commands above.
3. Install the `eq` package.
    ```bash
    pip install -e .
    ```


This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details: http://www.gnu.org/licenses/
