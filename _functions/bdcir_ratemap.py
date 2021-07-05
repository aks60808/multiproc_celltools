import pandas as pd
import matplotlib.pyplot as plt
import os
import os.path
from pathlib import Path
import numpy as np
from tqdm import tqdm 

def generate_bdcir_n_ratemap(filename,output_path_cd,cycles):
    f = "datasets\\" + filename + '.xlsx'

    
    df_bdcir = pd.read_excel(f)
    df_original = df_bdcir.copy()
    df_bdcir = df_bdcir[(df_bdcir['End Status'] == 'Time')]
    df_bdcir_9 = df_bdcir[(df_bdcir['Step'] == 9)]
    df_bdcir_8 = df_bdcir[(df_bdcir['Step'] == 8)]
    df_bdcir_9=df_bdcir_9[['V']]
    df_bdcir_9=df_bdcir_9.reset_index()
    df_bdcir_8= (df_bdcir_8.iloc[1: , :])[['V','mAH']]
    df_bdcir_8 = df_bdcir_8.reset_index()
    R = ((df_bdcir_9['V'] - df_bdcir_8['V'])/9)*1000
    df_bdcir= df_bdcir_8.copy()
    df_bdcir['V'] = R
    df_bdcir = df_bdcir.rename(columns={"V": "BDCIR"})
    del df_bdcir['index']
    output_bdcir = output_path_cd +'/'+ 'bdcir_' + filename + '.csv'
    df_bdcir.to_csv(output_bdcir,index=False)

    concat_cd_df=None

    for cycle in cycles:
        
        cycle = int(cycle)
        # charge part
        # select data where Action is CC-CV\C at specific cycle  
        c_df = df_original[(df_original['Action'] == 'CC-CV\C')&(df_original['Advance Cycle'] == cycle)&(df_original['R']!= float('inf'))]
        c_df = c_df.reset_index()
        c_df = c_df[['mAH','V']]
        c_df = c_df.rename(columns={"V": "Charge_Voltage(V)", "mAH": "Charge_mAh"})
#         discharge part
        d_df = df_original[(df_original['Action'] == 'CC\D')&(df_original['Advance Cycle'] == cycle)&(df_original['R']!= float('inf'))]
        d_df = d_df.reset_index()
        d_df = d_df[[ 'V','mAH']]
        d_df = d_df.rename(columns={"V": "Discharge_Voltage(V)", "mAH": "Discharge_mAh"})
            

        

    
        # concat two datafram ( charge + discharge)
        
        cd_df = pd.concat([c_df,d_df],axis=1)
        if len(d_df['Discharge_Voltage(V)']) == 0:
            print("[WARNING]file %s does't have discharge data at cycle %s "%(filename,str(cycle)))

        first_1 = np.full((1), f'Circle {cycle}')
        first_2 = np.full((3), '')
        first = np.concatenate((first_1, first_2))
        second = np.array(['Charge_mAh','Charge_Voltage(V)', 'Discharge_mAh','Discharge_Voltage(V)'])
        arrays = [first, second]
        cd_df_origin = cd_df.copy()
        ################### start - arrange the order of cd_dataframe
        cd_df_cols = ['Charge_mAh','Charge_Voltage(V)', 'Discharge_mAh','Discharge_Voltage(V)']
        cd_df = cd_df[cd_df_cols]
        #################### end 
        cd_df = pd.DataFrame(cd_df.transpose().values, index=arrays).transpose()
        if concat_cd_df is None:
            concat_cd_df = cd_df
        else:
            concat_cd_df = pd.concat([concat_cd_df, cd_df], axis = 1)
    output_cd = output_path_cd +'/'+ 'ratemap_' + filename + '.csv'

    concat_cd_df.to_csv(output_cd)


def run_bdcir_ratemap():
    cycle_num = list(int(num) for num in input("Enter cycles separated by space ").strip().split())[:]
    pbar = tqdm(total=100)
    i = 0
    cur_dir = os.getcwd()
    datafolder=cur_dir + '\datasets'
    output_path_root_folder = cur_dir + "/BDCIR_RATEMAP_output"
    try:
        os.mkdir(output_path_root_folder)
    except OSError:
        pass
    for entry in os.scandir(datafolder):
        if entry.path.endswith(".xlsx") and entry.is_file():
            filename  = Path(entry.path).stem
            output_path_folder = output_path_root_folder + '/'+ filename
            try:
                os.mkdir(output_path_folder)
            except OSError:
                pass
            print("******Now processing: %s" % entry.name)
            generate_bdcir_n_ratemap(filename,output_path_folder,cycle_num)
            pbar.update(100/len([name for name in os.scandir(datafolder) if name.path.endswith(".xlsx")]))
            print()
            print("output of %s is completed" % entry.name)
            i += 1
    print("Total %d files converted." % i)


