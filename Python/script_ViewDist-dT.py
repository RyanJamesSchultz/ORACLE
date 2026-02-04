#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 18 09:03:09 2025
Script to view the distributions predicted by Oracle.
"""

## Import relevant libraries.
import torch
import numpy as np
import matplotlib.pyplot as plt
import pytorch_lightning as pl
import pytorch_lightning.callbacks as pl_callbacks

import eq
from eq.catalogs import IScases
from data_utils import get_Datasets


## Plotting.
model = torch.load('model_Best_v15.pt')
model.eval()

# Get some data/model shiz.
cat = IScases('Basel')
d = next(iter(cat.dataset.get_dataloaderIS()))
h = model.get_history(d)[0]
c = model.get_context(h,d)
dT = model.get_inter_time_dist(c)
dTmean = dT.mean[0]

# Get the relevant distributions.
T=torch.pow(10,torch.arange(start=-10,end=+10,step=0.01)).unsqueeze(1)
PDF = dT.log_prob(T)
HAZ = dT.log_hazard(T)

# Make into numpy arrays.
T = T.detach().numpy()
dTmean = dTmean.detach().numpy()
PDF = PDF.detach().numpy()
HAZ = HAZ.detach().numpy()

# Plotting colors.
colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

# Plot.
n=5
i_range=range(round(c.shape[1]/n/2),c.shape[1],round(c.shape[1]/n))
fig = plt.figure()
gs = fig.add_gridspec(2, hspace=0)
axs = gs.subplots(sharex=True, sharey=False)
for j, i in enumerate(i_range):
    axs[0].plot(np.log10(T), PDF[:,[i]], color=colors[j] )
    axs[0].plot(np.log10(dTmean[i]), np.interp(dTmean[i],T.flatten(),PDF[:,i]), color=colors[j], marker='o')
    
    axs[1].plot(np.log10(T), HAZ[:,[i]], color=colors[j])
    axs[1].plot(np.log10(dTmean[i]), np.interp(dTmean[i],T.flatten(),HAZ[:,i]), color=colors[j], marker='o')
    
axs[0].set_ylabel('log PDF')
axs[1].set_ylabel('log Hazard')
axs[1].set_xlabel('Inter-event Time (log$_{10}$[min])')
axs[0].set_ylim(-15,+1)
axs[1].set_ylim( -8,+0)
axs[0].set_xlim(-1,+4)



