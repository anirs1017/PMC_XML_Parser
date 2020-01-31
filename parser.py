#!/usr/bin/env python
# coding: utf-8
"""
Created on Thu Jan 23 16:09:55 2020

@author: sinha
"""

from bs4 import BeautifulSoup
import os
import shutil
import re
import json
import spacy
from nltk import tokenize
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters

nlp = spacy.load('en_core_web_sm')

def writeToLogFile(filePath, filename, ref_dict, caption_dict):
    for key in ref_dict:
         write_text = ""
         write_text = filePath + ' , ' + filename + ' , '  + 'Reference'
         for item in ref_dict[key]:
             write_text = write_text + ' , ' + str(item) #+ ','
         write_text = write_text + '\n'
         log_file.write(write_text)
         
    for key in caption_dict:
         write_text = ""
         write_text = write_text = filePath + ' , ' + filename + ' , '  + 'Caption'
         for item in caption_dict[key]:
             write_text = write_text + ' , ' + str(item) #+ ','
         write_text = write_text + '\n'
         log_file.write(write_text)
    
    log_file.write('\n-------------------------------------------------------------------------------------------------\n')

class nxmlParser():
    
    def __init__(self):
        self.filename = ''
        self.tags_list = ['fig', 'table']
        
        self.log_file_caption = {}
        self.log_file_references = {}
        
        self.ref_marker_length = 0
        self.rids_dict = {}  # Save rids with uniquely added numbers as marker-keys and the corresponding direct references as values.
        self.captions_dict = {}  # Save keys as rids and values with Start and End markers with the captions.
        self.set_caption_markers = set()    # Save unique keys of the captions
        self.dict_markers_ids = {}  # Save a mapping of every rid with the markers of rids, key = rid, value = list of rid markers
        self.sentences_dict = {}  # Save a mapping of every sentence as captions, and the direct reference text
        
        self.updated_rids_dict = {}  # A temporary dictionary to store the cleaned form of direct references without the markers in the text. 
                                #key = marker-rids, value = list (Direct reference text, tuple of start and end marker points of the text)
        self.updated_captions_dict = {} # A temporary dictionary to store the cleaned form of captions without the markers in the text. 
                                #key = rid, value = list (caption text, tuple of start and end marker points of the text)
        
        self.captions_DRef_dict = {}  # A final dictionary to store the reference type, object identity with #, caption text and corresponding ref-points, direct reference text and corresponding ref-points 
        self.all_sent_parsed = []
        self.curr_ref_points = 0
        self.sent_ref_points = []
        self.all_sent_original = []
    
    def createLogFileDicts(self):
        for key in self.dict_markers_ids:
            if key not in self.log_file_caption:
                self.log_file_caption[key] = []
            
            caption_type = self.dict_markers_ids[key][0]
            caption_id = self.dict_markers_ids[key][-1]
            num_caption_references = len(self.dict_markers_ids[key]) - 2
            self.log_file_caption[key].append(caption_type)
            self.log_file_caption[key].append(caption_id)
            self.log_file_caption[key].append(num_caption_references)
        
        count = 0
        for key in self.updated_rids_dict:
            count += 1
            if key not in self.log_file_references:
                self.log_file_references[key] = []
            
            for id_key in self.dict_markers_ids:
                if key in self.dict_markers_ids[id_key]:
#                    ref_type = self.dict_markers_ids[id_key][0]
                    ref_to_capt_id = self.dict_markers_ids[id_key][-1]
                    
#                    self.log_file_references[key].append(ref_type)
                    self.log_file_references[key].append(ref_to_capt_id)
            
            self.log_file_references[key].append(count)
            ref_text_span_start = self.updated_rids_dict[key][1][0]
            if ref_text_span_start > 0:
                self.log_file_references[key].append(1)
            else:
                self.log_file_references[key].append(-1)

    
    def addMarkersToXREF(self):
        count = 0
        for ref in soup.find_all('xref'):
            if ref['ref-type'] in self.tags_list:
                rid_key = '#'+ ref['rid'] + '-' + str(count) + '#-'
                ref.string = rid_key + ref.string
                count += 1
                
                self.ref_marker_length = len(rid_key)
                marker_key = ref['rid']
                if marker_key not in self.dict_markers_ids:
                    self.dict_markers_ids[marker_key] = []
                    if ref['ref-type'] == "table":
                        self.dict_markers_ids[marker_key].append("Table")
                    elif ref['ref-type'] == "fig":
                        self.dict_markers_ids[marker_key].append("Figure")
           
                self.dict_markers_ids[marker_key].append(rid_key)
                
