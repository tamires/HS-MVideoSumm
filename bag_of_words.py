import re
import nltk
import math
import utils
import os

def remove_ponctuation(text):
    "Remove os sinais de pontuacao do texto."     

    return re.sub('[-./?!,":;()\']', '', text)

def remove_numbers(text):
    "Remove numeros do texto."

    return re.sub('[0-9]', '', text)

def remove_stopwords(text):
    "Remove stopwords do texto."
    
    # lista de stopwords: dicionario do nltk com as palavras
    # consideradas stopwords em portugues
    stopwords = nltk.corpus.stopwords.words('portuguese')
    
    new_text = []
    for word in text.split():
        if not word in stopwords:
            new_text.append(word)
    
    return " ".join(new_text)

def stemming(text):
    "Reduz cada palavra do texto ao seu radical."
    
    stemmer = nltk.stem.RSLPStemmer()
    stem_text = []
    for word in text.split():
        stem_text.append(stemmer.stem(word))
        
    return " ".join(stem_text)    
    
def compute_idf(dictionary, collection):
    "Calcula o idf (inverse document frequency) de cada termo do dicionario."

    N = 0
    for text in collection:
        N = N + len(text)
    
    idf = {}
    for term in dictionary:
        df = 0
        for text in collection:
            for topic in text:
                if topic.split().count(term) != 0:
                    df = df + 1
        idf[term] = math.log10(N/df)

    return idf
        
def compute_tf_idf(dictionary, collection):
    "Calcula um vetor de tf-idf (term frequency-inverse document frequency) para cada topico da colecao."
    
    idf = compute_idf(dictionary, collection)

    # features de toda colecao de textos
    features = {}
    text_num = 0
    for text in collection:
        # features de todos os topicos de um texto
        text_features = []
        for topic in text:
            # features de um topico
            topic_features = []
            for term in dictionary:
                tf = topic.split().count(term)
                topic_features.append(tf * idf.get(term))       
            topic_features = utils.normalize(topic_features)
            text_features.append(topic_features)
        features[text_num] = text_features
        text_num = text_num + 1
    
    return features

def text_match(features, segments):
    "Encontra correspondencias entre vetores de caracteristicas com base na tecnica OOS (one to one symmetric matching)."
    
    set_time = 0
    for i in range(len(segments)):
        set_time = set_time + utils.get_seconds(segments[i][len(segments[i])-1].get("end"))
    
    # similaridade minima para uma possivel correspondencia
    dif = (set_time - 785) / 785
    threshold = 0.17 + 0.17 * dif
    
    redundancy = []
    for text in range(len(features)):
        for topic in range(len(features.get(text))):
            for c_text in range(text+1, len(features)):
                max_sim = -1
                for c_topic in range(len(features.get(c_text))):
                    sim = utils.cosseno(features.get(text)[topic], features.get(c_text)[c_topic])
                    if sim > max_sim:
                        max_sim = sim
                        match_topic = c_topic
                if max_sim > threshold:
                    max_sim_check = -1
                    for topic_check in range(len(features.get(text))):
                        sim_check = utils.cosseno(features.get(c_text)[match_topic], features.get(text)[topic_check])
                        if sim_check > max_sim_check:
                            max_sim_check = sim_check
                            match_topic_check = topic_check
                    if match_topic_check == topic:
                        redundancy.append([segments[text][topic].get("content"), segments[c_text][match_topic].get("content")])
    
    return clustering(redundancy)

def clustering(redundancy):
    "Agrupa as correspondencias identificadas."

    clustered_matches = []
    while len(redundancy) != 0:
        cluster = []
        cluster.append(redundancy[0][0])
        cluster.append(redundancy[0][1])
        redundancy.remove(redundancy[0])
        add_cluster = 1
        while add_cluster != 0:
            new_list = []
            add_cluster = 0
            for match in redundancy:
                if (match[0] in cluster) or (match[1] in cluster):
                    cluster.append(match[0])
                    cluster.append(match[1])
                    add_cluster = add_cluster + 1
                else:
                    new_list.append(match)
            redundancy = new_list
        clustered_matches.append(list(set(cluster)))
        
    return clustered_matches

def print_clusters(redundancy, folder):
    "Imprime os agrupamentos em arquivo."
    
    file_name = os.path.join(folder, "clusters.txt")
    file = open(file_name, 'w')
    
    for cluster in redundancy:
        for topic in cluster:
            file.write(topic + "\n")
        file.write("\n\n")
    
    file.close()
