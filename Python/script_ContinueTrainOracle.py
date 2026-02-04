#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 27 10:09:46 2025
Script to continue training Oracle from a checkpoint.
@author: rschultz
"""

## Import relevant libraries.
import pytorch_lightning as pl
import pytorch_lightning.callbacks as pl_callbacks
import torch
import eq
from eq.catalogs import IScases
from eq.data.batch import BatchIS
import matplotlib.pyplot as plt
import numpy as np
#from eq.models.recurrentIS_test3 import RecurrentTPP_IS_test3

## Loading in the catalogues.
catalog1 = IScases('SSFS93')
catalog2 = IScases('SSFS00')
catalog3 = IScases('SSFS03')
catalog4 = IScases('SSFS04')
catalog5 = IScases('CB1a')
catalog6 = IScases('CB1b')
catalog7 = IScases('CB4')
catalogV = IScases('Basel')
catalogT = IScases('SSFS05')

#'''
# Concatenate the training datasets together.
train_datasets = torch.utils.data.ConcatDataset([catalog1.dataset,catalog2.dataset,catalog3.dataset,catalog4.dataset,catalog5.dataset,catalog6.dataset,catalog7.dataset])

# Print the number events available for training.
Ne = 0
for seq in train_datasets:
    Ne = Ne+seq.arrival_times.size()[0]
print('Number of events for training', Ne)

## Define the dataloaders for the training/validation/test datasets.
dl_train = torch.utils.data.DataLoader(train_datasets,batch_size=1,shuffle=False,collate_fn=BatchIS.from_list)
dl_val = catalogV.dataset.get_dataloaderIS()
dl_test = catalogT.dataset.get_dataloaderIS()

# Define the model.
model=torch.load('model.pt')
#model.learning_rate=1e-4

# Trainer prep.
#tb_logger = pl.loggers.TensorBoardLogger(save_dir='logs/')
checkpoint = pl_callbacks.ModelCheckpoint(monitor='val_forecast_loss', save_top_k=-1)
early_stopping = pl_callbacks.EarlyStopping(monitor='val_forecast_loss', patience=40, min_delta=1e-4)
num_gpus = int(torch.cuda.is_available())

# Trainer setup.
trainer = pl.Trainer(
    max_epochs=15000, 
    callbacks=[checkpoint, early_stopping], 
    gradient_clip_val=1.0, gradient_clip_algorithm='norm', 
    track_grad_norm=2, 
    #logger=[tb_logger],
    gpus=num_gpus, 
    detect_anomaly=True,
    )

# Train the model, and find best model via the validation dataset.
trainer.fit(model, dl_train, dl_val)
non_NaN_model_list=list({key: value for key, value in checkpoint.best_k_models.items() if value < 10})
model = model.load_from_checkpoint(non_NaN_model_list[-1])

## Test evaluation.
trainer.test(model, dl_test)
#'''


for i, d in enumerate(dl_train):
    loss=model.nll_loss(d).mean()
    loss.backward()
    
    print(i)
    for j,weight_part in enumerate(model.rnn.all_weights[0]):
        print(j, [weight_part.grad.isnan().any(), weight_part.grad.isinf().any()])
        print(j, [torch.nan_to_num(weight_part.grad).min(), torch.nan_to_num(weight_part.grad).max()])
        
    print([model.hypernet_time.weight.grad.isnan().any(), model.hypernet_time.weight.grad.isinf().any()])
    print([torch.nan_to_num(model.hypernet_time.weight.grad).min(), torch.nan_to_num(model.hypernet_time.weight.grad).max()])
    print([model.hypernet_time.bias.grad.isnan().any(), model.hypernet_time.bias.grad.isinf().any()])
    print([torch.nan_to_num(model.hypernet_time.bias.grad).min(), torch.nan_to_num(model.hypernet_time.bias.grad).max()])
    
    #trainer.optimizers[0].step()
    #trainer.optimizers[0].zero_grad()

#h = model.get_history(d)
#c = model.get_context(h,d)
#dist = model.get_inter_time_dist(c)
#scale = dist.component_distribution.scale
#shape = dist.component_distribution.shape
#logits = dist.mixture_distribution.logits
#dTs = d.inter_times.unsqueeze(-1)
#shape.retain_grad()
#fxn1 = torch.pow(dTs, shape)
#fxn2 = fxn1.sum()
#fxn2.backward()

#print('torch.pow-fxn output')
#print(fxn1.isinf().any())
#print(fxn1.isnan().any())
#print('torch.pow-fxn gradient wrt shape')
#print(shape.grad.isinf().any())
#print(shape.grad.isnan().any())
