#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 15 15:55:08 2025
Scripts to create the databases for training/validation/testing.
"""

#import eq
from eq.catalogs import IScases

# Load in a different catalog.
#catalog = eq.catalogs.White()

# Generate the catalogues.
IScases.generate_catalog('Basel')
IScases.generate_catalog('SSFS93')
IScases.generate_catalog('SSFS00')
IScases.generate_catalog('SSFS03')
IScases.generate_catalog('SSFS04')
IScases.generate_catalog('SSFS05')
IScases.generate_catalog('CB1a')
IScases.generate_catalog('CB1b')
IScases.generate_catalog('CB4')
IScases.generate_catalog('Paralana')
IScases.generate_catalog('St1-2018')
IScases.generate_catalog('St1-2020')
IScases.generate_catalog('FORGE-S1')
IScases.generate_catalog('FORGE-S2')
IScases.generate_catalog('FORGE-S3')
IScases.generate_catalog('PNR1z-a')
IScases.generate_catalog('PNR1z-b')
IScases.generate_catalog('PNR1z-c')
IScases.generate_catalog('PNR2-cWa')
IScases.generate_catalog('PNR2-cWb')
IScases.generate_catalog('PNR2-cE')
IScases.generate_catalog('GTS-HS4')
IScases.generate_catalog('GTS-HS5')
IScases.generate_catalog('GTS-HF2')

# Load in the catalogues.
#d=IScases('SSFS93')

