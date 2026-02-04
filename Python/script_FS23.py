#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  5 08:37:35 2025
Script that plots OracleLite's training curves for various architecture choices.
Used to make Figure S23.
"""

import numpy as np
import matplotlib.pyplot as plt
from tensorboard.backend.event_processing import event_accumulator


def get_TBscalars(log_dir: str, scalar_name: str, unique_flag = False) -> np.array:
    """ Routine that will return the values of a TensorBoard logged scalar as a NumPy array."""
    list1=[]
    list2=[]
    event_acc = event_accumulator.EventAccumulator(log_dir)
    event_acc.Reload()
    for e in event_acc.Scalars(scalar_name):
        list1.append(e.value)
        list2.append(e.step)
    value = np.array(list1)
    step = np.array(list2)
    if unique_flag:
        idx = np.unique(step, return_index=True)[1]
        value = value[idx]
        step = step[idx]
    return value, step

def get_LogGroup(log_dir_list: [str], scalar_name: str,) -> [np.array]:
    """ Routine that will return a group of TensorBoard logs."""
    list1=[]
    list2=[]
    list3=[]
    for log_dir in log_dir_list:
        value, step = get_TBscalars(log_dir, scalar_name, unique_flag=True)
        list1.append(value)
        list2.append(step)
        list3.append(len(step))
    N = max(list3)
    out_s = list2[list3.index(N)]
    out_v = np.ones((N,len(log_dir_list)))*np.nan
    for i, (value, step) in enumerate(zip(list1, list2)):
        n = len(value)
        out_v[0:n,i] = value
    return out_v, out_s


# Directory paths containing the TensorBoard logs.
route_log='logsExp'
IDlist = ['1','2','3','4','5']
scalar_metric = 'val_fit_loss'
ldl1 = [f'{route_log}/ExpLogs/FCN1a-' +  s for s in IDlist]
ldl2 = [f'{route_log}/ExpLogs/FCN1-' +   s for s in IDlist]
ldl3 = [f'{route_log}/ExpLogs/FCN10-' +  s for s in IDlist]
ldl4 = [f'{route_log}/ExpLogs/FCN100-' + s for s in IDlist]
ldl5 = [f'{route_log}/ExpLogs/TF-' +     s for s in IDlist]
ldl6 = [f'{route_log}/ExpLogs/TFgru-' +  s for s in IDlist]

# Get the logs.
v1, s1 = get_LogGroup(ldl1, scalar_metric)
v2, s2 = get_LogGroup(ldl2, scalar_metric)
v3, s3 = get_LogGroup(ldl3, scalar_metric)
v4, s4 = get_LogGroup(ldl4, scalar_metric)
v5, s5 = get_LogGroup(ldl5, scalar_metric)
v6, s6 = get_LogGroup(ldl6, scalar_metric)


# Plot.
fig, ax = plt.subplots()
fig.set_size_inches(9.5, 4.5)
ax.plot([0,1200],0.6028*np.ones((2)),color='black',linestyle='--', linewidth=1) # Trivial guess.
ax.plot([0,1200],0.4672*np.ones((2)),color='black',linestyle='--', linewidth=1) # Smoothed seismicity rate guess.
ax.plot([0,1200],0.4360*np.ones((2)),color='black',linestyle='--', linewidth=1) # ETAS fit.
ax.plot(s1,v1,                     color='lightcoral',    linestyle='-', linewidth=1)
ax.plot(s2,v2,                     color='bisque',        linestyle='-', linewidth=1)
ax.plot(s3,v3,                     color='lightsteelblue',linestyle='-', linewidth=1)
ax.plot(s4,v4,                     color='palegreen',     linestyle='-', linewidth=1)
ax.plot(s5,v5,                     color='plum',          linestyle='-', linewidth=1)
ax.plot(s6,v6,                     color='pink',          linestyle='-', linewidth=1)
ax.plot(s1,np.nanmean(v1, axis=1), color='red',           linestyle='-', linewidth=2)
ax.plot(s2,np.nanmean(v2, axis=1), color='darkorange',    linestyle='-', linewidth=2)
ax.plot(s3,np.nanmean(v3, axis=1), color='royalblue',     linestyle='-', linewidth=2)
ax.plot(s4,np.nanmean(v4, axis=1), color='olivedrab',     linestyle='-', linewidth=2)
ax.plot(s5,np.nanmean(v5, axis=1), color='indigo',        linestyle='-', linewidth=2)
ax.plot(s6,np.nanmean(v6, axis=1), color='crimson',       linestyle='-', linewidth=2)
ax.set_ylabel(r'L1 Loss (log$_{10}$[min])')
ax.set_xlabel(r'Training Step')
ax.set_ylim(0.42,0.62)
plt.savefig('FS23.eps', format='eps')
plt.show()



