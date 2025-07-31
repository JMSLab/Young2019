import pandas as pd
import os
from source.lib.SaveData import SaveData
import glob

def check_results(paper, paper_dir, acronym, num_blocks):
    block_dirs = sorted(glob.glob(os.path.join(paper_dir, 'block_*')))
    results_paths = [os.path.join(block_dir, f'results_Fisher{acronym}.dta') for block_dir in block_dirs]
    results_paths = [p for p in results_paths if os.path.exists(p)]
    if len(results_paths) != num_blocks:
        raise ValueError(f"Expected {num_blocks} results files, but found {len(results_paths)}")
    if not os.path.exists(f'temp/replication/{paper}/output_{paper}.csv'):
        raise FileNotFoundError(f"Output file for {paper} not found: temp/replication/{paper}/output_{paper}.csv")

def process_paper(paper, xwalk, num_blocks):
    paper_dir = f'temp/replication/{paper}'
    acronym = xwalk['acronym'][xwalk['dir_name'] == paper].values[0]
    check_results(paper, paper_dir, acronym, num_blocks)
    df = pd.read_csv(f'temp/replication/{paper}/output_{paper}.csv')
    df['acronym in Young replication package'] = acronym
    df_paper = df.groupby('paper').agg({
        'acronym in Young replication package': 'first',
        'leverage (paper)': 'mean'
    }).reset_index()
    df_table = df.groupby(['paper', 'original table number']).agg({
        'main table indicator': 'first',
    }).reset_index().sort_values('original table number')
    df_model = df.groupby(['paper', 'regression number']).agg({
        'original table number': 'first',
        'regression command': 'first',
        'variance-covariance estimator': 'first'
    }).reset_index().sort_values('regression number')
    df_param = df.groupby(['paper', 'coefficient number']).agg({
        'regression number': 'first',
        'original p-value': 'first',
        'randomization inference p-value': 'first',
        'reported treatment effect indicator': 'first',
        'leverage': 'first'
    }).reset_index().sort_values('coefficient number')
    return df_paper, df_table, df_model, df_param

def main():
    df = pd.read_csv('source/derived/replication/dispatch.csv')
    xwalk = pd.read_csv('datastore/raw/InputsToYoung2019/Young2019AcronymCrosswalk.csv')
    keys = ['original table number', 'regression number', 'coefficient number']
    df_paper, df_table, df_model, df_param = [], [], [], []
    for _, row in df.iterrows():
        try:
            df_p = process_paper(row['paper'], xwalk, row['num_blocks'])
            df_paper.append(df_p[0])
            df_table.append(df_p[1])
            df_model.append(df_p[2])
            df_param.append(df_p[3])
        except Exception as e:
            continue
    
    os.makedirs('output/derived/replication', exist_ok=True)
    for i, lev in enumerate(['paper', 'table', 'model', 'param']):
        df = pd.concat(locals()[f'df_{lev}'], ignore_index=True)
        key = ['paper'] + [keys[i-1]] if i > 0 else ['paper']
        SaveData(df, key, f'output/derived/replication/{lev}.csv', log_file=f'output/derived/replication/{lev}.log')

if __name__ == "__main__":
    main()
