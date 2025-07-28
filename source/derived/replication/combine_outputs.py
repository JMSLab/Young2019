import pandas as pd
import os
from source.lib.SaveData import SaveData

def process_paper(paper, xwalk):
    acronym = xwalk['acronym'][xwalk['dir_name'] == paper].values[0]
    if not os.path.exists(f'temp/replication/{paper}/output_{paper}.csv'):
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
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
    papers = df[df['num_blocks'].gt(0)]['paper'].unique()
    keys = ['original table number', 'regression number', 'coefficient number']
    df_paper, df_table, df_model, df_param = [], [], [], []
    for p in papers:
        df_paper_p, df_table_p, df_model_p, df_param_p = process_paper(p, xwalk)
        df_paper.append(df_paper_p)
        df_table.append(df_table_p)
        df_model.append(df_model_p)
        df_param.append(df_param_p)
    
    os.makedirs('output/derived/replication', exist_ok=True)
    for i, lev in enumerate(['paper', 'table', 'model', 'param']):
        df = pd.concat(locals()[f'df_{lev}'], ignore_index=True)
        key = ['paper'] + [keys[i-1]] if i > 0 else ['paper']
        SaveData(df, key, f'output/derived/replication/{lev}.csv', log_file=f'output/derived/replication/{lev}.log')

if __name__ == "__main__":
    main()
