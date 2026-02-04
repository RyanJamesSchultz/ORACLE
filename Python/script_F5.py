#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 24 15:18:00 2025
Script to compare the Oracle results: 'vanilla' versus supplementary marks.
Used to make Figure 5.
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

# Handle the supplementary marks considered.
M_marks = ['Mo','Vc']
P_marks = ['Pm','pm','dP','sp']
E_marks = ['Eh','dEh']
supp_mark_list = []+M_marks+P_marks+E_marks
supp_mark_tag = ''.join(supp_mark_list)

# Initialize the dictionaries.
vanilla_loss = defaultdict(dict)
supplementary_loss = defaultdict(dict)
case_list = []
for partition in partition_list:
    test_case_list = case_dict[partition]
    for test_case in test_case_list:
        vanilla_loss[test_case] = np.empty(0)
        supplementary_loss[test_case] = np.empty(0)
        case_list.append(test_case)
        
# Loop over all of the Oracle examples.
for test_partition in partition_list:
    val_list = partition_list.copy()
    #val_list.remove(test_partition)
    for val_partition in val_list:
        test_case_list = case_dict[test_partition]
        for test_case in test_case_list:
            
            if(val_partition==test_partition):
                vanilla_loss[test_case] = np.append(vanilla_loss[test_case],np.nan)
                supplementary_loss[test_case] = np.append(supplementary_loss[test_case],np.nan)
                continue
            
            # Get the corresponding Vanilla model.
            oracle_model_name = 'models/Vanilla/Model_' + test_partition + '_' + val_partition + '.pt'
            model = eq.models.Oracle()
            model.load_state_dict(torch.load(oracle_model_name))
            model.eval()
            
            # Get (and save) the loss metrics.
            d = next(iter(IScases(test_case).dataset.get_dataloaderIS()))
            loss = model.loss(d).detach().numpy()[0]
            vanilla_loss[test_case] = np.append(vanilla_loss[test_case],loss)
            
            # Get the corresponding supplemented model.
            #oracle_model_name = 'models/Model_' + test_partition + '_' + val_partition + '.pt'
            oracle_model_name = 'models/' + supp_mark_tag + '/Model_' + test_partition + '_' + val_partition + '.pt'
            model = eq.models.Oracle(supplementary_mark_list=supp_mark_list)
            model.load_state_dict(torch.load(oracle_model_name))
            model.eval()
            
            # Get (and save) the loss metrics.
            d = next(iter(IScases(test_case).dataset.get_dataloaderIS()))
            loss = model.loss(d).detach().numpy()[0]
            supplementary_loss[test_case] = np.append(supplementary_loss[test_case],loss)

# Report some values.
for partition in partition_list:
    test_case_list = case_dict[partition]
    for test_case in test_case_list:
        print('\n')
        print(test_case)
        print(np.nanmean(vanilla_loss[test_case]))
        print(vanilla_loss[test_case])
        print(np.nanmean(supplementary_loss[test_case]))
        print(supplementary_loss[test_case])

# Boxplot.
fig, ax = plt.subplots()
i=0
for partition in partition_list:
    test_case_list = case_dict[partition]
    for test_case in test_case_list:
        v = supplementary_loss[test_case] - vanilla_loss[test_case]
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
fig.set_size_inches(9.5, 3.5)
plt.savefig('F5.eps', format='eps')
plt.show()






