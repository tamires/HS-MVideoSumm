import os
from moviepy.editor import *
import utils

def get_reference_info(redundancy, segments):
    "Obtem informacoes necessarias para a producao do sumario, em especial, para cronologia."
    
    # estrutura:
    # info {} -> armazena, para cada topico, o numero do texto de origem ("text") e 
    # posicao do topico em tal texto ("topic")
    # cluster [{}{}{}] -> lista com informacoes dos topicos de um agrupamento
    # reference [[{}{}{}][{}{}]...] -> conjunto de clusters
    reference = []
    for item in redundancy:
        cluster = []
        for phrase in item:
            info = {}
            for text in range(len(segments)):
                for elem in segments[text]:
                    if phrase == elem.get("content"):
                        info["text"] = text
                        info["topic"] = segments[text].index(elem)
                        break
            cluster.append(info)
        reference.append(cluster)
    
    return reference
    
def text_in_cluster(text, reference, cluster):
    "Retorna, se existir, o topico do agrupamento que pertence ao texto fornecido (text)."
    
    for item in reference[cluster]:
        if item.get("text") == text:
            return item
    return {}
    
def insert_summary(item, summary, reference, cluster):
    "Insere um topico no sumario respeitando a cronologia."
    
    position = 0
    for phrase in summary:
        item_compare = text_in_cluster(phrase.get("text"), reference, cluster)
        if (item_compare == {}):
            if item.get("topic") > phrase.get("topic"):
                position = position + 1
            else:
                break      
        else:
            if item_compare.get("topic") > phrase.get("topic"):
                position = position + 1
            else:
                break
    
    summary.insert(position, item)
    
    return summary
    
def generate_summary(reference, segments, histogram):
    "Produz o sumario selecionando o segmento mais relevante de cada grupo."
    
    summary = []
    seg_num = 0
    for cluster in range(len(reference)):
        max_score = -1
        for candidate in range(len(reference[cluster])):
            score = sum(histogram[seg_num])
            if score > max_score:
                max_score = score
                summary_item = reference[cluster][candidate]
            seg_num = seg_num + 1
        
        summary = insert_summary(summary_item, summary, reference, cluster)
    
    return summary
        
def print_summary(intro, summary, folder, segments):
    "Imprime o texto do sumario em arquivo."
    
    file_name = os.path.join(folder, "text_summary.txt")
    file = open(file_name, 'w')
    
    # introducao
    file.write(str(intro.get("video")) + "-intro ")
    file.write(intro.get("content") + "\n")
    # demais segmentos do sumario
    for item in summary:
        file.write(str(item.get("text")) + "-" + str(item.get("topic")) + " ")
        file.write(segments[item.get("text")][item.get("topic")].get("content") + "\n")
    
    file.close()
    
def create_video_summary(intro, summary, folder, video_name, segments):
    "Produz o video do sumario, unindo os segmentos selecionados."

    clips_list = []
    # introducao
    input_video = video_name[intro.get("video")+2] + ".mp4"
    begin = utils.get_seconds(intro.get("begin"))
    end = utils.get_seconds(intro.get("end"))
    clip = VideoFileClip(input_video).subclip(begin,end)
    clip = vfx.fadeout(clip, 0.5)
    clips_list.append(clip)
    
    # demais segmentos do sumario
    for item in summary:
        input_video = video_name[item.get("text")+2] + ".mp4"
        begin = segments[item.get("text")][item.get("topic")].get("begin")
        begin = utils.get_seconds(begin)
        end = segments[item.get("text")][item.get("topic")].get("end")
        end = utils.get_seconds(end)
        clip = VideoFileClip(input_video).subclip(begin,end)
        # adiciona efeitos de fade-in e fade-out no video e audio
        clip = vfx.fadein(clip, 0.5)
        clip = vfx.fadeout(clip, 0.5)
        
        clips_list.append(clip)
        
    # gera o sumario de video concatenando os segmentos
    file_name = os.path.join(folder, "video_summary.mp4")
    final_clip = concatenate_videoclips(clips_list)
    final_clip.write_videofile(file_name)
