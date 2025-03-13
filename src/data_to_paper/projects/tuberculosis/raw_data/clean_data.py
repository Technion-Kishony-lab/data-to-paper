import gzip
import os
import zipfile

import numpy as np
import pandas as pd

GENOME_AB_NAMES = ["RIF", "INH", "PZA", "EMB", "AMI", "KAN", "LEV", "MXF", "ETH", "PAS", "RFB", "LZD", "BDQ", "DLM", "CFZ"]
PHENOTYPE_AB_NAMES = ['AMI', 'BDQ', 'CFZ', 'DLM', 'EMB', 'ETH', 'INH', 'KAN', 'LEV', 'LZD', 'MXF', 'RIF', 'RFB']

assert set(PHENOTYPE_AB_NAMES) - set(GENOME_AB_NAMES) == set()


def unzip_zip(filename: str):
    # extract zip file
    zipfilename = filename + '.zip'

    with zipfile.ZipFile(zipfilename, 'r') as zip_ref:
        zip_ref.extractall('.')

    os.remove('__MACOSX/._' + filename)
    return pd.read_csv(filename)


def zip_zip(filename: str):
    # compress
    with zipfile.ZipFile(filename + '.zip', 'w') as zip_ref:
        zip_ref.write(filename)
    os.remove(filename)


def unzip_gz(filename: str):
    # extract gz file
    zipfilename = filename + '.gz'
    with gzip.open(zipfilename, 'rb') as f_in:
        with open(filename, 'wb') as f_out:
            f_out.write(f_in.read())
    return pd.read_csv(filename)


def zip_gz(filename: str):
    # compress
    with open(filename, 'rb') as f_in:
        with gzip.open(filename + '.gz', 'wb') as f_out:
            f_out.write(f_in.read())


def save_to_data_folder(df, output_filename, filename):
    print(f'Saving {output_filename} to data folder')
    print(df.head().to_string())
    print()
    output_filepath = '../data/' + output_filename
    df.to_csv(output_filepath, index=False)

    # compress
    zip_zip(output_filepath)

    # delete the original csv file
    os.remove(filename)
    # os.remove(output_filepath)


def process_genomes():
    filename = 'GENOMES.csv'
    columns = ['UNIQUEID', 'SPECIES', 'LINEAGE_NAME']
    df = unzip_gz(filename)
    df = df[df['ISOLATENO'] == 1]
    ab_names = [ab + '_PREDICTED' for ab in GENOME_AB_NAMES]
    df[ab_names] = np.array(df['WGS_PREDICTION_STRING'].apply(list).to_list())
    df = df[columns + ab_names]
    # remove cases where ISOLATENO is not 1:
    save_to_data_folder(df, 'GENOMES_CLEAN.csv', filename)


def process_samples():
    filename = 'SAMPLES.csv'
    columns = ['UNIQUEID', 'COUNTRY_WHERE_SAMPLE_TAKEN', 'COLLECTION_DATE', 'SMOKER', 'INJECT_DRUG_USER', 'IS_HOMELESS',
               'IS_IMPRISONED', 'HIV', 'DIABETES', 'WHO_OUTCOME']
    df = unzip_gz(filename)
    # 'site.' + df['SITEID'] + '.subj.' + df['SUBJID'] + '.lab.' + df['LABID'] + '.iso.1'
    df['UNIQUEID'] = df.apply(lambda x: 'site.' + str(x['SITEID']) + '.subj.' + str(x['SUBJID']) + '.lab.' + str(x['LABID']) + '.iso.1', axis=1)
    df = df[columns]
    save_to_data_folder(df, 'SAMPLES_CLEAN.csv', filename)


def process_phenotypes():
    filename = 'CRyPTIC_reuse_table_20240917.csv'
    columns = ['UNIQUEID']

    df = unzip_zip(filename)
    ab_namnes_mapping = {ab + '_BINARY_PHENOTYPE': ab + '_MEASURED' for ab in PHENOTYPE_AB_NAMES}
    df.rename(columns=ab_namnes_mapping, inplace=True)
    df = df[columns + list(ab_namnes_mapping.values())]
    save_to_data_folder(df, 'PHENOTYPES_CLEAN.csv', filename)


if __name__ == '__main__':
    process_genomes()
    process_samples()
    process_phenotypes()
