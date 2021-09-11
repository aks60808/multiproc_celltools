import pandas as pd
import numpy as np
import os
import os.path
from pathlib import Path
import inquirer
import time
import multiprocessing
import warnings
warnings.filterwarnings("ignore")

def _rect_inter_inner(x1, x2):
    n1 = x1.shape[0]-1
    n2 = x2.shape[0]-1
    X1 = np.c_[x1[:-1], x1[1:]]
    X2 = np.c_[x2[:-1], x2[1:]]
    S1 = np.tile(X1.min(axis=1), (n2, 1)).T
    S2 = np.tile(X2.max(axis=1), (n1, 1))
    S3 = np.tile(X1.max(axis=1), (n2, 1)).T
    S4 = np.tile(X2.min(axis=1), (n1, 1))
    return S1, S2, S3, S4


def _rectangle_intersection_(x1, y1, x2, y2):
    S1, S2, S3, S4 = _rect_inter_inner(x1, x2)
    S5, S6, S7, S8 = _rect_inter_inner(y1, y2)
    # print(S1,S2)
    C1 = np.less_equal(S1, S2)
    C2 = np.greater_equal(S3, S4)
    C3 = np.less_equal(S5, S6)
    C4 = np.greater_equal(S7, S8)

    ii, jj = np.nonzero(C1 & C2 & C3 & C4)
    return ii, jj


def intersection(x1, y1, x2, y2):
    """
    INTERSECTIONS Intersections of curves.
    Computes the (x,y) locations where two curves intersect.  The curves
    can be broken with NaNs or have vertical segments.
    usage:
    x,y=intersection(x1,y1,x2,y2)
        Example:
        a, b = 1, 2
        phi = np.linspace(3, 10, 100)
        x1 = a*phi - b*np.sin(phi)
        y1 = a - b*np.cos(phi)
        x2=phi
        y2=np.sin(phi)+2
        x,y=intersection(x1,y1,x2,y2)
        plt.plot(x1,y1,c='r')
        plt.plot(x2,y2,c='g')
        plt.plot(x,y,'*k')
        plt.show()
    """
    x1 = np.asarray(x1)
    x2 = np.asarray(x2)
    y1 = np.asarray(y1)
    y2 = np.asarray(y2)

    ii, jj = _rectangle_intersection_(x1, y1, x2, y2)
    n = len(ii)

    dxy1 = np.diff(np.c_[x1, y1], axis=0)
    dxy2 = np.diff(np.c_[x2, y2], axis=0)

    T = np.zeros((4, n))
    AA = np.zeros((4, 4, n))
    AA[0:2, 2, :] = -1
    AA[2:4, 3, :] = -1
    AA[0::2, 0, :] = dxy1[ii, :].T
    AA[1::2, 1, :] = dxy2[jj, :].T

    BB = np.zeros((4, n))
    BB[0, :] = -x1[ii].ravel()
    BB[1, :] = -x2[jj].ravel()
    BB[2, :] = -y1[ii].ravel()
    BB[3, :] = -y2[jj].ravel()

    for i in range(n):
        try:
            T[:, i] = np.linalg.solve(AA[:, :, i], BB[:, i])
        except:
            T[:, i] = np.Inf

    in_range = (T[0, :] >= 0) & (T[1, :] >= 0) & (
        T[0, :] <= 1) & (T[1, :] <= 1)

    xy0 = T[2:, in_range]
    xy0 = xy0.T
    return xy0[:, 0], xy0[:, 1]
