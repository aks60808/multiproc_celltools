import pandas as pd
import matplotlib.pyplot as plt
import os
import os.path
from pathlib import Path
import numpy as np
import inquirer
from _functions.pf_cd_hf_bdcir import run_pf_cd_hf_bdcir
from _functions.pf_us import run_pf_us
from _functions.dcir import run_dcir
from _functions.bdcir_ratemap import run_bdcir_ratemap
from _functions.helper import welcome

        
        
    


if __name__ == '__main__':
    welcome()
    mode_prompt = [
    inquirer.List('Mode',
                    message="Service List",
                    choices=['PF+CD+HF+BDCIR(CPD only)', 'DCIR', 'PF(US)', 'BDCIR+RATEMAP'],
                ),
    ]
    service_mode = inquirer.prompt(mode_prompt)['Mode']
    print(f"{service_mode} has been selected")
    if service_mode == 'PF+CD+HF+BDCIR(CPD only)':
        run_pf_cd_hf_bdcir()
    elif service_mode == 'DCIR':
        run_dcir()
    elif service_mode == 'PF(US)':
        run_pf_us()
    elif service_mode == 'BDCIR+RATEMAP':
        run_bdcir_ratemap()
    print(f"{service_mode} has been completed, exit...")