#                if rid_key not in self.rids_dict:
#                    self.rids_dict[rid_key] = []
    
    def showCaptions(self):
        for ref in soup.find_all('xref'):
            original_key = ref['ref-type']
            tag_id = ref['rid']
            key = original_key
            
            if key in self.tags_list:
                if key == 'table':
                    key = 'table-wrap'
                if key == 'bibr':
                    key = 'ref'
                
                label = ""
                
                if key == 'fig' or key == 'table-wrap':
                    y = soup.find(key, {"id": tag_id})
                    print (y.find('label').text + y.find('caption').text, '\n')
                        
    def tokenizeCaption(self, caption_text):
#        caption_text = caption_text.replace(u'\xa0', u' ')
        import unidecode
        caption_text = unidecode.unidecode(caption_text)
        tokenized_caption = self.sentenceTokenizer(caption_text)
        store_caption = ""
        for token in tokenized_caption:
            store_caption += token
        
        return store_caption
    
    def getCaptions(self):
        for ref in soup.find_all('xref'):
            original_key = ref['ref-type']
            tag_id = ref['rid']
            key = original_key
            
            if key in self.tags_list:
                if key == 'table':
                    key = 'table-wrap'
                if key == 'bibr':
                    key = 'ref'
                
                label = ""
                store_caption = ""
                if tag_id not in self.captions_dict:
#                    y = soup.find(key, {"id": tag_id})
                    if key == 'fig' or key == 'table-wrap':
                        y = soup.find(key, {"id": tag_id})
                        if y is not None:
                            lab = y.find('label')
                            lab.string = lab.string#+ ': '
                            lab.string = self.tokenizeCaption(lab.text)
                            label = lab.text
                            capt = y.find('caption')
                            tokenized_caption = self.tokenizeCaption(capt.text)
    #                        print (tokenized_caption, '\n')
                            if capt.string is not None:
                                capt.string = tokenized_caption
                            elif capt.findChild().string is not None:
                                capt.findChild().string = tokenized_caption
                            store_caption = y.find('label').text + ' ' + y.find('caption').text.replace('\n', '')
    
                            self.captions_dict[tag_id] = store_caption
                            self.dict_markers_ids[tag_id].append(label)
    
    '''Sentence segmentation of the files
    # 
    # Process - 
    # 1. Segment the soup text with the markers present. Output is a list of sentences, all_sent_parsed.
    # 2. Use the same segmentation technique to clean the text without the markers, i.e. original text. Output is a list of sentences with the same indices as the previous list of segmented sentences, all_sent_original. 
    # 3. While segmenting the original text, create another list that stores the character length of each sentence at the corresponding index, sent_ref_points
    '''
            
    def sentenceTokenizer(self, input_text):
        import unidecode
        original_content_text = unidecode.unidecode(input_text)
#        original_content_text = input_text
        content_text = re.sub('\s\s+', ' ', original_content_text)
        content_text = re.sub(' +', ' ', content_text)#' +', ' '
         
        punkt_param = PunktParameters()
        abbreviation = self.tags_list
        punkt_param.abbrev_types = set(abbreviation)
        tokenizer = PunktSentenceTokenizer(punkt_param)
        tokenized_output = tokenizer.tokenize(content_text)
        
        return tokenized_output
    
    def segmentSentences(self, doc_text):
        parsed_tokens = self.sentenceTokenizer(doc_text)
        
        for item in parsed_tokens:
            s = item.strip()
            self.all_sent_parsed.append(s)
            self.sent_ref_points.append(self.curr_ref_points)
            self.curr_ref_points += len(s) + 2      # Added 2 to the length as BRAT tool takes \n as 2 characters.
            # There is a \n at the end of every sentence. 

    def getDirectReferences(self):
        for key in self.dict_markers_ids:
            for i in range(1, len(self.dict_markers_ids[key]) - 1):
                marker_key = self.dict_markers_ids[key][i]
                for index, sent in enumerate(self.all_sent_parsed):
                    if marker_key in sent:
                        curr_text = sent.replace(marker_key, '')
                        self.rids_dict[marker_key] = index
