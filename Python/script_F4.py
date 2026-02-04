#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 21 10:39:52 2025
Script to compare the Oracle results against the ETAS benchmarks.
Used to make Figure 4.
"""

# Import relevant libraries.
import torch
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

import eq
from eq.catalogs import IScases


# Organize of all the partitions/cases.
partition_list = ['Basel','SSFS','CB','St1','FORGE','PNR1','PNR2']
case_dict = {'Basel': ['Basel'],
             'SSFS': ['SSFS93','SSFS00','SSFS03','SSFS04','SSFS05'],
             'CB': ['CB1a','CB1b','CB4'],
             'St1': ['St1-2018','St1-2020'],
             'FORGE': ['FORGE-S1','FORGE-S2','FORGE-S3'],
             'PNR1': ['PNR1z-a','PNR1z-b','PNR1z-c'],
             'PNR2': ['PNR2-cWa','PNR2-cWb','PNR2-cE']
             }

# Initialize the dictionaries.
etas_loss = defaultdict(dict)
oracle_loss = defaultdict(dict)
case_list = []
for partition in partition_list:
    test_case_list = case_dict[partition]
    for test_case in test_case_list:
        etas_loss[test_case] = np.empty(0)
        oracle_loss[test_case] = np.empty(0)
        case_list.append(test_case)

# Loop over all of the ETAS examples.
for partition in partition_list:
    test_case_list = case_dict[partition]
    for test_case in test_case_list:
        val_case_list = test_case_list.copy()
        #val_case_list.remove(test_case)
        for val_case in val_case_list:
        
            # Get the corresponding ETAS model.
            etas_model_name = 'models/ETAS/Model_' + val_case + '_etas.pt'
            model = eq.models.ETAS_IS()
            model.load_state_dict(torch.load(etas_model_name))
            model.eval()
        
            # Get (and save) the loss metrics.
            d = next(iter(IScases(test_case).dataset.get_dataloaderIS()))
            loss = model.loss(d).detach().numpy()[0]
            etas_loss[test_case] = np.append(etas_loss[test_case],loss)
        
# Loop over all of the Oracle examples.
for test_partition in partition_list:
    val_list = partition_list.copy()
    #val_list.remove(test_partition)
    for val_partition in val_list:
        test_case_list = case_dict[test_partition]
        for test_case in test_case_list:
            
            if(val_partition==test_partition):
                oracle_loss[test_case] = np.append(oracle_loss[test_case],np.nan)
                continue
            
            # Get the corresponding ETAS model.
            oracle_model_name = 'models/Vanilla/Model_' + test_partition + '_' + val_partition + '.pt'
            model = eq.models.Oracle()
            model.load_state_dict(torch.load(oracle_model_name))
            model.eval()
            
            # Get (and save) the loss metrics.
            d = next(iter(IScases(test_case).dataset.get_dataloaderIS()))
            loss = model.loss(d).detach().numpy()[0]
            oracle_loss[test_case] = np.append(oracle_loss[test_case],loss)

# Report some values.
for partition in partition_list:
    test_case_list = case_dict[partition]
    for test_case in test_case_list:
        print('\n')
        print(test_case)
        print(np.average(etas_loss[test_case]))
        print(etas_loss[test_case])
        print(np.nanmean(oracle_loss[test_case]))
        print(oracle_loss[test_case])

# Boxplot.
fig, ax = plt.subplots()
fig.set_size_inches(9.5, 3.0)
i=0
for partition in partition_list:
    test_case_list = case_dict[partition]
    for test_case in test_case_list:
        v =  np.average(etas_loss[test_case]) - oracle_loss[test_case]
        v = np.delete(v,np.isnan(v))
        i+=2
        VP = ax.boxplot(v, positions=[i], widths=1.5, patch_artist=True,
                        showmeans=False, showfliers=False,
                        medianprops={'color': 'white', 'linewidth': 0.5},
                        boxprops={'facecolor': 'C0', 'edgecolor': 'white', 'linewidth': 0.5},
                        whiskerprops={'color': 'C0', 'linewidth': 1.5},
                        capprops={'color': 'C0', 'linewidth': 1.5})
ax.plot([2,i],[0,0],'-',color='black')
plt.grid(axis='x', color='0.95')
ax.set_xticklabels(case_list)
ax.set_xlabel('Case')
ax.set_ylabel('Relative Loss')
plt.savefig('F4.eps', format='eps')
plt.show()

# Other plot.
#fig, ax = plt.subplots()
#x = np.arange(0,len(partition_list))
#for i,partition in enumerate(partition_list):
#    test_case_list = case_dict[partition]
#    for test_case in test_case_list:
#        v = np.insert(oracle_loss[test_case]-np.average(oracle_loss[test_case]),i,np.nan)
#        ax.plot(x,v)
#ax.set_xticklabels(partition_list)
#ax.set_xlabel('Partition')
#plt.show()

# Other plot.
fig, ax = plt.subplots()
fig.set_size_inches(9.5, 4.5)
x = np.arange(0,len(case_list))
for i,partition in enumerate(partition_list):
    v = np.empty(0)
    for test_case in case_list:
        v = np.append(v, oracle_loss[test_case][i]-np.nanmean(oracle_loss[test_case]) )
    #v[np.isnan(v)] = 0
    ax.plot(x,v)
plt.xticks(np.arange(0,len(case_list)))
plt.grid(axis='x', color='0.95')
ax.set_xticklabels(case_list)
ax.set_xlabel('Case')
ax.legend(partition_list)
plt.show()
