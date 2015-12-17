import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import NMF
from load_data import stop_words


def top_words(clusters, feature_names, num_words):
    idxs = [np.argsort(cluster)[-num_words:][::-1] for cluster in clusters]
    return [feature_names[idx] for idx in idxs]


def cluster_headlines(df, labels, kmeans, num_rows=None, random=False):
    if num_rows:
        if random:
            idxs = [np.random.choice(df.loc[labels == label, :].index, size=num_rows) for label in xrange(kmeans.n_clusters)]
            return [df.loc[idx, 'headline'] for idx in idxs]
        else:
            return [df.loc[labels == label, 'headline'][:num_rows] for label in xrange(kmeans.n_clusters)]
    else:
        return [df.loc[labels == label, 'headline'] for label in xrange(kmeans.n_clusters)]


def create_document_vector(df, max_features=5000, max_df=1, min_df=1):
    '''
    INPUTS: df - df['lemmatized_text'] will be what is vectorized
            max_features - number of words to be kept in the TfidfVector
            max_df - Cut off for words appearing in a given threshold of documents. (i.e. 1 = no limit, 0.95 will exclude words appearing in at least 95% of documents from being included in the resulting vector)
            min_df - Cut off for words appearing in a minimum number of documents. (i.e. 2 = term must appear in at least two documents)
    OUTPUT: TfidfVectorizer Object
            TfidfVector
            Feature Names Array
    '''
    stopwords = stop_words()
    # Create TfidfVectorizer
    tfid = TfidfVectorizer(input='content', stop_words=stopwords, use_idf=True, lowercase=True, max_features=max_features)
    X = tfid.fit_transform(df['lemmatized_text'].values)
    feature_names = np.array(tfid.get_feature_names())
    return tfid, X, feature_names


def cluster_articles(df, n_clusters, max_features=5000, max_df=1, min_df=1,  num_words=15, num_headlines=None):
    tfid, X, feature_names = create_document_vector(df, max_features=max_features, max_df=max_df, min_df=min_df)
    kmeans = KMeans(n_clusters=n_clusters)
    kmeans.fit(X)
    clusters = kmeans.cluster_centers_
    labels = kmeans.labels_
    words = top_words(clusters, feature_names, num_words=num_words)
    headlines = cluster_headlines(df, labels, kmeans, num_rows=num_headlines, random=True)
    return tfid, kmeans, labels, words, headlines


def nmf_articles(df, n_topics, n_features=5000, n_top_words=20, random_state=None, max_df=1, min_df=1):
    tfid, X, feature_names = create_document_vector(df, max_features=n_features, max_df=max_df, min_df=min_df)

    nmf = NMF(n_components=n_topics, random_state=random_state, alpha=.1, l1_ratio=0.5).fit(X)
    W = nmf.transform(X)

    labels = np.array([np.argmax(row) for row in W])
    # rel_importance will give a sense of how well a article can be attributed to a given topic
    rel_importance = np.array([row[np.argmax(row)] / row.sum() for row in W])
    words = top_words(nmf.components_, feature_names, n_top_words)

    return tfid, nmf, X, W, labels, rel_importance, words, feature_names


if __name__=='__main__':
    df = pd.read_pickle('election_data.pkl')

    # tfid, kmeans, labels, top_words, headlines = cluster_articles(df, n_clusters=14, max_features=15000, num_words=20, max_df=0.95, min_df=2)

    # for n_topics in xrange(6, 20):
    #     tfid, nmf, X, W, labels, rel_importance, topic_words, feature_names = nmf_articles(df, n_topics=n_topics, n_features=15000, random_state=1, max_df=0.95, min_df=2)
    #     importances = np.array([rel_importance[labels == idx].mean() for idx in xrange(n_topics)])
    #     print n_topics, len(importances[importances > 0.55])

    tfid, nmf, X, W, labels, rel_importance, topic_words, feature_names = nmf_articles(df, n_topics=12, n_features=15000, random_state=1, max_df=0.95, min_df=2)
    topic_size = [len(labels[labels == idx]) for idx in xrange(len(topic_words))]
    sort = np.argsort(topic_size)

    for idx in sort:
        print topic_words[idx]
        print 'Number of articles in topic: {}'.format(topic_size[idx])
        print rel_importance[labels == idx].mean()
        print '\n'