#                        self.updated_rids_dict[marker_key] = curr_text 
                        self.all_sent_parsed[index] = curr_text
                
        
        for key in self.rids_dict:
            all_sent_indx = self.rids_dict[key]
            if key not in self.updated_rids_dict:
                self.updated_rids_dict[key] = []
                
            self.updated_rids_dict[key] = self.all_sent_parsed[all_sent_indx]
        
    '''
    Finally, create the compiled dictionary of all entities - 
    1. Reference Type
    2. Reference Object Identity,e.g. Table 1, Table 2, Fig 1, Fig 2, etc.
    3. Caption Text,
    4. Caption Ref Start and End Points
    5. All direct references and their corresponding start and end points
    '''
    def findSpanInSentence(self, file_text, searchText):
        first_9_words = ' '.join(searchText.split()[:10])
        start_span = file_text.find(searchText)
        clean_tokenized_txt_sentences = self.sentenceTokenizer(file_text)
        
        found_sentence = ""
        if (start_span < 0):
            for sentence in clean_tokenized_txt_sentences:
                if first_9_words in file_text:
                    found_sentence = sentence
                    break
            start_span = file_text.find(found_sentence) 
        else:
            found_sentence = searchText
            
        end_span = start_span + len(found_sentence)  
        
        return start_span, end_span
    
    def compileDRefCaptions(self, path):
        f = open(path + self.filename + ".txt", "r")
        read_text = f.read()
        
        for key in self.updated_rids_dict:
            for marker_keys in self.dict_markers_ids:
                if key in self.dict_markers_ids[marker_keys]:
                    if marker_keys not in self.captions_DRef_dict:
                        self.captions_DRef_dict[marker_keys] = []
                        xref_type = self.dict_markers_ids[marker_keys][0]
                        xref_object = self.dict_markers_ids[marker_keys][-1]
                        
                        self.captions_DRef_dict[marker_keys].append(xref_type)
                        self.captions_DRef_dict[marker_keys].append(xref_object)
                    
                        if marker_keys in self.captions_dict:
                            object_caption = self.captions_dict[marker_keys]
#                            caption_start_span = read_text.find(object_caption)
#                            caption_end_span = caption_start_span + len(object_caption)
                            caption_start_span, caption_end_span = self.findSpanInSentence(read_text, object_caption)
                            object_caption_len = ((caption_start_span, caption_end_span))
                            self.captions_DRef_dict[marker_keys].append(object_caption)
                            self.captions_DRef_dict[marker_keys].append(object_caption_len)

                    direct_ref_text = self.updated_rids_dict[key][0]
