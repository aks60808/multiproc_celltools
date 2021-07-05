import pandas as pd
import matplotlib.pyplot as plt
import os
import os.path
from pathlib import Path
import numpy as np
from tqdm import tqdm 





def generate_data(filename,output_path_pf):
    f = "datasets\\" + filename + '.xls'
    output_pf = output_path_pf +'/'+ 'pf_' + filename + '.xls'
    df = pd.read_excel(f,header=[0,1])
    lst = [x for x in df.columns]
    lst = [ y for _,y in lst]
    df.columns = lst
    df = df[(df['ES'] == 133)| (df['ES'] == 158)]
    df = df[(df['Cyc#'] != 0)]
    df = df[['StepTime(s)', 'Temp 1']]
    df['Run time(min)'] = df['StepTime(s)'].divide(60)

    # fomat the values 
    df['Run time(min)'] = df['Run time(min)'].astype(float)
    df['Run time(min)'] = df['Run time(min)'].round(4)
    # each row of Step Time was divided by the first value in the column
    df['Retention(%)'] = df['StepTime(s)'].divide(df['StepTime(s)'].iloc[0])
    # format the value
    df['Retention(%)'] = df['Retention(%)'].astype(float)
    df['Retention(%)'] = df['Retention(%)'].round(4)
    # rearrange the order of columns
    df_cols = ['StepTime(s)','Run time(min)','Temp 1','Retention(%)']
    df = df[df_cols]
    df = df.rename(columns={"Temp 1": "Temperature(°C)"})
    df = df.reset_index()
    df = df.drop(columns=['index'])
    df.to_excel(output_pf,index=False)
    
        
    


def run_pf_us():
    pbar = tqdm(total=100)
    i = 0
    cur_dir = os.getcwd()
    datafolder=cur_dir + '\datasets'
    output_path_root_folder = cur_dir + "/PF_US_output"
    try:
        os.mkdir(output_path_root_folder)
    except OSError:
        pass
    for entry in os.scandir(datafolder):
        if entry.path.endswith(".xlsx") or entry.path.endswith(".xls"):
            filename  = Path(entry.path).stem
            output_path_folder = output_path_root_folder + '/'+ filename
            output_path_subfolder_pf = output_path_folder + '/' + "Performance_US"
            try:
                os.mkdir(output_path_folder)
                os.mkdir(output_path_subfolder_pf)
            except OSError:
                pass
            print("******Now processing: %s" % entry.name)
            generate_data(filename, output_path_subfolder_pf)
            pbar.update(100/len([name for name in os.scandir(datafolder) if name.path.endswith(".xlsx")]))
            print()
            print("output of %s is completed" % entry.name)
            i += 1
    print("Total %d files converted." % i)


