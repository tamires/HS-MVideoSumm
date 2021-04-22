import os
import utils
# opencv versao 3.4.2.16
import cv2
from sklearn.cluster import KMeans
import numpy as np
import math

def image_match(desc1, desc2):
    "Encontra o numero de vetores de caracteristicas correspondentes entre dois conjuntos com base na tecnica OOS."
    
    # similaridade minima para uma possivel correspondencia
    threshold = 0.95
    num_match = 0
    desc1t = np.transpose(desc1)
    desc2t = np.transpose(desc2)
    for i in range(len(desc1)):
        sim = np.dot(desc1[i], desc2t)
        sort = np.argsort(-sim)
        if sim[sort[0]] >= threshold:
            match_feature = desc2[sort[0]]
            sim_check = np.dot(match_feature, desc1t)
            sort2 = np.argsort(-sim_check)
            if sim_check[sort2[0]] >= threshold:
                if sort2[0] == i:
                    num_match = num_match + 1
                    
    return num_match

def ks_sift(item, segments, video_name, folder):
    "Utiliza o metodo KS-SIFT para selecionar quadros-chave de um segmento de video e extrai descritores SIFT de tais quadros."
    
    begin = segments[item.get("text")][item.get("topic")].get("begin")
    begin = utils.get_seconds(begin)
    end = segments[item.get("text")][item.get("topic")].get("end")
    end = utils.get_seconds(end)
    frames_folder = utils.get_frames_folder(folder, video_name[item.get("text")+2])
    
    # arquivo com os quadros-chave dos segmentos
    file_name = os.path.join(folder, "keyframes.txt")
    file = open(file_name, 'a')
    file.write("Texto " + str(item.get("text")) + " tópico " + str(item.get("topic")) + " - ")
    
    seg_desc = []
    keyframes_desc = []
    keyframes_num_desc = []
    
    # nao considera o primeiro e o ultimo quadro de cada segmento
    for frame in range(begin+1,end,1):
        img_name = os.path.join(frames_folder, "image" + str(frame) + ".jpg")
        img = cv2.imread(img_name, cv2.IMREAD_GRAYSCALE)
        sift = cv2.xfeatures2d.SIFT_create()   
        keypoints, descriptor = sift.detectAndCompute(img, None)
        
        if descriptor is not None:    
            for i in range(len(descriptor)):
                descriptor[i] = utils.normalize(descriptor[i])
                
            num_desc = len(descriptor)
            insert = 0
            if len(keyframes_num_desc) == 0:
                insert = 1
            else:
                count = 0
                for i in range(len(keyframes_num_desc)):
                    if abs(num_desc - keyframes_num_desc[i]) >= keyframes_num_desc[i]*0.6:
                        count = count + 1
                    else:
                        num_match = image_match(keyframes_desc[i], descriptor)
                        if num_match < 0.1*keyframes_num_desc[i]:
                            count = count + 1
                if count == len(keyframes_num_desc):
                    insert = 1
        
            if insert == 1:
                file.write(str(frame) + " ")
                keyframes_num_desc.append(num_desc)
                keyframes_desc.append(descriptor)
                descriptor = descriptor.tolist()
                for feature in descriptor:
                    seg_desc.append(feature)
    
    file.write("\n")
    file.close()
    return seg_desc
    
def compute_histogram(reference, segments, video_name, folder):
    "Calcula, para cada segmento, um histograma de palavras visuais com pesos tf-idf."
    
    all_features = []
    seg_features = []
    for cluster in reference:
        for item in cluster:
            # obtem um conjunto de vetores de caracteristicas para representar o segmento
            desc = ks_sift(item, segments, video_name, folder)
            
            seg_features.append(desc)
            for feature in desc:
                all_features.append(feature)
    
    print("K-means: dicionario de palavras visuais...\n")
    # encontra o dicionario de palavras visuais
    # gera 300 agrupamentos, sendo os centroides inicializados de maneira aleatoria
    dic_size = 300
    kmeans = KMeans(n_clusters = dic_size, init = 'random', max_iter = 50)
    kmeans.fit(all_features)
    
    n_seg = len(seg_features)
    tf_idf = np.zeros((n_seg, dic_size))
    df = np.zeros(dic_size)
    for i in range(n_seg):
        visual_words = kmeans.predict(seg_features[i]).tolist()  
        # calcula df(w) = numero de segmentos que contem a palavra visual 'w'
        # calcula tf(w,s) = numero de vezes que a palavra 'w' ocorre no segmento 's'
        for word in range(dic_size):
            n_features = visual_words.count(word)
            if n_features > 0:
                df[word] = df[word] + 1
                tf_idf[i][word] = n_features
    
    # calcula o vetor de tf-idf de cada segmento
    for i in range(n_seg):
        for word in range(dic_size):
            tf_idf[i][word] = tf_idf[i][word] * math.log10(n_seg/df[word])
          
    file_name = os.path.join(folder, "histograms.txt")
    file = open(file_name, 'w')   
    for vector in tf_idf:
        for p in vector:
            file.write(str(p) + " ")
        file.write("\n")
    file.close()
            
    return tf_idf