#                    ref_start_span = read_text.find(direct_ref_text)
#                    ref_end_span = ref_start_span + len(direct_ref_text)
                    ref_start_span, ref_end_span = self.findSpanInSentence(read_text, direct_ref_text)
                    direct_ref_len = ((ref_start_span, ref_end_span))
                    self.captions_DRef_dict[marker_keys].append(direct_ref_text)
                    self.captions_DRef_dict[marker_keys].append(direct_ref_len)
                    
    def createAllSentencesFile(self, path):
        file1 = open(path + self.filename + ".txt", "w+b") #, encoding = "utf-8")
        self.all_sent_original = self.all_sent_parsed
        
        for sentence in self.all_sent_original:
            file1.write(str.encode(sentence) + b'\n')
        file1.close()
        
    def createJSONFile(self, soup_original, path, subdir):
        soup_original.find_all('xref')
        '''
        Step 1. Looking up the reference tags in the document and creating 2 dictionaries - 
        
        1. ref_tags {ref-type(key): rid_list (value)} - This dict will contain all the tags with ref-types that are in the list ['bibr (Citation References)', 'aff (Author/Affiliation References)', 'fig (Figure References)',
        'table (Table References)'] with their corresponding rid(s) for detailed Text lookups in the nxml document.
        
        2. rid_mappings {each rid (key) : text associated with that ref tag (value)} - This dict will contain all the rid values that have been stored in the above dict
        with their corresponding texts for future lookups.
        
        
        Step 2. If the ref-type is 'bibr', save its key in ref_tags as 'ref', and if the ref-type is 'table', save its key in ref_tags 
        as 'table-wrap' because that's how the nxml document has them represented for the details. 
        '''
        
        xref = soup_original.find_all('xref')
        ref_tags = {}
        rid_mappings = {}
        tags_list = ['table', 'fig']
        count = 0
        
        for ref in xref:
            original_key = ref['ref-type']
            key = original_key
            if key == "bibr":
                key = "ref"
            elif key == "table":
                key = "table-wrap"
            value = ref['rid']
        
            if original_key in tags_list:
                if key not in ref_tags:
                    ref_tags[key] = []
                    
                ref_tags[key].append(value)
                count+=1
                
                rid_mappings[value] = ref.get_text()
        
        pdf_file = self.filename + '.pdf'
        json_dict = {"document_name": str(pdf_file), "caption" : {}}
        if "caption" in json_dict:
            for i in range(count):
                json_dict["caption"][str(i+1)] = {}

        index = 1
        for key in ref_tags:
            for tag_id in ref_tags.get(key):
                y = soup_original.find(key, {"id": tag_id})
                
                if y == None and key == "supplementary-material":
                    y = soup_original.find("sec", {"id": tag_id})
                    
                caption = None 
                href = None
                ref_type = None
                number = None
        
                if key == "fig":
                    caption = y.find("label").text + " : " + y.find("caption").text
                    href = y.find("graphic")["xlink:href"]
                    ref_type = "Figure"
                    number = y.find("label").text.split(" ")[1]
                elif key == "table-wrap":
                    caption = y.find("label").text + " : " + y.find("caption").text
                    ref_type = "Table"
                    number = y.find("label").text.split(" ")[1]
                elif key == "supplementary-material":
                    ref_type = "Supplementary"
                    caption = y.text
                    href = y.find("media")["xlink:href"]
                else:
                    ref_type = "General"
                    caption = y.text
                
                if href is not None:
                    href = href + '.jpg'
                
                authors = []
                publication = []
                if ref_type == "Citation":
                        s = re.split('\n\n\n', caption)
                        curr_citation = []
                        while '' in s:
                            s.remove('')
                        for item in s:
                            item = " ".join(re.split('\n', item))
                            curr_citation.append(item)
                    
                        authors.append(curr_citation[:-1])
                        publication.append(curr_citation[-1])
                else:
                    caption = "".join(re.split('\n', caption))
                
                if str(index) in json_dict["caption"]:
                    json_dict["caption"][str(index)]["type"] = ref_type
                    json_dict["caption"][str(index)]["number"] = number
                    json_dict["caption"][str(index)]["subnumber"] = ""
                    if ref_type == "Citation":
                        json_dict["caption"][str(index)]["authors"] = [s for Au in authors for s in Au]
                        json_dict["caption"][str(index)]["publication"] = publication[0] 
                    else:
                        json_dict["caption"][str(index)]["caption_text"] = caption
                        json_dict["caption"][str(index)]["sub-caption text"] = ""
                          
                        if ref_type == "Figure" or ref_type == "supplementary-material":
                            href_path = os.getcwd() + '/' + href
                            href_path = href_path.replace(os.sep, '/')
                            json_dict["caption"][str(index)]["path-to-media"] = os.path.relpath(subdir).replace(os.sep, '/') + 'images/' + os.path.relpath(href_path)
                index += 1
    
        with open(path + self.filename + '.json', 'w') as fp:
            json.dump(json_dict, fp)

    def createANNfile(self, path):
        print('\n***** New ANN File creation.********')
        f_ann = open(path + self.filename + '.ann', 'w+', encoding = "utf8")
        t_ind = 0
        a_ind = 0
        for key in self.captions_DRef_dict:
            t_ind += 1
            a_ind += 1
            t_num = "T" + str(t_ind)
            add_text = "" 
            add_text = add_text + t_num
            add_text = add_text + "\tCaption "
            ref_points = self.captions_DRef_dict[key][3]
            add_text += str(ref_points[0]) + " " + str(ref_points[1])
            add_text += "\t" + self.captions_DRef_dict[key][2] + "\n"
            
            ref_type, ref_num = self.captions_DRef_dict[key][1].split(" ")
            add_text = add_text + "A" + str(a_ind) + "\tType " + t_num + " " + ref_type + "\n"   
            a_ind += 1
            add_text = add_text + "A" + str(a_ind) + "\tNum " + t_num + " " + ref_num + "\n\n"
            a_ind += 1
            f_ann.write(add_text)
            
            for i in range(4, len(self.captions_DRef_dict[key]), 2):
                t_ind += 1
                sub_t_num = "T" + str(t_ind)
                add_text = "" 
                add_text = add_text + sub_t_num
                add_text = add_text + "\tReference "
                sub_ref_points = self.captions_DRef_dict[key][i+1]
                add_text += str(sub_ref_points[0]) + " " + str(sub_ref_points[1]) + "\t"
                add_text += self.captions_DRef_dict[key][i] + "\n"
                add_text = add_text + "A" + str(a_ind) + "\tRefType " + sub_t_num + " Direct\n"   
                a_ind += 1
                add_text = add_text + "A" + str(a_ind) + "\tType " + sub_t_num + " " + ref_type + "\n"   
                a_ind += 1
                add_text = add_text + "A" + str(a_ind) + "\tNum " + sub_t_num + " " + ref_num + "\n\n"
                a_ind += 1
                f_ann.write(add_text)
        f_ann.close()

