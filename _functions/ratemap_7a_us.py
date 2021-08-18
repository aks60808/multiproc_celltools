import pandas as pd
import os
import os.path
from pathlib import Path
import numpy as np
from tqdm import tqdm 
import multiprocessing
import time
import xlsxwriter
import inquirer
def worker(command):
    
    file = command[0]
    filename  = command[1]
    output_path_7a_us = command[2]
    excel_flag = int(command[3])
    proc_mode = command[4]
    f = "datasets\\" + file
    output_7a_us = output_path_7a_us +'/'+ '7A_US_' + filename + '.xlsx'
    if excel_flag == 1:
        df = pd.read_excel(f,header=1)
    else:
        df = pd.read_csv(f,sep='\t',header=1)
    # lst = [x for x in df.columns]
    # lst = [ y for y in lst]
    # df.columns = lst
    df = df[df['State']=='D']
    df_cyc_sum = df[(df['ES'] == 133)| (df['ES'] == 158)]
    workbook = xlsxwriter.Workbook(output_7a_us)
    Step_list = list( int(i) for i in df_cyc_sum['Step'])
    worksheet = workbook.add_worksheet()

    ind = 0
    for step in Step_list:
        df_temp = df[df['Step'] == step]
        df_temp['Amps_change'] = ((df_temp['Amps'] - df_temp['Amps'].iloc[0])*100).abs()
        df_temp['Watt-hr'] = df_temp['Watt-hr'] * 1000
        df_temp['Amp-hr'] = df_temp['Amp-hr'] * 1000
        df_temp['Power'] = df_temp['Amps'] * df_temp['Volts']

        ## constant current mode
        if (df_temp['Amps_change']<10).all() == True:
    
            format_Amps = "{:.2f}".format(df_temp['Amps'].iloc[1])
            Temperature_list = list(df_temp['Aux #1'])
            Temperature_list.insert(0, 'T')
            Temperature_list.insert(0, 'Constant Current')
            Temperature_list.insert(0, f'Step-{step}')
            
            Volts_list = list(df_temp['Volts'])
            Volts_list.insert(0, 'V') 
            Volts_list.insert(0, f'{format_Amps}A')
            Volts_list.insert(0, ' ')
            
            Capacity_list = list(df_temp['Amp-hr'] )
            Capacity_list.insert(0, 'Q')
            Capacity_list.insert(0, ' ')
            Capacity_list.insert(0, ' ')
            for j in range(0,len(Temperature_list)):
                worksheet.write(j, ind, Temperature_list[j])
                worksheet.write(j, ind+1, Volts_list[j])
                worksheet.write(j, ind+2, Capacity_list[j])
        else:
            format_Power = "{:.2f}".format(df_temp['Power'].iloc[1])
            Temperature_list = list(df_temp['Aux #1'])
            Temperature_list.insert(0, 'T')
            Temperature_list.insert(0, 'Constant Power')
            Temperature_list.insert(0, f'Step-{step}')
            
            Volts_list = list(df_temp['Volts'])
            Volts_list.insert(0, 'V') 
            Volts_list.insert(0, f'{format_Power}W')
            Volts_list.insert(0, ' ')
            
            Capacity_list = list(df_temp['Amp-hr'] )
            Capacity_list.insert(0, 'Q')
            Capacity_list.insert(0, ' ')
            Capacity_list.insert(0, ' ')
            for j in range(0,len(Temperature_list)):
                worksheet.write(j, ind, Temperature_list[j])
                worksheet.write(j, ind+1, Volts_list[j])
                worksheet.write(j, ind+2, Capacity_list[j])
            
        ind+=3
    workbook.close()
    

def run_7a_us():
    pool=multiprocessing.Pool()
    proc_list = []
    i = 1
    proc_questions = [
    inquirer.List('Mode',
                    message="Discharge List",
                    choices=['AUX', 'TEMP(not available)'],
                ),
    ]
    proc_mode = inquirer.prompt(proc_questions)['Mode']
    cur_dir = os.getcwd()
    datafolder=cur_dir + '\datasets'
    output_path_root_folder = cur_dir + "/7A_US_output"
    try:
        os.mkdir(output_path_root_folder)
    except OSError:
        pass
    print("****** File list ******")
    for entry in os.scandir(datafolder):
        
        filename  = Path(entry.path).stem
        output_path_folder = output_path_root_folder + '/'+ filename
        output_path_subfolder_pf = output_path_folder + '/' + "7A_US"
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