def worker(command):
    filename = command[0]
    output_path_pf = command[1]
    output_path_cd = command[2]
    output_path_hfir = command[3]
    output_path_bdcir = command[4]
    cycles = command[5]
    proc_mode = command[6]
    file = "datasets\\" + filename + '.xlsx'
    df = pd.read_excel(file)
    if 'Action' not in df.columns:
        df = pd.read_excel(file,skiprows=[0,1])
    if proc_mode == 'CPD':
        mode = 'CP\D'
        bdcir_flag = True
    else:
        mode = 'CC\D'
        bdcir_flag = False
        df = df[~df['Loop1'].isna()]
    #   select data where Action is mode and End status is either EV or ET
    pf_df = df[(df['Action'] == mode)&(df['End Status']=='EV') | (df['End Status']=='ET')]
    # extract attributes - Step Time, temperature and advanced cycle
    pf_df = pf_df[['Step time', 'T','Advance Cycle','mAH']]
    # convert sec to min
    pf_df['Run time(min)'] = pf_df['Step time'].divide(60)
    # fomat the values 
    pf_df['Run time(min)'] = pf_df['Run time(min)'].astype(float)
    pf_df['Run time(min)'] = pf_df['Run time(min)'].round(4)
    # each row of Step Time was divided by the first value in the column
    pf_df['Retention(%)'] = pf_df['Step time'].divide(pf_df['Step time'].iloc[0])
    # format the value
    pf_df['Retention(%)'] = pf_df['Retention(%)'].astype(float)
    pf_df['Retention(%)'] = pf_df['Retention(%)'].round(4)
    # rearrange the order of columns
    pf_cols = ['mAH','Step time','Run time(min)','T','Retention(%)','Advance Cycle']
    pf_df = pf_df[pf_cols]

    pf_df = pf_df.rename(columns={"Step time": "Step time(s)", "T": "Temperature(°C)"})
    # output the file
    output_pf = output_path_pf +'/'+ 'pf_' + filename + '.xlsx'
    if proc_mode == 'CCD':
        pf_df['Advance Cycle'] = pf_df['Advance Cycle'].subtract(1)
        pf_df = pf_df[['mAH','Run time(min)','Temperature(°C)', 'Retention(%)','Advance Cycle']]
    else:
        pf_df = pf_df[['Step time(s)','Run time(min)','Temperature(°C)','Retention(%)','Advance Cycle']]
    pf_df.to_excel(output_pf,index=False)

    # data collection for HF and IR
    half_cap_ir_lst=[]
    concat_cd_df = None
    for cycle in cycles:
        
        cycle = int(cycle)
        # charge part
        # select data where Action is CC-CV\C at specific cycle  
        c_df = df[(df['Action'] == 'CC-CV\C')&(df['Advance Cycle'] == cycle)&(df['R']!= float('inf'))]
        c_df = c_df.sort_values('Step time')
        # extract attributes - Voltage and Capacity
        c_df = c_df[[ 'V','mAH']]
        c_df = c_df.rename(columns={"V": "Charge_Voltage(V)", "mAH": "Charge_mAh"})
        c_df = c_df.reset_index()
        # discharge part
        d_df = df[(df['Action'] == mode)&(df['Advance Cycle'] == cycle)]
        d_df = d_df[[ 'V','mAH']]
        d_df = d_df.rename(columns={"V": "Discharge_Voltage(V)", "mAH": "Discharge_mAh"})
        d_df = d_df.reset_index()

       

       
        # concat two datafram ( charge + discharge)
        
        cd_df = pd.concat([c_df,d_df],axis=1)
        
        # drop irrelvant col
        cd_df = cd_df.drop(columns=['index'])
        # output csv file
        output_cd = output_path_cd +'/'+ 'cd_c_' + str(cycle) + '_'+ filename + '.csv'
        
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

        #   detect if there's any error occurred
        try:
        # pick the maximum value of Dis/Charge capacity
            cp_c = max(cd_df_origin['Charge_mAh'])
            cp_d = max(cd_df_origin['Discharge_mAh'])
            cp_max = max(cp_c,cp_d)
            #   fitting for two curve
            #   create fitting space
            phi = np.linspace(0, cp_max, 100)
            #   setup x1y1,x2y2
            x1 = np.array(cd_df_origin['Charge_mAh'])
            y1 = np.array(cd_df_origin['Charge_Voltage(V)'])
            y2 = np.array(cd_df_origin['Discharge_Voltage(V)'])
            x2 = np.array(cd_df_origin['Discharge_mAh'])
            #   find intersection(polarization point)
            x, y = intersection(x1, y1, x2, y2)
            #   calculate half_capacity
            half_cap = cp_d/2 - x[0]
            #   calculate IR drop
            
            ir_drop = d_df['Discharge_Voltage(V)'][0] - d_df['Discharge_Voltage(V)'][1]
            #   append to collection
            half_cap_ir_lst.append({'Cycle':cycle,'Half_capacity(mAh)':round(half_cap,2),'Est. Polarization Voltage(V)':y[0],'Est. Polarization Capacity(mAh)':x[0],'IR_drop(ΔV)':ir_drop})
        except:
            #   shoot the warning
            print("[WARNING]file %s does't have right data at cycle %s for hf/ir conversion"%(filename,str(cycle)))
            pass
    output_cd = output_path_cd +'/'+ 'cd_' + filename + '.csv'

    concat_cd_df.to_csv(output_cd)

    hf_ir_df = pd.DataFrame(half_cap_ir_lst)    
    output_hf = output_path_hfir +'/'+ 'hf_ir_' + filename + '.xlsx'
    hf_ir_df.to_excel(output_hf)


        
    ## BDCIR
    if bdcir_flag == True:
        # Basic filter (End status, Action, Loop, Step)
        bdcir_df = df[(df['End Status'] == 'Time') & (df['Action'] == 'CC\D')]
        bdcir_df['Loop1'] = bdcir_df['Loop1'].fillna('0/6') # Fill the cycle100 Loop1 from na to 0/6
        bdcir_df = bdcir_df[bdcir_df['Step'].isin([36, 37, 64, 65])]

        # From 100 ~ 700

        # 100
        bdcir_df_100_1 = bdcir_df[(bdcir_df['Step'] == 36) & (bdcir_df['Loop1'] == '0/6')]['V'].iloc[1:].reset_index(drop=True)
        bdcir_df_100_1.loc[bdcir_df_100_1.shape[0]] = 0
        bdcir_df_100_1_mAH = bdcir_df[(bdcir_df['Step'] == 36) & (bdcir_df['Loop1'] == '0/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_100_2 = bdcir_df[(bdcir_df['Step'] == 37) & (bdcir_df['Loop1'] == '0/6')]['V'].reset_index(drop=True)
        # bdcir_df_100_2_mAH = bdcir_df[(bdcir_df['Step'] == 37) & (bdcir_df['Loop1'] == '0/6')]['mAH'].reset_index(drop=True)
        # bdcir_df_100_mAH = bdcir_df[(bdcir_df['Loop1'] == '0/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_VMin_100 = ((bdcir_df_100_2 - bdcir_df_100_1) / 9 * 1000).min()

        # 200
        bdcir_df_200_1 = bdcir_df[(bdcir_df['Step'] == 64) & (bdcir_df['Loop1'] == '1/6')]['V'].iloc[1:].reset_index(drop=True)
        bdcir_df_200_1.loc[bdcir_df_200_1.shape[0]] = 0
        bdcir_df_200_1_mAH = bdcir_df[(bdcir_df['Step'] == 64) & (bdcir_df['Loop1'] == '1/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_200_2 = bdcir_df[(bdcir_df['Step'] == 65) & (bdcir_df['Loop1'] == '1/6')]['V'].reset_index(drop=True)
        # bdcir_df_200_2_mAH = bdcir_df[(bdcir_df['Step'] == 65) & (bdcir_df['Loop1'] == '1/6')]['mAH'].reset_index(drop=True)
        # bdcir_df_200_mAH = bdcir_df[(bdcir_df['Loop1'] == '1/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_VMin_200 = ((bdcir_df_200_2 - bdcir_df_200_1) / 9 * 1000).min()

        # 300
        bdcir_df_300_1 = bdcir_df[(bdcir_df['Step'] == 64) & (bdcir_df['Loop1'] == '2/6')]['V'].iloc[1:].reset_index(drop=True)
        bdcir_df_300_1.loc[bdcir_df_300_1.shape[0]] = 0
        bdcir_df_300_1_mAH = bdcir_df[(bdcir_df['Step'] == 64) & (bdcir_df['Loop1'] == '2/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_300_2 = bdcir_df[(bdcir_df['Step'] == 65) & (bdcir_df['Loop1'] == '2/6')]['V'].reset_index(drop=True)
        # bdcir_df_300_2_mAH = bdcir_df[(bdcir_df['Step'] == 65) & (bdcir_df['Loop1'] == '2/6')]['mAH'].reset_index(drop=True)
        # bdcir_df_300_mAH = bdcir_df[(bdcir_df['Loop1'] == '2/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_VMin_300 = ((bdcir_df_300_2 - bdcir_df_300_1) / 9 * 1000).min()

        # 400
        bdcir_df_400_1 = bdcir_df[(bdcir_df['Step'] == 64) & (bdcir_df['Loop1'] == '3/6')]['V'].iloc[1:].reset_index(drop=True)
        bdcir_df_400_1.loc[bdcir_df_400_1.shape[0]] = 0
        bdcir_df_400_1_mAH = bdcir_df[(bdcir_df['Step'] == 64) & (bdcir_df['Loop1'] == '3/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_400_2 = bdcir_df[(bdcir_df['Step'] == 65) & (bdcir_df['Loop1'] == '3/6')]['V'].reset_index(drop=True)
        # bdcir_df_400_2_mAH = bdcir_df[(bdcir_df['Step'] == 65) & (bdcir_df['Loop1'] == '3/6')]['mAH'].reset_index(drop=True)
        # bdcir_df_400_mAH = bdcir_df[(bdcir_df['Loop1'] == '3/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_VMin_400 = ((bdcir_df_400_2 - bdcir_df_400_1) / 9 * 1000).min() 

        # 500
        bdcir_df_500_1 = bdcir_df[(bdcir_df['Step'] == 64) & (bdcir_df['Loop1'] == '4/6')]['V'].iloc[1:].reset_index(drop=True)
        bdcir_df_500_1.loc[bdcir_df_500_1.shape[0]] = 0
        bdcir_df_500_1_mAH = bdcir_df[(bdcir_df['Step'] == 64) & (bdcir_df['Loop1'] == '4/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_500_2 = bdcir_df[(bdcir_df['Step'] == 65) & (bdcir_df['Loop1'] == '4/6')]['V'].reset_index(drop=True)
        # bdcir_df_500_2_mAH = bdcir_df[(bdcir_df['Step'] == 65) & (bdcir_df['Loop1'] == '4/6')]['mAH'].reset_index(drop=True)
        # bdcir_df_500_mAH = bdcir_df[(bdcir_df['Loop1'] == '4/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_VMin_500 = ((bdcir_df_500_2 - bdcir_df_500_1) / 9 * 1000).min()

        # 600
        bdcir_df_600_1 = bdcir_df[(bdcir_df['Step'] == 64) & (bdcir_df['Loop1'] == '5/6')]['V'].iloc[1:].reset_index(drop=True)
        bdcir_df_600_1.loc[bdcir_df_600_1.shape[0]] = 0
        bdcir_df_600_1_mAH = bdcir_df[(bdcir_df['Step'] == 64) & (bdcir_df['Loop1'] == '5/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_600_2 = bdcir_df[(bdcir_df['Step'] == 65) & (bdcir_df['Loop1'] == '5/6')]['V'].reset_index(drop=True)
        # bdcir_df_600_2_mAH = bdcir_df[(bdcir_df['Step'] == 65) & (bdcir_df['Loop1'] == '5/6')]['mAH'].reset_index(drop=True)
        # bdcir_df_600_mAH = bdcir_df[(bdcir_df['Loop1'] == '5/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_VMin_600 = ((bdcir_df_600_2 - bdcir_df_600_1) / 9 * 1000).min()

        # 700
        bdcir_df_700_1 = bdcir_df[(bdcir_df['Step'] == 64) & (bdcir_df['Loop1'] == '6/6')]['V'].iloc[1:].reset_index(drop=True)
        bdcir_df_700_1.loc[bdcir_df_700_1.shape[0]] = 0
        bdcir_df_700_1_mAH = bdcir_df[(bdcir_df['Step'] == 64) & (bdcir_df['Loop1'] == '6/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_700_2 = bdcir_df[(bdcir_df['Step'] == 65) & (bdcir_df['Loop1'] == '6/6')]['V'].reset_index(drop=True)
        # bdcir_df_700_2_mAH = bdcir_df[(bdcir_df['Step'] == 65) & (bdcir_df['Loop1'] == '6/6')]['mAH'].reset_index(drop=True)
        # bdcir_df_700_mAH = bdcir_df[(bdcir_df['Loop1'] == '6/6')]['mAH'].iloc[1:].reset_index(drop=True)

        bdcir_df_VMin_700 = ((bdcir_df_700_2 - bdcir_df_700_1) / 9 * 1000).min()

        # print(bdcir_df_VMin_100, bdcir_df_VMin_200, bdcir_df_VMin_300, bdcir_df_VMin_400, bdcir_df_VMin_500, bdcir_df_VMin_600, bdcir_df_VMin_700)

        bdcir_space = pd.DataFrame([""], columns=[""])
        bdcir_minimum = pd.DataFrame({'DCIR1': [bdcir_df_VMin_100], 'DCIR2': [bdcir_df_VMin_200], 'DCIR3': [bdcir_df_VMin_300], 'DCIR4': [bdcir_df_VMin_400], 'DCIR5': [bdcir_df_VMin_500], 'DCIR6': [bdcir_df_VMin_600], 'DCIR7': [bdcir_df_VMin_700]})
        bdcir_final = pd.concat([
            bdcir_df_100_1, bdcir_df_100_2, bdcir_df_100_1_mAH, bdcir_minimum['DCIR1'], bdcir_space,
            bdcir_df_200_1, bdcir_df_200_2, bdcir_df_200_1_mAH, bdcir_minimum['DCIR2'], bdcir_space,
            bdcir_df_300_1, bdcir_df_300_2, bdcir_df_300_1_mAH, bdcir_minimum['DCIR3'], bdcir_space,
            bdcir_df_400_1, bdcir_df_400_2, bdcir_df_400_1_mAH, bdcir_minimum['DCIR4'], bdcir_space,
            bdcir_df_500_1, bdcir_df_500_2, bdcir_df_500_1_mAH, bdcir_minimum['DCIR5'], bdcir_space,
            bdcir_df_600_1, bdcir_df_600_2, bdcir_df_600_1_mAH, bdcir_minimum['DCIR6'], bdcir_space,
            bdcir_df_700_1, bdcir_df_700_2, bdcir_df_700_1_mAH, bdcir_minimum['DCIR7'], bdcir_space,
            ],
            axis=1,
            keys=[
                "Cycle 100(36)", "Cycle 100(37)", "Cycle 100 mAH", 'bdcir_minimum DCIR(100)', '',
                "Cycle 200(64)", "Cycle 200(65)", "Cycle 200 mAH", 'bdcir_minimum DCIR(200)', '',
                "Cycle 300(64)", "Cycle 300(65)", "Cycle 300 mAH", 'bdcir_minimum DCIR(300)', '',
                "Cycle 400(64)", "Cycle 400(65)", "Cycle 400 mAH", 'bdcir_minimum DCIR(400)', '',
                "Cycle 500(64)", "Cycle 500(65)", "Cycle 500 mAH", 'bdcir_minimum DCIR(500)', '',
                "Cycle 600(64)", "Cycle 600(65)", "Cycle 600 mAH", 'bdcir_minimum DCIR(600)', '',
                "Cycle 700(64)", "Cycle 700(65)", "Cycle 700 mAH", 'bdcir_minimum DCIR(700)', '',
                ])
        output_bdcir = output_path_bdcir +'/'+ 'bdcir_' + filename + '.csv'
        bdcir_final.to_csv(output_bdcir, index=False)

def run_pf_cd_hf_bdcir():
    pool=multiprocessing.Pool()
    proc_list = []
    cycle_num = list(int(num) for num in input("Enter cycles separated by space ").strip().split())[:]
    proc_questions = [
    inquirer.List('Mode',
                    message="Discharge List",
                    choices=['CCD', 'CPD'],
                ),
    ]
    proc_mode = inquirer.prompt(proc_questions)['Mode']
    i = 0
    cur_dir = os.getcwd()
    datafolder=cur_dir + '\datasets'
    output_path_root_folder = cur_dir + "/PF_CD_HF_output"
    try:
        os.mkdir(output_path_root_folder)
    except OSError:
        pass
    print()
    print("****** File list ******")
    
    for entry in os.scandir(datafolder):
        
        if entry.path.endswith(".xlsx") and entry.is_file():
            filename  = Path(entry.path).stem
            output_path_folder = output_path_root_folder + '/'+ filename
            output_path_subfolder_pf = output_path_folder + '/' + "Performance"
            output_path_subfolder_cd = output_path_folder + '/' + "CD"
            output_path_subfolder_hfir = output_path_folder + '/' + "HFIR"
            output_path_subfolder_bdcir = output_path_folder + '/' + "BDCIR"
            try:
                os.mkdir(output_path_folder)
                os.mkdir(output_path_subfolder_pf)
                os.mkdir(output_path_subfolder_cd)
                os.mkdir(output_path_subfolder_hfir)
                os.mkdir(output_path_subfolder_bdcir)
            except OSError:
                pass
            print("%d : %s" % (i,entry.name))
            command =[filename,output_path_subfolder_pf,output_path_subfolder_cd,output_path_subfolder_hfir,
            output_path_subfolder_bdcir,cycle_num,proc_mode]
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