'''
---------------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------
                                            DRIVER'S CODE
---------------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------
'''        
rootdir = 'data/'
img_ext = ('.jpg', '.gif', '.png', '.tif')
log_file = open('log_file.txt', 'w+', encoding = "utf8")

for subdir, dirs, files in os.walk(rootdir):
    for curr_file in files:
        if curr_file.lower().endswith('.nxml'):  
            print('Processing file: ', subdir + '/' + curr_file, '\n')
            infile = open(subdir + '/' + curr_file, "r")
#subdir = 'PMC3016212/'
#curr_file = '228_2010_Article_901.nxml'
#print('Processing file: ', subdir + '/' + curr_file, '\n')
#infile = open(subdir + '/' + curr_file, "r")
            soup = BeautifulSoup(infile, 'xml')
            soup_original = soup
            soup_copy = soup
            filename = os.path.splitext(curr_file)[0]
            
            curr_doc = nxmlParser()
            curr_doc.filename = filename
            
            curr_doc.addMarkersToXREF()
            #            curr_doc.addMarkersToCaptions()
            
            '''
            Segment the Sentences
            '''
            soup_copy = soup_original
            parsed_doc_text = soup.get_text()
            curr_doc.segmentSentences(parsed_doc_text)
            
            curr_doc.getDirectReferences()
            curr_doc.getCaptions()
            
            # Verify that all three lists have the same size
            #            print (len(curr_doc.sent_ref_points), len(curr_doc.all_sent_parsed), len(curr_doc.all_sent_original) )
            
            '''
            Creating the all_sentences.txt file. 
            Segment the sentences and dump each sentence on one line of the file.
            '''
            try: 
                os.mkdir(subdir + "/annotation") 
            except(FileExistsError): 
                pass
            currPath = subdir + '/annotation/'
            #            print(currPath,'\n')
            
            curr_doc.createAllSentencesFile(currPath)
            #            curr_doc.showCaptions()
            curr_doc.compileDRefCaptions(currPath)
            d = curr_doc.captions_DRef_dict
            print (d, '\n\n')
            
            curr_doc.createLogFileDicts()
            writeToLogFile(currPath, curr_doc.filename, curr_doc.log_file_references, curr_doc.log_file_caption)

            curr_doc.createJSONFile(soup_original, currPath, subdir)
            curr_doc.createANNfile(currPath)
            print('\nFinished processing file: ', subdir + '/' + curr_file, '\n')
            print('----------------------------------------\n\n')
#        elif curr_file.lower().endswith(img_ext):
#            try:
#                os.mkdir(subdir + '/images')
#            except(FileExistsError):
#                pass
#            imgPath = subdir + '/images/'
#            shutil.move(subdir + '/' + curr_file, imgPath)

log_file.close()