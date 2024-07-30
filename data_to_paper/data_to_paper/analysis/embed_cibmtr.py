import numpy as np

from data_to_paper.servers.semantic_scholar import SemanticScholarEmbeddingServerCaller
import pandas as pd


if __name__ == '__main__':
    df = pd.read_csv('pubmed_publications.csv')
    semantic_scholar = SemanticScholarEmbeddingServerCaller()
    df['Embedding'] = [None] * df.shape[0]
    for i, row in df.iterrows():
        if row['Abstract'] != "No Abstract":
            paper = {'paper_id': np.random.randint(1000000, 9999999),
                     'title': row['Title'],
                     'abstract': row['Abstract']}
            embedding = semantic_scholar.get_server_response(paper)
            df.at[i, 'Embedding'] = embedding
    df.to_csv('pubmed_publications.csv', index=False)
