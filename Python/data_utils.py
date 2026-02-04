from typing import List
import torch
from eq.catalogs import IScases
from eq.data.batch import BatchIS

def get_Datasets(case_list: List[str]):
    """ Simple function that will return Pytorch dataloaders from the list of IS sequences."""
    
    # Loop over all of the cases.
    Ne = 0
    dataset_list = []
    for case in case_list:
        catalog = IScases(case)
        dataset_list.append(catalog.dataset)
        Ne += catalog.full_sequence.arrival_times.shape[0]

    # Return the dataloader and number of event samples.
    train_datasets = torch.utils.data.ConcatDataset(dataset_list)
    dataloader = torch.utils.data.DataLoader(train_datasets,batch_size=1,shuffle=False,collate_fn=BatchIS.from_list)
    return (dataloader,Ne)

def get_kFold_datasets_test(case_test: str, case_val: str):
    """ Simple function that makes training/validation/test k-folds of the datasets."""

    # Organize/list all of the sequences into their named partitions.
    Basel_list = ['Basel']
    SSFS_list = ['SSFS00','SSFS04','SSFS05'] # Omitted SSFS93 & SSFS03 because of data gaps.
    CB_list = ['CB1b', 'CB4'] # Omitted CB1a because of data gaps.
    Paralana_list = [] # Omitted Paralana because of poor data.
    St1_list = ['St1-2018','St1-2020']
    FORGE_list = ['FORGE-S1','FORGE-S2','FORGE-S3']
    PNR1_list = ['PNR1z-a','PNR1z-b','PNR1z-c']
    PNR2_list = ['PNR2-cWa','PNR2-cWb','PNR2-cE']
    train_list = Basel_list + SSFS_list + CB_list + Paralana_list + St1_list + FORGE_list + PNR1_list + PNR2_list

    # Make the test partition.
    if (case_test == 'Basel'):
        test_list = Basel_list
    elif (case_test == 'SSFS'):
        test_list = SSFS_list
    elif (case_test == 'CB'):
        test_list = CB_list
    elif (case_test == 'St1'):
        test_list = St1_list
    elif (case_test == 'FORGE'):
        test_list = FORGE_list
    elif (case_test == 'PNR1'):
        test_list = PNR1_list
    elif (case_test == 'PNR2'):
        test_list = PNR2_list

    # Make the validation partition.
    if (case_val == 'Basel'):
        val_list = Basel_list
    elif (case_val == 'SSFS'):
        val_list = SSFS_list
    elif (case_val == 'CB'):
        val_list = CB_list
    elif (case_val == 'St1'):
        val_list = St1_list
    elif (case_val == 'FORGE'):
        val_list = FORGE_list
    elif (case_val == 'PNR1'):
        val_list = PNR1_list
    elif (case_val == 'PNR2'):
        val_list = PNR2_list

    # Remove the test/validation partitinos from the training partition.
    for case_name in test_list:
        train_list.remove(case_name)
    for case_name in val_list:
        train_list.remove(case_name)

    # Get the dataloaders.
    train_dataloader, Ntrain = get_Datasets(train_list)
    val_dataloader,   Nval =   get_Datasets(val_list)
    test_dataloader,  Ntest =  get_Datasets(test_list)

    # Return everything.
    return (train_dataloader,val_dataloader,test_dataloader, Ntrain,Nval,Ntest)

def get_kFold_datasets_val(case: str):
    """ Simple function that makes training/validation k-folds of the datasets."""

    # Organize/list all of the sequences into their named partitions.
    Basel_list = ['Basel']
    SSFS_list = ['SSFS00','SSFS04','SSFS05'] # Omitted SSFS93 & SSFS03 because of data gaps.
    CB_list = ['CB1b', 'CB4'] # Omitted CB1a because of data gaps.
    Paralana_list = [] # Omitted Paralana because of poor data.
    St1_list = ['St1-2018','St1-2020']
    FORGE_list = ['FORGE-S1','FORGE-S2','FORGE-S3']
    PNR1_list = ['PNR1z-a','PNR1z-b','PNR1z-c']
    PNR2_list = ['PNR2-cWa','PNR2-cWb','PNR2-cE']

    # Make the training and validation/test partitions.
    if (case == 'Basel'):
        train_list = SSFS_list + CB_list + Paralana_list + St1_list + FORGE_list + PNR1_list + PNR2_list
        test_list = Basel_list
    elif (case == 'SSFS'):
        train_list = Basel_list + CB_list + Paralana_list + St1_list + FORGE_list + PNR1_list + PNR2_list
        test_list = SSFS_list
    elif (case == 'CB'):
        train_list = Basel_list + SSFS_list + Paralana_list + St1_list + FORGE_list + PNR1_list + PNR2_list
        test_list = CB_list
    elif (case == 'St1'):
        train_list = Basel_list + SSFS_list + CB_list + Paralana_list + FORGE_list + PNR1_list + PNR2_list
        test_list = St1_list
    elif (case == 'FORGE'):
        train_list = Basel_list + SSFS_list + CB_list + Paralana_list + St1_list + PNR1_list + PNR2_list
        test_list = FORGE_list
    elif (case == 'PNR1'):
        train_list = Basel_list + SSFS_list + CB_list + Paralana_list + St1_list + FORGE_list + PNR2_list
        test_list = PNR1_list
    elif (case == 'PNR2'):
        train_list = Basel_list + SSFS_list + CB_list + Paralana_list + St1_list + FORGE_list + PNR1_list
        test_list = PNR2_list

    # Get the dataloaders.
    train_dataloader, Ntrain = get_Datasets(train_list)
    test_dataloader,  Ntest =  get_Datasets(test_list)

    # Return everything.
    return (train_dataloader,test_dataloader, Ntrain,Ntest)