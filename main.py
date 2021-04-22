#######################################################
# Técnica de sumarização multivídeo HS-MVideoSumm     #
# Autora: Tamires T. S. Barbieri                      #
# Desenvolvido em macOS High Sierra - versão 10.13.6  #
#######################################################

import sys
import os
import json
import bag_of_words as bow
import bag_of_features as bof
import summarization as summ
import segments as seg
import utils
import time

def main():
    begin = time.time()
    
    if len(sys.argv) < 4:
        print("USAGE: main.py \"<video_set>\" \"<video1>\" \"<video2>\" [\"<video3>\" ...]\n")
        sys.exit(1)
     
    folder = "results_" + sys.argv[1]
    os.mkdir(folder)
    
    # a colecao de textos eh representada como uma matriz em que
    # cada linha contem um texto e cada coluna um topico
    collection = []
    segments = []
    min_intro = -1
    # obtem uma lista de adjetivos do lexico SentiLex (idioma portugues)
    adjectives = seg.get_sentilex_adjectives()
    
    for input_num in range(2, len(sys.argv)):
        file_name = sys.argv[input_num] + ".json"
        file = open(file_name).read()
        segments.append(json.loads(file))
        
        # identifica quantos segmentos compoem a introducao do video, a partir de seu inicio
        num_seg, final_frame = seg.detect_introduction(segments[input_num-2], folder, sys.argv[input_num])
        
        # a menor introducao eh salva para ser posteriormente levada ao sumario
        if num_seg > 0:
            intro_size = final_frame + 1
            if intro_size < min_intro or min_intro == -1:
                min_intro = intro_size
                intro = {"video": input_num-2, "begin": "00:00:00", "end": segments[input_num-2][num_seg-1].get("end"), "content": ""}
                for i in range(num_seg-1):
                    intro["content"] += segments[input_num-2][i].get("content") + " " 
                intro["content"] += segments[input_num-2][num_seg-1].get("content")
        
        # exclui os segmentos de introducao
        del(segments[input_num-2][0:num_seg])

        # identifica os segmentos que contem opiniao de reporter ou entrevista
        opinion_seg = seg.detect_opinion_interview(segments[input_num-2], folder, sys.argv[input_num], adjectives)
        
        # exclui os segmentos de opiniao de reporter ou entrevista
        temp = []
        for i in range(len(segments[input_num-2])):
            if i not in opinion_seg:
                temp.append(segments[input_num-2][i])
        segments[input_num-2] = temp
        
        # obtem os textos
        text = []
        for topic in segments[input_num-2]:
            text.append(topic.get("content"))
        collection.append(text)
    
    full_text = ""    
    # pre-processamento da colecao de textos
    for text in range(len(collection)):
        for topic in range(len(collection[text])):
            collection[text][topic] = collection[text][topic].lower()
            collection[text][topic] = bow.remove_ponctuation(collection[text][topic])
            collection[text][topic] = bow.remove_numbers(collection[text][topic])
            collection[text][topic] = bow.remove_stopwords(collection[text][topic])
            collection[text][topic] = bow.stemming(collection[text][topic])
            full_text = full_text + " " + collection[text][topic]
    
    # obtem o vocabulario da colecao de textos
    dictionary = list(sorted(set(full_text.split())))
    
    # obtem um vetor de caracteristicas para cada topico da colecao
    features = bow.compute_tf_idf(dictionary, collection)
    
    # encontra redundancia entre os textos, isto e, topicos que
    # aparecem em mais que um texto da colecao
    redundancy = bow.text_match(features, segments)
    bow.print_clusters(redundancy, folder)
    
    # produz o sumario
    reference = summ.get_reference_info(redundancy, segments)
    histogram = bof.compute_histogram(reference, segments, sys.argv, folder)
    summary = summ.generate_summary(reference, segments, histogram)
    summ.print_summary(intro, summary, folder, segments)
    # produz o video do sumario
    summ.create_video_summary(intro, summary, folder, sys.argv, segments)
    
    end = time.time()
    processing_time = end - begin
    
    file_name = os.path.join(folder, "time.txt")
    file = open(file_name, 'w')
    file.write("Tempo de execução: " + str(processing_time))
    file.close()
    
if __name__ == '__main__':
    main()
