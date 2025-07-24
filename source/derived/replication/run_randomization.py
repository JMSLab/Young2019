import pandas as pd
import os
import subprocess
import sys
import shutil
import glob

def find_stata_bin():
    for exe in ('stata-mp', 'stata-se', 'stata', 'stata-cli'):
        path = shutil.which(exe)
        if path:
            return path
    apps = glob.glob('/Applications/Stata/Stata*.app/Contents/MacOS/*')
    if apps:
        return apps[0]
    raise FileNotFoundError("Stata binary not found: please install Stata or add it to your PATH.")

def copy_files(paper_dir, block_dir, acronym):
    os.makedirs(block_dir, exist_ok=True)
    srs = os.path.join(paper_dir, f'FisherN{acronym}.do')
    dst = os.path.join(block_dir, f'FisherN{acronym}.do')
    shutil.copy(srs, dst)
    for file in glob.glob(f'{paper_dir}/Dat*.dta') + glob.glob(f'{paper_dir}/*.ado'):
        shutil.copy(file, block_dir)

def modify_fisher(block_dir, block_num, num_reps, acronym, stata_version='13.0'):
    with open(f'{block_dir}/FisherN{acronym}.do', 'r') as f:
        lines = f.readlines()
        lines.insert(0, f'cd "{block_dir}"\n')
        lines.insert(0, f'global reps = {num_reps}\n')
        lines.insert(0, f'version {stata_version}\n')
        lines = [line.replace('ivreg2', 'ivreg') for line in lines]
        lines = [line.replace(f'save results\\Fisher{acronym}, replace', 
                              f'save results_Fisher{acronym}, replace') for line in lines]
        lines = [line.replace(f'set seed `c\'', f'set seed `={num_reps * block_num} + `c\'\'') for line in lines]
    with open(f'{block_dir}/FisherN{acronym}.do', 'w') as f:
        f.writelines(lines)

def run_fisher(acronym, block_dir, stata_bin, timeout=3600):
    cmd = [stata_bin, '-b', 'run', os.path.join(block_dir, f'FisherN{acronym}.do')]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"Stata execution timed out after {timeout} seconds", file=sys.stderr)
        return
    if result.returncode != 0:
        print("Stata returned an error:", result.stderr, file=sys.stderr)

def main():
    paper = sys.argv[1] if len(sys.argv) > 1 else 'AshrafBerryShapiro_2010'
    block_num = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    num_reps = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    xwalk = pd.read_csv('datastore/raw/InputsToYoung2019/Young2019AcronymCrosswalk.csv')
    acronym = xwalk['acronym'][xwalk['dir_name'] == paper].values[0]
    paper_dir = f'temp/replication/{paper}'
    block_dir = f'{paper_dir}/block_{block_num}'
    stata_bin = find_stata_bin()

    copy_files(paper_dir, block_dir, acronym)
    modify_fisher(block_dir, block_num, num_reps, acronym)
    run_fisher(acronym, block_dir, stata_bin)
    for file in glob.glob(f'{block_dir}/Dat*.dta'):
        os.remove(file)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error occurred:", e)
