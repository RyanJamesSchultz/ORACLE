#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 22 11:23:28 2025
Script that plots Oracle's fit for the Basel case.
Used to make Figure 2.
"""

# Import relevant libraries.
import torch
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

import eq
from eq.catalogs import IScases

# Pick the case for plotting.
partition_list = ['Basel','SSFS','CB','St1','FORGE','PNR1','PNR2']
test_case = 'Basel'
test_partition = 'Basel'
val_partition = 'FORGE'

# Get the save path for models.
oracle_model_savepath = 'models/Vanilla/Model_' + test_partition + '_' + val_partition + '.pt'
etas_model_savepath = 'models/ETAS/Model_' + test_case + '_etas.pt'

# Get the corresponding Oracle model.
model_O = eq.models.Oracle()
model_O.load_state_dict(torch.load(oracle_model_savepath))
model_O.eval()

# Get some data for plotting.
d = next(iter(IScases(test_case).dataset.get_dataloaderIS()))
seq =  d.get_sequence(0)
m = model_O.get_marks(d)
p = model_O.get_pre_params(m)
dT = model_O.get_dT_dist(p)
dTmean = dT.mean[0]

# Test loss.
print('Test loss')
print(model_O.loss(d))

# Get the mean rates from fitting.
Rm = dT.mean.squeeze(0).detach().numpy()
Rm = -np.log10((Rm[0:-1]))

# Get the fitted conditional intensity function values (i.e., the hazard function).
th,Rh = model_O.evaluate_intensity(sequence=seq,num_grid_points=0)
th = th.numpy()
Rh = Rh.log10().detach().numpy()

# Get some compensator values from fitting.
tc,Cf = model_O.evaluate_compensator(sequence=seq,num_grid_points=0)
tc = tc.numpy()
Cf = Cf.detach().numpy()

# Prep the input data for plotting.
te = seq.arrival_times.numpy()
Re = -np.log10(seq.inter_times.numpy()[0:-1])
ti = seq.inj_time.numpy()
Vi = seq.inj_rate.numpy()

# Get the relevant distributions.
T=torch.pow(10,torch.arange(start=-10,end=+10,step=0.01)).unsqueeze(1)
PDF = dT.log_prob(T)
HAZ = dT.log_hazard(T)

# Make into numpy arrays.
T = T.detach().numpy()
dTmean = dTmean.detach().numpy()
PDF = PDF.detach().numpy()
HAZ = HAZ.detach().numpy()

# Sample points to show.
#n=5
#i_range=np.arange(round(c.shape[1]/n/2),c.shape[1],round(c.shape[1]/n))
i_range = np.array([20, 120, 400, 750, 870, 1050])

# Numerically solve for the 10/90 percentiles.
dT10 = np.zeros_like(dTmean)
dT90 = np.zeros_like(dTmean)
for i in range(dT.component_distribution.shape.shape[1]):
    f10 = lambda x: dT.log_survival(torch.as_tensor(x))[0][i].detach().numpy()-np.log(0.90)
    f90 = lambda x: dT.log_survival(torch.as_tensor(x))[0][i].detach().numpy()-np.log(0.10)
    dT10[i] = fsolve(f10, 1)[0]
    dT90[i] = fsolve(f90, 1)[0]
Rh10 = np.log10(np.exp(dT.log_hazard(torch.as_tensor(dT10)).squeeze(0).detach().numpy()))
Rh90 = np.log10(np.exp(dT.log_hazard(torch.as_tensor(dT90)).squeeze(0).detach().numpy()))
R10 = -np.log10((dT10))
R90 = -np.log10((dT90))


## Plotting.

# Plotting colors.
colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

# Plot the sequence.
fig, ax = plt.subplots()
fig.set_size_inches(9.5, 3)
ax.plot(te,Re, color='red', marker='o', linestyle='')
ax.plot(th,Rh, color='black', linestyle='-')
#ax.plot(th,Rh10, color='black', linestyle=':')
#ax.plot(th,Rh90, color='black', linestyle='--')
ax.plot(ti,Vi, color='blue', linestyle = '-')
ax.plot(te,Rm, color='pink', marker='+', linestyle='')
ax.plot(th,R10, color='pink', linestyle=':')
ax.plot(th,R90, color='pink', linestyle='--')
for j, i in enumerate(i_range):
    ax.plot(te[i],Rm[i], color=colors[j], marker='o')
ax.set_ylabel(r'Seismicity Rate (log$_{10}$[min])')
ax.set_xlabel('Time (min)')
plt.savefig('F2a.eps', format='eps')
plt.show()


# Plot the inter-event time PDF and hazard function.
fig = plt.figure()
fig.set_size_inches(9.5, 4)
gs = fig.add_gridspec(2, hspace=0)
axs = gs.subplots(sharex=True, sharey=False)
for j, i in enumerate(i_range):
    axs[0].plot(np.log10(T), PDF[:,[i]], color=colors[j] )
    axs[0].plot(np.log10(dTmean[i]), np.interp(dTmean[i],T.flatten(),PDF[:,i]), color=colors[j], marker='o')
    
    axs[1].plot(np.log10(T), HAZ[:,[i]], color=colors[j])
    axs[1].plot(np.log10(dTmean[i]), np.interp(dTmean[i],T.flatten(),HAZ[:,i]), color=colors[j], marker='o')
    
axs[0].set_ylabel(r'$ln$ $f(\tau)$')
axs[1].set_ylabel(r'$ln$ $\lambda(\tau)$')
axs[1].set_xlabel(r'Inter-event time $\tau$ (-log$_{10}$[min])')
axs[0].set_ylim(-15,+1)
axs[1].set_ylim( -8,+0)
axs[0].set_xlim(-1,+4)
plt.savefig('F2b.eps', format='eps')
plt.show()

# Plot the histogram of Weibull parameters.
#n = dT.component_distribution.shape.shape[1]*dT.component_distribution.shape.shape[2]
#v = torch.reshape(dT.component_distribution.shape.squeeze(0),(1,n)).squeeze(0).detach().numpy()
#fig, ax = plt.subplots()
#fig.set_size_inches(9.5, 4)
#ax.hist(v,np.sqrt(n).round().astype(int))
#ax.set_xlabel(r'Weibull Shape Parameter k$_{sh}$')
#ax.set_ylabel(r'Counts')
#plt.show()
