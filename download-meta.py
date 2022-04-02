import os
import json
import requests
import argparse
import multiprocessing
from tqdm import tqdm
from urllib import request, error
from multiprocessing import Process

def parse_args():
    desc="download bird audios"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--name', type=str, required=True, help="[1] name of one bird species; [2] file of bird species spaced by '\\n' ")
    parser.add_argument('--cnt', type=str, default=None, help="country code. refer to `https://xeno-canto.org/help/search` for more details in search query")
    parser.add_argument('--output', type=str, default="dataset/metadata/", help="directory to output directory. default: `dataset/metadata/`")
    return parser.parse_args()

def metadata(filt, output_dir, CNT):
    filt_path = list()
    filt_url = list()
    print("Retrieving metadata...")

    # Scrubbing input for file name and url
    for f in filt:
        filt_url.append(f.replace(' ', '%20'))
        print(filt_url)
        filt_path.append((f.replace(' ', '')).replace("\"",""))

    paths = [output_dir + pa for pa in filt_path]

    # Overwrite metadata query folder 
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    # Save all pages of the JSON response    
    for fu in tqdm(filt_url, desc="retrieving metadata"):
        path = output_dir + fu.replace('%20','')
        print(path)
        page, page_num = 1, 1
        while page < page_num + 1:
            if not CNT:
                url = 'https://www.xeno-canto.org/api/2/recordings?query={0}&page={1}'.format(fu, page)
            else:
                url = 'https://www.xeno-canto.org/api/2/recordings?query={0}%20{1}&page={2}'.format(fu, CNT, page)
            try:
                r = request.urlopen(url)
            except error.HTTPError as e:
                print('An error has occurred: ' + str(e))
                print('Bad filter url: %s'%fu)
                break
#             print("Downloading metadate page " + str(page) + "...")
            data = json.loads(r.read().decode('UTF-8'))
            filename = path + '/page' + str(page) + '.json'
            with open(filename, 'w') as saved:
                json.dump(data, saved)
            # restrict recording number to 1500 recordings/species
#             page_num = min(3, data['numPages'])
            # no restrict
            page_num = data['numPages']
            page += 1

    # Return the path to the folder containing downloaded metadata
    return paths

if __name__ == '__main__':
    
    args = parse_args()
    isFile = os.path.isfile(args.name)
    if isFile:
        with open(args.name, 'r') as f:
            all_birds = [n.lower() for n in f.read().split('\n') if n]
    else:
        all_birds = [args.name.lower()+'&cnt:'+args.cnt]
        
    # retrieve metadata
    metadata_path = metadata(all_birds, args.output, args.cnt)