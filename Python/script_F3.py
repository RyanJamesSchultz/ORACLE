#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 22 14:25:28 2025
Script to plot the Oracle forecast for the Basel case.
Used to make Figure 3.
"""

# Import relevant libraries.
import torch
import numpy as np
import matplotlib.pyplot as plt

import eq
from eq.catalogs import IScases

# Pick the case for plotting.
partition_list = ['Basel','SSFS','CB','St1','FORGE','PNR1','PNR2']
test_case = 'PNR2-cWb'
test_partition = 'PNR2'
val_partition = 'St1'

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

# Get the forecast estimates of the conditional intensity function.
t_forecast = seq.t_start+0.12*(seq.t_end-seq.t_start)
tf1,tf2,Rf1,Rf2,Rmf = model_O.forecast_intensity(sequence=seq,t_forecast=t_forecast)

# Prep the input data for plotting.
te = seq.arrival_times.numpy()
Re = -np.log10(seq.inter_times.numpy()[0:-1])
ti = seq.inj_time.numpy()
Vi = seq.inj_rate.numpy()
tf1 = tf1.numpy()
tf2 = tf2.numpy()
Rf1 = Rf1.log10().detach().numpy()
Rf2 = Rf2.log10().detach().numpy()
Rmf = Rmf.detach().numpy()
Rmf = -np.log10(Rmf)



## Plotting.

# Plot the sequence.
fig, ax = plt.subplots()
fig.set_size_inches(9.5, 4.5)
ax.plot(te,Re, color='red', marker='o', linestyle='')
ax.plot(th,Rh, color='black', linestyle='-')
ax.plot(ti,Vi, color='blue', linestyle = '-')
ax.plot(te,Rm, color='pink', marker='+', linestyle='')
#ax.plot(tf2,Rmf, color='lavenderblush', marker='.', linestyle='')
ax.plot(tf1,Rf1, color='silver', linestyle=':')
ax.plot(tf2,Rf2, color='grey', linestyle='-')
ax.set_ylabel(r'Seismicity Rate (-log$_{10}$[min])')
ax.set_xlabel('Time (min)')
plt.savefig('F3.eps', format='eps')
plt.show()




