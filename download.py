import os
import json
import requests
import argparse
from tqdm import tqdm
from urllib import request, error

def parse_args():
    desc="download bird audios"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--name', type=str, required=True, help="[1] name of one bird species; [2] file of bird species spaced by '\\n' ")
    return parser.parse_args()

def metadata(filt):
    filt_path = list()
    filt_url = list()
    print("Retrieving metadata...")

    # Scrubbing input for file name and url
    for f in filt:
        filt_url.append(f.replace(' ', '%20'))
        filt_path.append((f.replace(' ', '')).replace(':', '_').replace("\"",""))

#     path = 'dataset/metadata/' + ''.join(filt_path)
    paths = ['dataset/metadata/' + pa for pa in filt_path]

    # Overwrite metadata query folder 
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)

    # Save all pages of the JSON response    
    for fu in filt_url:
        path = 'dataset/metadata/' + fu.replace('%20','')
        page, page_num = 1, 1
        while page < page_num + 1:
            url = 'https://www.xeno-canto.org/api/2/recordings?query={0}&page={1}'.format(fu, page)
            print(url)
            try:
                r = request.urlopen(url)
            except error.HTTPError as e:
                print('An error has occurred: ' + str(e))
                exit()
            print("Downloading metadate page " + str(page) + "...")
            data = json.loads(r.read().decode('UTF-8'))
            filename = path + '/page' + str(page) + '.json'
            with open(filename, 'w') as saved:
                json.dump(data, saved)
            page_num = data['numPages']
            page += 1

    # Return the path to the folder containing downloaded metadata
    return paths

def listdir_nohidden(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f

def download(filt):
    
    all_recordings = []
    print("Downloading all recordings for query...")

    # Retrieve metadata to parse for download links
    paths = metadata(filt)

    # Enumerate list of metadata folders
    path_list = listdir_nohidden("dataset/metadata/")
    redown = set()
    
    # Check for any in_progress files in the metadata folders
    for p in path_list:
        check_path = "dataset/metadata/" + str(p)
        if os.path.isfile(check_path):
            continue

        if os.path.exists(check_path + "/in_progress.txt"):
            curr = open(check_path + "/in_progress.txt")
            line = int(curr.readline())
            if line not in redown:
                redown.add(line)
            curr.close()
    
    for pa in paths:
        page = 1
        with open(pa + '/page' + str(page) + ".json", 'r') as jsonfile:
            data = json.loads(jsonfile.read())
            
        # init audio directory and collect data
        if int(data['numRecordings']) > 0:
            bird_name = data['recordings'][0]['en'].replace(' ','')
            audio_dir = 'dataset/audio/' + bird_name
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)
        all_recordings += data['recordings']
        page_num = data['numPages']

        # combine multiple pages for multiprocessing
        if page_num > 1:
            for i in range(2, page_num+1):
                with open(pa + '/page' + str(i) + ".json", 'r') as jsonfile:
                    new_data = json.loads(jsonfile.read())
                    all_recordings += new_data['recordings']
                
    print("Found " + str(len(all_recordings)) + " recordings for given queries, downloading...") 
    
    for curr_rec in tqdm(all_recordings, desc="downloading"):
        url = curr_rec['file']
        # redirect url and update real url
        re_url = requests.get(url, allow_redirects=True).url
        name = (curr_rec['en']).replace(' ', '')
        track_id = curr_rec['id']

        # Keep track of the most recently downloaded file
        recent = open('dataset/audio/' + name + "/in_progress.txt", "w")
        recent.write(str(track_id))
        recent.write("\n")
        recent.close()

        audio_path = 'dataset/audio/' + name + '/'
        audio_file = str(track_id) + '.mp3'

        # If the track has been included in the progress files, it can be corrupt and must be redownloaded regardless
        if int(track_id) in redown:
            print("File " + str(track_id) + ".mp3 must be redownloaded since it was not completed during a previous query.")
            print("Downloading " + str(track_id) + ".mp3")
            request.urlretrieve(url, audio_path + audio_file)
            continue

        if not os.path.exists(audio_path):
            os.makedirs(audio_path)

        # If the file exists in the directory, we will skip it
        if os.path.exists(audio_path + audio_file):
            continue

        request.urlretrieve(url, audio_path + audio_file)

        # If the method has completed successfully, then we can delete the in_progress file
        os.remove('dataset/audio/' + name + "/in_progress.txt")

if __name__ == '__main__':
    
    args = parse_args()
    isFile = os.path.isfile(args.name)
    if isFile:
        with open(args.name, 'r') as f:
            all_birds = [n.lower() for n in f.read().split('\n') if n]
    else:
        all_birds = [args.name.lower()]
    download(all_birds)