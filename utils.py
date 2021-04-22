import parse
import os

def normalize(vector):
    "Faz a normalizacao de um vetor de caracteristicas."
       
    magnitude = 0
    for p in vector:
        magnitude = magnitude + p*p
    magnitude = magnitude ** (1/2)    
    
    if magnitude != 0:
        for i in range(len(vector)):
            vector[i] = vector[i] / magnitude
    
    return vector

def cosseno(v1, v2):
    "Calcula o valor do cosseno entre dois vetores."

    cos = 0
    for i in range(len(v1)):
        cos = cos + v1[i] * v2[i]
        
    return cos

def get_seconds(time):
    "Converte o formato HH:MM:SS em segundos."

    num = parse.search("{:d}:{:d}:{:d}", time)
    seconds = num[0]*3600 + num[1]*60 + num[2]
    
    return seconds

def get_frames_folder(folder, news):
    "Compoe o caminho para a pasta com os quadros do video."
    
    news_path = news.split(os.sep)
    news_name = news_path[len(news_path)-1]
    
    return os.path.join(folder, "frames_" + news_name)
