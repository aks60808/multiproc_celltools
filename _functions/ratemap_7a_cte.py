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
    output_path_7a_cte = command[2]
    f = "datasets\\" + file
    output_7a_cte = output_path_7a_cte +'/'+ '7A_CTE_' + filename + '.xlsx'
    df = pd.read_excel(f,header=2)

    df = df[((df['Action']=='CC\D')|(df['Action']=='CP\D'))&(df['R']!=float('inf'))]
    df_cyc_sum = df[(df['End Status']=='EV')|(df['End Status']=='ET')]
    workbook = xlsxwriter.Workbook(output_7a_cte)
    Step_list = list( int(i) for i in df_cyc_sum['Step'])
    worksheet = workbook.add_worksheet()

    ind = 0
    for step in Step_list:
        df_temp = df[df['Step'] == step]
        df_temp['Amps_change'] = ((df_temp['I'] - df_temp['I'].iloc[1])*100).abs()
        df_temp['Watt-hr'] = df_temp['WH'] 
        df_temp['Amp-hr'] = df_temp['mAH'] 
        df_temp['Power'] = df_temp['P'] 

        ## constant current mode
        if (df_temp['Amps_change']<15).all() == True:
    
            format_Amps = "{:.2f}".format(df_temp['I'].iloc[1])
            Temperature_list = list(df_temp['T'])
            Temperature_list.insert(0, f'{format_Amps}A')
            Temperature_list.insert(0, f'Step-{step}')
            Temperature_list.insert(0, 'T')
            
            Volts_list = list(df_temp['V'])
            Volts_list.insert(0, f'{format_Amps}A')
            Volts_list.insert(0, f'Step-{step}')
            Volts_list.insert(0, 'V')
            
            Capacity_list = list(df_temp['Amp-hr'] )
            Capacity_list.insert(0, f'{format_Amps}A')
            Capacity_list.insert(0, f'Step-{step}')
            Capacity_list.insert(0, 'Q')
            for j in range(0,len(Temperature_list)):
                worksheet.write(j, ind, Capacity_list[j])
                worksheet.write(j, ind+1, Volts_list[j])
                worksheet.write(j, ind+2, Temperature_list[j])
        else:
            format_Power = round(df_temp['Power'].iloc[-1])
            Temperature_list = list(df_temp['T'])
            Temperature_list.insert(0, f'{format_Power}W') 
            Temperature_list.insert(0, f'Step-{step}')
            Temperature_list.insert(0, 'T')
            
            Volts_list = list(df_temp['V'])
            Volts_list.insert(0, f'{format_Power}W') 
            Volts_list.insert(0, f'Step-{step}' )
            Volts_list.insert(0, 'V')
            
            Capacity_list = list(df_temp['Amp-hr'] )
            Capacity_list.insert(0, f'{format_Power}W') 
            Capacity_list.insert(0, f'Step-{step}' )
            Capacity_list.insert(0, 'Q')
            for j in range(0,len(Temperature_list)):
                worksheet.write(j, ind, Capacity_list[j])
                worksheet.write(j, ind+1, Volts_list[j])
                worksheet.write(j, ind+2, Temperature_list[j])
            
        ind+=3
    workbook.close()
    

def run_7a_cte():
    pool=multiprocessing.Pool()
    proc_list = []
    i = 1
    # proc_questions = [
    # inquirer.List('Mode',
    #                 message="Discharge List",
    #                 choices=['AUX', 'TEMP(not available)'],
    #             ),
    # ]
    # proc_mode = inquirer.prompt(proc_questions)['Mode']
    cur_dir = os.getcwd()
    datafolder=cur_dir + '\datasets'
    output_path_root_folder = cur_dir + "/7A_CTE_output"
    try:
        os.mkdir(output_path_root_folder)
    except OSError:
        pass
    print("****** File list ******")
    for entry in os.scandir(datafolder):
        
        filename  = Path(entry.path).stem
        output_path_folder = output_path_root_folder + '/'+ filename
        output_path_subfolder_pf = output_path_folder + '/' + "7A_CTE"
        try:
            os.mkdir(output_path_folder)
            os.mkdir(output_path_subfolder_pf)
        except OSError:
            pass
        print("%d : %s" % (i,entry.name))
        command =[entry.name,filename,output_path_subfolder_pf]
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


