import os
import utils
import cv2
import re
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
    
def detect_introduction(segments, folder, news):
    "Identifica quantos segmentos compoem a introducao de um video (news), a partir de seu inicio."
    
    # pasta para salvar os quadros
    frames_folder = utils.get_frames_folder(folder, news)
    os.mkdir(frames_folder)
    
    # extrai um quadro por segundo no formato jpg
    os.system("ffmpeg -i " + news + ".mp4 -vf fps=1 -start_number 0 " + os.path.join(frames_folder, "image%d.jpg"))
    
    video_size = utils.get_seconds(segments[len(segments)-1].get("end"))
    # quadro final da introducao
    final_frame = -1
    # numero de segmentos na introducao
    num_seg_intro = 0

    img_name = os.path.join(frames_folder, "image0.jpg")
    img0 = cv2.imread(img_name, cv2.IMREAD_GRAYSCALE)
    hist1 = cv2.calcHist([img0], [0], None, [256], [0,256])
    cv2.normalize(hist1, hist1, norm_type=cv2.NORM_L1)
    
    for i in range(1,video_size,1):
        img_name = os.path.join(frames_folder, "image" + str(i) + ".jpg")
        img = cv2.imread(img_name, cv2.IMREAD_GRAYSCALE)
        hist2 = cv2.calcHist([img], [0], None, [256], [0,256])
        cv2.normalize(hist2, hist2, norm_type=cv2.NORM_L1)
    
        intersection = cv2.compareHist(hist1, hist2, cv2.HISTCMP_INTERSECT)
        if intersection < 0.7:
            final_frame = i-1
            break
        hist1 = hist2

    if final_frame > -1:
        for i in range(len(segments)):
            seg_end = utils.get_seconds(segments[i].get("end"))
            if seg_end > final_frame+1:
                break
            num_seg_intro = num_seg_intro + 1
            
    return num_seg_intro, final_frame

def get_sentilex_adjectives():
    "Obtem os adjetivos presentes no lexico para portugues SentiLex."
    
    sentilex_file = open('SentiLex-flex-PT02.txt', 'r')

    sentilex = sentilex_file.readlines()
    adjectives = []

    for line in sentilex:
        if "PoS=Adj" in line:
            splitted = line.split(',')
            adjectives.append(splitted[0])

    sentilex_file.close()
    
    return adjectives

def count_adjectives(text, adjectives):
    "Conta o numero de adjetivos no texto."
    
    text = re.sub('[-./?!,":;()\']', ' ', text)
    text = text.lower()
    adj_num = 0
    text_list = text.split()
    for word in text_list:
        if word in adjectives:
            adj_num = adj_num + 1
                    
    # retorna o numero de adjetivos e numero de palavras
    return adj_num, len(text_list)

def search_faces(segment, frames_folder, face_cascade):
    "Verifica se o segmento possui faces em destaque."
    # se algum quadro do segmento possuir faces em destaque, retorna 1
    # caso contrario, retorna 0
    
    begin = utils.get_seconds(segment.get("begin"))
    end = utils.get_seconds(segment.get("end"))
    
    # nao considera o primeiro e o ultimo quadro de cada segmento
    for i in range(begin+1,end,1):
        img_name = os.path.join(frames_folder, "image" + str(i) + ".jpg")
        img = cv2.imread(img_name, cv2.IMREAD_GRAYSCALE)

        faces = face_cascade.detectMultiScale(img, 1.1, 5)
        if len(faces) > 0:
            return 1
    return 0
    
def detect_opinion_interview(segments, folder, news, adjectives):
    "Identifica quais sao os segmentos de opiniao de reporter ou entrevista."

    opinion_seg = []    
    face_cascade = cv2.CascadeClassifier("lbpcascade_frontalface_improved.xml")
    frames_folder = utils.get_frames_folder(folder, news)
    client = language.LanguageServiceClient()
    
    for i in range(len(segments)):
        candidate = search_faces(segments[i], frames_folder, face_cascade)
        
        if candidate == 1:
            text = segments[i].get("content")
            document = types.Document(
                content=text,
                type=enums.Document.Type.PLAIN_TEXT,
                language="pt-BR")
            sentiment = client.analyze_sentiment(document=document)
            seg_magnitude = sentiment.document_sentiment.magnitude
        
            adj_num, seg_size = count_adjectives(text, adjectives)
            
            if seg_size >= 0 and seg_size <= 35:       
                if seg_magnitude > 0.6 or adj_num >= 3:
                    opinion_seg.append(i)
            else:
                if seg_size > 35 and seg_size <= 70:
                    if seg_magnitude > 1.2 or adj_num >= 4:
                        opinion_seg.append(i)
                else:
                    if seg_magnitude > 1.2:
                        sentences = sentiment.sentences
                        count = 0
                        for s in sentences:
                            if s.sentiment.score < -0.3 or s.sentiment.score > 0.3:
                                count = count + 1
                
                        if count >= len(sentences) * 0.4 or adj_num >= 4:
                            opinion_seg.append(i)
    
    return opinion_seg