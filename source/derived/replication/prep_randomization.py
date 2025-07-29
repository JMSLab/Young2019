import pandas as pd
import os
import subprocess
import sys
import shutil
import glob
import requests

def find_stata_bin():
    for exe in ('stata-mp', 'stata-se', 'stata', 'stata-cli'):
        path = shutil.which(exe)
        if path:
            return path
    apps = glob.glob('/Applications/Stata/Stata*.app/Contents/MacOS/*')
    if apps:
        return apps[0]
    raise FileNotFoundError("Stata binary not found: please install Stata or add it to your PATH.")

def copy_files_to_temp(code_dir, data_dir, paper_dir, acronym):
    os.makedirs(paper_dir, exist_ok=True)
    for file in os.listdir(data_dir):
        src = os.path.join(data_dir, file)
        dst = os.path.join(paper_dir, file)
        shutil.copy(src, dst)
    files = [f'Replication{acronym}.do', f'FisherN{acronym}.do', f'mycmd{acronym}.do']
    if acronym == 'LL':
        files += ['augmentation.dta']
    for file in files:
        src = os.path.join(code_dir, file)
        dst = os.path.join(paper_dir, file)
        shutil.copy(src, dst)

def modify_replication_file(file, paper_dir, stata_version='13.0'):
    with open(os.path.join(paper_dir, file), 'r') as f:
        lines = f.readlines()
        lines.insert(0, f'version {stata_version}\n')
        lines = [line.replace('ivreg2', 'ivreg') for line in lines]
    with open(os.path.join(paper_dir, file), 'w') as f:
        f.writelines(lines)

def xtset(acronym, paper_dir, varname):
    for prefix in ['Replication', 'FisherN']:
        with open(os.path.join(paper_dir, f'{prefix}{acronym}.do'), 'r') as file:
            lines = file.readlines()
        with open(os.path.join(paper_dir, f'{prefix}{acronym}.do'), 'w') as file:
            for line in lines:
                file.write(line)
                if 'use Dat' in line:
                    file.write(f'xtset {varname}\n')

def modify_ALO(paper_dir):
    with open(os.path.join(paper_dir, 'ReplicationALO.do'), 'r') as file:
        lines = file.readlines()
        lines = [line.replace('partial(`all\')', '') for line in lines]
    with open(os.path.join(paper_dir, 'ReplicationALO.do'), 'w') as file:
        file.writelines(lines)

def modify_CMS(paper_dir):
    xtset('CMS', paper_dir, 'id_number')

def modify_CC2(paper_dir):
    xtset('CC2', paper_dir, 'subject')

def modify_CGTTTV(paper_dir):
    url = 'http://fmwww.bc.edu/repec/bocode/w/winsor.ado'
    response = requests.get(url)
    do_path = os.path.join(paper_dir, 'winsor.do')
    with open(do_path, 'w') as file:
        file.write(response.text)

def modify_GMR(paper_dir):
    with open(os.path.join(paper_dir, 'FisherNGMR.do'), 'r') as file:
        lines = file.readlines()
    with open(os.path.join(paper_dir, 'FisherNGMR.do'), 'w') as file:
        for line in lines:
            file.write(line)
            if 'use DatGMR' in line:
                file.write('capture rename _const const')

def modify_DHR(paper_dir):
    src = os.path.join(paper_dir, 'drop.dta')
    dst = os.path.join(paper_dir, 'Temp', 'drop.dta')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    os.system(f'mv {src} {dst}')
    with open(os.path.join(paper_dir, 'ReplicationDHR.do'), 'r') as file:
        lines = file.readlines()
    with open(os.path.join(paper_dir, 'ReplicationDHR.do'), 'w') as file:
        lines = [line.replace('Temp\\', 'Temp/') for line in lines]
        mod_lines = [line for line in lines if 'use ' in line and '\"' not in line]
        lines = [line.replace('use ', 'use \"') if line in mod_lines else line for line in lines]
        mod_lines = [line for line in lines if ', clear' in line and '\",' not in line]
        lines = [line.replace(', clear', '\", clear') if line in mod_lines else line for line in lines]
        file.writelines(lines)

def modify_ER(paper_dir):
    with open(os.path.join(paper_dir, 'mycmdER.do'), 'r') as file:
        lines = file.readlines()
        lines = [line for line in lines if line.strip()]
        lines = lines[:-3]
    with open(os.path.join(paper_dir, 'mycmdER.do'), 'w') as file:
        file.writelines(lines)

def modify_LL(paper_dir):
    xtset('LL', paper_dir, 'uniqueid')

def modify_MMW(paper_dir):
    with open(os.path.join(paper_dir, 'ReplicationMMW.do'), 'r') as file:
        lines = file.readlines()
        lines = [line for line in lines if 'xtivreg' not in line]
        lines = [line for line in lines if 'lincom' not in line]
    with open(os.path.join(paper_dir, 'ReplicationMMW.do'), 'w') as file:
        file.writelines(lines)

def modify_R(paper_dir):
    xtset('R', paper_dir, 'id')

def modify_S(paper_dir):
    xtset('S', paper_dir, 'session')

def modify_T(paper_dir):
    with open(os.path.join(paper_dir, 'ReplicationT.do'), 'r') as file:
        lines = file.readlines()
    with open(os.path.join(paper_dir, 'ReplicationT.do'), 'w') as file:
        for line in lines:
            if 'save DatT' in line:
                file.write('drop if villnum == .\n')
            file.write(line)

def modify_WDL(paper_dir):
    src = os.path.join(paper_dir, 'AEJApp_2008_0129_data.sav')
    dst = os.path.join(paper_dir, 'AEJApp_2008_0129_data.dta')
    df = pd.read_spss(src)
    df.to_stata(dst, write_index=False)

def make_tables(acronym, paper_dir, stata_bin, timeout=3600):
    cmd = [stata_bin, '-b', 'run', f'Replication{acronym}.do']
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=paper_dir, timeout=timeout)
    if result.returncode != 0:
        print("Stata returned an error:", result.stderr, file=sys.stderr)
    with open(os.path.join(paper_dir, f'replication.log'), 'w') as log_file:
        log_file.write(result.stdout)

def main():
    paper = sys.argv[1] if len(sys.argv) > 1 else 'FieldPandePappRigol_2013'
    
    xwalk = pd.read_csv('datastore/raw/InputsToYoung2019/Young2019AcronymCrosswalk.csv')
    acronym = xwalk['acronym'][xwalk['dir_name'] == paper].values[0]
    code_dir = f'datastore/raw/Young2019/data/{acronym}'
    data_dir = f'datastore/raw/InputsToYoung2019/{paper}/data'
    paper_dir = f'temp/replication/{paper}'
    stata_bin = find_stata_bin()

    copy_files_to_temp(code_dir, data_dir, paper_dir, acronym)
    modify_replication_file(f'Replication{acronym}.do', paper_dir)
    if f'modify_{acronym}' in globals():
        globals()[f'modify_{acronym}'](paper_dir)
    make_tables(acronym, paper_dir, stata_bin)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error occurred:", e)
