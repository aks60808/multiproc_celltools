import pandas as pd
import matplotlib.pyplot as plt
import os
import os.path
from pathlib import Path
import numpy as np
from datetime import datetime
from tqdm import tqdm 

gb_concat_dcir_10A_df = None
gb_concat_dcir_20A_df = None
gb_concat_dcir_30A_df = None

def generate_dcir(filename):
    global gb_concat_dcir_10A_df
    global gb_concat_dcir_20A_df
    global gb_concat_dcir_30A_df
    file = "datasets\\" + filename + '.xlsx'
    df = pd.read_excel(file)
    df = df[(df['End Status'] == 'Time')]

    ## 10A
    df_10A_ref_1A = df[(df['Step'] == 6)]
    df_10A = df[(df['Step'] == 7)]
    df_10A_ref_1A = df_10A_ref_1A[['V']]
    df_10A = df_10A[['V', 'mAH']]
    df_10A_ref_1A = df_10A_ref_1A.reset_index()
    df_10A = df_10A.reset_index()
    df_10A_ref_1A = df_10A_ref_1A.rename(columns={"V": "V(10A_ref_1A)"})
    df_10A = df_10A.rename(columns={"V": "V(10A)","mAH":"mAh(10A)"})
    R_10A = ((df_10A_ref_1A['V(10A_ref_1A)'] - df_10A['V(10A)'])/9)*1000
    dcir_10A_df = pd.concat([df_10A_ref_1A,df_10A],axis=1)
    dcir_10A_df = dcir_10A_df.drop(columns=['index'])
    dcir_10A_df['R(10A)'] = R_10A

    first_1_10A = np.full((1), f'file {filename}')
    first_2_10A = np.full((3), '')
    first = np.concatenate((first_1_10A, first_2_10A))
    second = np.array(['V(10A_ref_1A)','V(10A)', 'mAh(10A)','R(10A)'])
    arrays = [first, second]
    dcir_10A_df = pd.DataFrame(dcir_10A_df.transpose().values, index=arrays).transpose()

    if gb_concat_dcir_10A_df is None:
        gb_concat_dcir_10A_df = dcir_10A_df
    else:
        gb_concat_dcir_10A_df = pd.concat([gb_concat_dcir_10A_df, dcir_10A_df], axis = 1)


    # 20A
    df_20A_ref_1A = df[(df['Step'] == 11)]
    df_20A = df[(df['Step'] == 12)]
    df_20A_ref_1A = df_20A_ref_1A[['V']]
    df_20A = df_20A[['V', 'mAH']]
    df_20A_ref_1A = df_20A_ref_1A.reset_index()
    df_20A = df_20A.reset_index()
    df_20A_ref_1A = df_20A_ref_1A.rename(columns={"V": "V(20A_ref_1A)"})
    df_20A = df_20A.rename(columns={"V": "V(20A)","mAH":"mAh(20A)"})
    R_20A = ((df_20A_ref_1A['V(20A_ref_1A)'] - df_20A['V(20A)'])/19)*1000
    dcir_20A_df = pd.concat([df_20A_ref_1A,df_20A],axis=1)
    dcir_20A_df = dcir_20A_df.drop(columns=['index'])
    dcir_20A_df['R(20A)'] = R_20A

    first_1_20A = np.full((1), f'file {filename}')
    first_2_20A = np.full((3), '')
    first = np.concatenate((first_1_20A, first_2_20A))
    second = np.array(['V(20A_ref_1A)','V(20A)', 'mAh(20A)','R(20A)'])
    arrays = [first, second]
    dcir_20A_df = pd.DataFrame(dcir_20A_df.transpose().values, index=arrays).transpose()

    if gb_concat_dcir_20A_df is None:
        gb_concat_dcir_20A_df = dcir_20A_df
    else:
        gb_concat_dcir_20A_df = pd.concat([gb_concat_dcir_20A_df, dcir_20A_df], axis = 1)


    # 30A 
    df_30A_ref_1A = df[(df['Step'] == 16)]
    df_30A = df[(df['Step'] == 17)]
    df_30A_ref_1A = df_30A_ref_1A[['V']]
    df_30A = df_30A[['V', 'mAH']]
    df_30A_ref_1A = df_30A_ref_1A.reset_index()
    df_30A = df_30A.reset_index()
    df_30A_ref_1A = df_30A_ref_1A.rename(columns={"V": "V(30A_ref_1A)"})
    df_30A = df_30A.rename(columns={"V": "V(30A)","mAH":"mAh(30A)"})
    R_30A = ((df_30A_ref_1A['V(30A_ref_1A)'] - df_30A['V(30A)'])/29)*1000
    dcir_30A_df = pd.concat([df_30A_ref_1A,df_30A],axis=1)
    dcir_30A_df = dcir_30A_df.drop(columns=['index'])
    dcir_30A_df['R(30A)'] = R_30A

    first_1_30A = np.full((1), f'file {filename}')
    first_2_30A = np.full((3), '')
    first = np.concatenate((first_1_30A, first_2_30A))
    second = np.array(['V(30A_ref_1A)','V(30A)', 'mAh(30A)','R(30A)'])
    arrays = [first, second]
    dcir_30A_df = pd.DataFrame(dcir_30A_df.transpose().values, index=arrays).transpose()

    if gb_concat_dcir_30A_df is None:
        gb_concat_dcir_30A_df = dcir_30A_df
    else:
        gb_concat_dcir_30A_df = pd.concat([gb_concat_dcir_30A_df, dcir_30A_df], axis = 1)

def run_dcir():
    
    pbar = tqdm(total=100)
    i = 0
    cur_dir = os.getcwd()
    datafolder=cur_dir + '\datasets'
    output_path_root_folder = cur_dir + "/DCIR_output"
    try:
        os.mkdir(output_path_root_folder)
    except OSError:
        pass
    for entry in os.scandir(datafolder):
        if entry.path.endswith(".xlsx") and entry.is_file():
            filename  = Path(entry.path).stem
            print("******Now processing: %s" % entry.name)
            generate_dcir(filename)
            pbar.update(100/len([name for name in os.scandir(datafolder) if name.path.endswith(".xlsx")]))
            print()
            print("output of %s is completed" % entry.name)
            i += 1
    output_file = output_path_root_folder + '/dcir_' + str(datetime.now().strftime("%d-%m-%Y-%H-%M-%S")) + '.xlsx'
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    # Write each dataframe to a different worksheet.
    gb_concat_dcir_10A_df.to_excel(writer, sheet_name='10A')
    gb_concat_dcir_20A_df.to_excel(writer, sheet_name='20A')
    gb_concat_dcir_30A_df.to_excel(writer, sheet_name='30A')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

    print("Total %d files converted." % i)

