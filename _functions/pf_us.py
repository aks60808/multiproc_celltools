import pandas as pd
import matplotlib.pyplot as plt
import os
import os.path
from pathlib import Path
import numpy as np
import time
import multiprocessing
import inquirer





def worker(command):
    
    file = command[0]
    filename  = command[1]
    output_path_pf = command[2]
    excel_flag = int(command[3])
    proc_mode = command[4]
    f = "datasets\\" + file
    output_pf = output_path_pf +'/'+ 'pf_' + filename + '.xlsx'
    if excel_flag == 1:
        df = pd.read_excel(f,header=1)
    else:
        df = pd.read_csv(f,sep='\t',header=1)
    lst = [x for x in df.columns]
    lst = [ y for y in lst]
    df.columns = lst
    df = df[(df['ES'] == 133)| (df['ES'] == 158)]
    df = df[(df['Cyc#'] != 0)]
    if proc_mode == 'AUX':
        df = df[['Step (Sec)', 'Aux #1']]
        df['Run time(min)'] = df['Step (Sec)'].divide(60)

        # fomat the values 
        df['Run time(min)'] = df['Run time(min)'].astype(float)
        df['Run time(min)'] = df['Run time(min)'].round(4)
        # each row of Step Time was divided by the first value in the column
        df['Retention(%)'] = df['Step (Sec)'].divide(df['Step (Sec)'].iloc[0])
        # format the value
        df['Retention(%)'] = df['Retention(%)'].astype(float)
        df['Retention(%)'] = df['Retention(%)'].round(4)
        # rearrange the order of columns
        df_cols = ['Step (Sec)','Run time(min)','Aux #1','Retention(%)']
        df = df[df_cols]
        df = df.rename(columns={"Aux #1": "Temperature(°C)"})
    else:
        df = df[['StepTime', 'Temp 1']]
        df['Run time(min)'] = df['StepTime'].divide(60)
        
        # fomat the values 
        df['Run time(min)'] = df['Run time(min)'].astype(float)
        df['Run time(min)'] = df['Run time(min)'].round(4)
        # each row of Step Time was divided by the first value in the column
        df['Retention(%)'] = df['StepTime'].divide(df['StepTime'].iloc[0])
        # format the value
        df['Retention(%)'] = df['Retention(%)'].astype(float)
        df['Retention(%)'] = df['Retention(%)'].round(4)
        # rearrange the order of columns
        df_cols = ['StepTime','Run time(min)','Temp 1','Retention(%)']
    df = df[df_cols]
    df = df.rename(columns={"Temp 1": "Temperature(°C)"})
    df = df.reset_index()
    df = df.drop(columns=['index'])
    df.to_excel(output_pf,index=False)
    
        
    


def run_pf_us():
    pool=multiprocessing.Pool()
    proc_list = []
    i = 1
    proc_questions = [
    inquirer.List('Mode',
                    message="Discharge List",
                    choices=['AUX', 'TEMP'],
                ),
    ]
    proc_mode = inquirer.prompt(proc_questions)['Mode']
    cur_dir = os.getcwd()
    datafolder=cur_dir + '\datasets'
    output_path_root_folder = cur_dir + "/PF_US_output"
    try:
        os.mkdir(output_path_root_folder)
    except OSError:
        pass
    print("****** File list ******")
    for entry in os.scandir(datafolder):
        
        filename  = Path(entry.path).stem
        output_path_folder = output_path_root_folder + '/'+ filename
        output_path_subfolder_pf = output_path_folder + '/' + "Performance_US"
        try:
            os.mkdir(output_path_folder)
            os.mkdir(output_path_subfolder_pf)
        except OSError:
            pass
        print("%d : %s" % (i,entry.name))
        if entry.path.endswith(".xlsx") or entry.path.endswith(".xls"):
            xlsx_flag = 1
        else:
            xlsx_flag = 0
        command =[entry.name,filename,output_path_subfolder_pf,xlsx_flag,proc_mode]
        proc_list.append(command)
        
        i += 1
    print("****** Total %d files will be processed in parallel. ******" % i)
    multiple_results = pool.map_async(worker,proc_list)
    pool.close()
    animation = "|/-\\"
    idx = 0
    while not multiple_results.ready():
        print("Processing: ", end = '')
        print(animation[idx % len(animation)], end="\r")
        idx += 1
        time.sleep(0.1)
    pool.join()

