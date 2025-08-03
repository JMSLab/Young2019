import pandas as pd
import numpy as np
import csv
from source.lib.JMSLab.tablefill import tablefill
import pypandoc

def process_data(df_par, df_mod, df_tab, df_pap):
    df = df_par.merge(df_mod, on=['paper', 'regression number'], how='left')
    df = df.merge(df_tab, on=['paper', 'original table number'], how='left')
    df = df.merge(df_pap, on='paper', how='left')
    q_0 = np.quantile(df_pap['leverage (paper)'], 0.33)
    q_1 = np.quantile(df_pap['leverage (paper)'], 0.66)
    df['leverage group'] = np.where(df['leverage (paper)'] <= q_0, 'low',
                        np.where(df['leverage (paper)'] < q_1, 'medium', 'high'))
    interactions_mask = df.groupby('paper')['interactions included'].transform('std') > 0
    df['interactions included'] = np.where(interactions_mask, df['interactions included'], np.nan)
    ft_mask = df.groupby('paper')['main table indicator'].transform('std') > 0
    df['main table indicator'] = np.where(ft_mask, df['main table indicator'], np.nan)
    return df

def extract_results(df):
    results = {}
    metrics = {'orig': 'original p-value', 'ri': 'randomization inference p-value'}
    group_filters = {
        'all': df.index, **{lev: df['leverage group'] == lev for lev in ['low', 'medium', 'high']},
        'first': df['main table indicator'] == 1, 'other': df['main table indicator'] == 0,
        'interactions': df['interactions included'] == 1, 'no interactions': df['interactions included'] == 0
    }
    for grp, filt in group_filters.items():
        results[(grp, 'num_papers')] = df.loc[filt, 'paper'].nunique()
        for alpha in [0.01, 0.05]:
            results[(grp, 'orig', alpha)] = df.loc[filt][metrics['orig']].le(alpha).mean()
            results[(grp, 'ri', alpha)] = df.loc[filt][metrics['ri']].le(alpha).mean() / df.loc[filt][metrics['orig']].le(alpha).mean()
    return results

def fill_table(results, input_path, template_path, output_path):
    out_mat = np.full((6, 8), np.nan)
    groups = ['all', 'low', 'medium', 'high']
    meta_groups = ['first', 'other', 'interactions', 'no interactions']
    alphas = [0.01, 0.05]
    out_mat[0, :len(groups)] = [results[(g, 'num_papers')] for g in groups]
    for i, metric in enumerate(['orig', 'ri'], start=1):
        out_mat[i] = [results[(g, metric, a)] for g in groups for a in alphas]
    out_mat[3, :len(meta_groups)] = [results[(g, 'num_papers')] for g in meta_groups]
    for i, metric in enumerate(['orig', 'ri'], start=4):
        out_mat[i] = [results[(g, metric, a)] for g in meta_groups for a in alphas]
    tag = "<tab:table_v>"
    with open(input_path, "w", newline="") as f:
        f.write(tag + "\n")
    pd.DataFrame(out_mat).to_csv(input_path, sep="\t", index=False, header=False,
        mode="a", quoting=csv.QUOTE_NONE, escapechar="\\")
    tablefill(input = input_path, template = template_path, output = output_path + '.tex')
    with open(output_path + '.md', "w") as f:
        f.write(pypandoc.convert_file(
            output_path + '.tex',
            to="gfm",
            format="latex"
        ))

def main():
    df_par = pd.read_csv('output/derived/replication/param.csv')
    df_mod = pd.read_csv('output/derived/replication/model.csv')
    df_tab = pd.read_csv('output/derived/replication/table.csv')
    df_pap = pd.read_csv('output/derived/replication/paper.csv')
    df = process_data(df_par, df_mod, df_tab, df_pap)
    results = extract_results(df)
    fill_table(results, 'output/analysis/replication/table_v.txt',
               'source/tables/table_v.tex', 'output/tables/table_v')

if __name__ == "__main__":
    main()

