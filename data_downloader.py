import os 
import json 
import wget 
import csv
from tqdm import tqdm
import tarfile 
import sys
import multiprocessing
import random 

file_list = []
if not os.path.exists("./oa_file_list.csv"):
    wget.download(url="https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_file_list.csv")

with open("./oa_file_list.csv", 'r') as csvfile:
    csv_content = csv.reader(csvfile, delimiter = ',', quotechar = "|")
    count = 0
    for row in csv_content:
        if count != 0:
            file_list.append(row[0])
        
        count += 1

n_files = 500
file_list = random.sample(file_list, n_files)

def downloader(file_path, des_path):
	web_address = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/"
    url = os.path.join(web_address, file_path)
    wget.download(url=url, out=des_path)

def extractor(file_path, des_path):
    tar = tarfile.open(file_path)
    tar.extractall(path=des_path)
    tar.close 

def main(file):
    tar_path = "./tar_gz/"
    data_path = "./data/"

    if not os.path.exists(tar_path):
        os.mkdir(tar_path)
    if not os.path.exists(data_path):
        os.mkdir(data_path)

    file_name = os.path.split(file)[1]

    downloader(file,tar_path)
    extractor(os.path.join(tar_path, file_name), data_path)

# main("oa_package/e6/58/PMC176545.tar.gz")

pool = multiprocessing.Pool()

# for i in tqdm(pool.imap(main, file_list), total = len(file_list)):
#     pass

# for i in pool.imap(main, file_list):
#     pass

for item in tqdm(file_list):
    main(item)