import pandas as pd
import os
import subprocess
import sys
import glob
from source.derived.replication.prep_randomization import find_stata_bin

def concat_results(paper_dir, acronym, num_blocks):
    block_dirs = sorted(glob.glob(os.path.join(paper_dir, 'block_*')))
    results_paths = [os.path.join(block_dir, f'results_Fisher{acronym}.dta') for block_dir in block_dirs]
    results_paths = [p for p in results_paths if os.path.exists(p)]
    if len(results_paths) != num_blocks:
        raise ValueError(f"Expected {num_blocks} results files, but found {len(results_paths)}")
    df_1 = pd.read_stata(results_paths[0])
    first_cols = [c for c in df_1.columns if not c.startswith('Res') and c not in ['N']]
    df_1 = df_1[first_cols].dropna(how='all')
    df_2 = []
    for result_path in results_paths:
        block_df = pd.read_stata(result_path)
        block_df = block_df.drop(columns=first_cols, errors='ignore')
        block_df = block_df.dropna(how='all')
        df_2.append(block_df)
    df_2 = pd.concat(df_2, axis=0)
    df_2 = df_2.reset_index(drop=True)
    df = pd.concat([df_1] + [df_2], axis=1)
    return df

def modify_file(file, paper_dir, acronym, stata_version='13.0'):
    with open(os.path.join('source/derived/replication', file), 'r') as f:
        lines = f.readlines()
        lines.insert(0, f'use results_Fisher{acronym}.dta, clear\n')
        lines.insert(0, f'version {stata_version}\n')
        lines.insert(0, f'local paper {acronym}\n')
    with open(os.path.join(paper_dir, f'{acronym}_{file}'), 'w') as f:
        f.writelines(lines)

def run_stata(file, paper_dir, stata_bin):
    cmd = [stata_bin, '-b', 'do', file]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=paper_dir)
    if result.returncode != 0:
        print("Stata returned an error:", result.stderr, file=sys.stderr)

def add_characteristics(paper_dir, young_dir, acronym):
    df = pd.read_stata(os.path.join(paper_dir, f'stats_{acronym}.dta'))
    df = df[['paper', 'RegNum', 'CoefNum', 'p', 'rt1']]
    chars = pd.read_stata(os.path.join(young_dir, 'results', 'characteristics.dta'))
    df = df.merge(chars, on=['paper', 'RegNum'], how='inner')
    coef_chars = pd.read_stata(os.path.join(young_dir, 'results', 'basecoef.dta'))
    df = df.merge(coef_chars, on=['paper', 'RegNum', 'CoefNum'], how='inner')
    df = df[['paper', 'RegNum', 'CoefNum', 'p', 'rt1', 'cmd', 'vce', 'firsttable', 'table', 'select']]
    df = df.rename(columns={
        'RegNum': 'regression number',
        'CoefNum': 'coefficient number',
        'p': 'original p-value',
        'rt1': 'randomization inference p-value',
        'cmd': 'regression command',
        'vce': 'variance-covariance estimator',
        'firsttable': 'main table indicator',
        'table': 'original table number',
        'select': 'reported treatment effect indicator'
    })
    return df

def add_leverage(df, paper_dir, acronym):
    lev = pd.read_stata(os.path.join(paper_dir, f'leverage_{acronym}.dta'))
    lev = lev[lev['QQ1'].notna()]
    lev = lev.rename(columns={
        'CoefNum': 'coefficient number',
        'QQ3': 'leverage'
    })
    lev = lev.merge(df[['paper', 'coefficient number', 'reported treatment effect indicator']], 
                    on=['paper', 'coefficient number'], how='left')
    lev = lev[lev['reported treatment effect indicator'] == 1]
    df = df.merge(lev[['paper', 'coefficient number', 'leverage']], on=['paper', 'coefficient number'], how='left')
    df['leverage (paper)'] = df['leverage'].mean()
    return df

def process(paper, num_blocks):
    xwalk = pd.read_csv('datastore/raw/InputsToYoung2019/Young2019AcronymCrosswalk.csv')
    acronym = xwalk['acronym'][xwalk['dir_name'] == paper].values[0]
    young_dir = 'datastore/raw/Young2019/data'
    paper_dir = f'temp/replication/{paper}'
    stata_bin = find_stata_bin()
    df = concat_results(paper_dir, acronym, num_blocks)
    df.to_stata(os.path.join(paper_dir, f'results_Fisher{acronym}.dta'), write_index=False)
    modify_file('base_results.do', paper_dir, acronym)
    run_stata(f'{acronym}_base_results.do', paper_dir, stata_bin)
    modify_file('leverage.do', paper_dir, acronym)
    run_stata(f'{acronym}_leverage.do', paper_dir, stata_bin)
    df = add_characteristics(paper_dir, young_dir, acronym)
    df = add_leverage(df, paper_dir, acronym)
    df['paper'] = paper
    df.to_csv(os.path.join(paper_dir, f'output_{paper}.csv'), index=False)

def main():
    df = pd.read_csv('source/derived/replication/dispatch.csv')
    for _, row in df.iterrows():
        print(f"Processing paper: {row['paper']}")
        try:
            process(row['paper'], row['num_blocks'])
        except Exception as e:
            print(f"Error processing paper {row['paper']}: {e}")
            continue

if __name__ == "__main__":
    main()
