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
    parser.add_argument('--process-ratio', type=float, default=0.8, help="float[0~1], define cpu utilities in downloading audios [default: 0.8]")
    return parser.parse_args()

def metadata(filt):
    filt_path = list()
    filt_url = list()
    print("Retrieving metadata...")

    # Scrubbing input for file name and url
    for f in filt:
        filt_url.append(f.replace(' ', '%20'))
        filt_path.append((f.replace(' ', '')).replace(':', '_').replace("\"",""))

    paths = ['dataset/metadata/' + pa for pa in filt_path]

    # Overwrite metadata query folder 
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    # Save all pages of the JSON response    
    for fu in tqdm(filt_url, desc="retrieving metadata"):
        path = 'dataset/metadata/' + fu.replace('%20','')
        page, page_num = 1, 1
        while page < page_num + 1:
            url = 'https://www.xeno-canto.org/api/2/recordings?query={0}&page={1}'.format(fu, page)
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

def listdir_nohidden(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f

def download(pid, pTotal, metadata_paths):
    isFirst = True
    
    all_recordings = []

    # Retrieve metadata to parse for download links
    paths = metadata_paths

    # Enumerate list of metadata folders
    path_list = listdir_nohidden("dataset/metadata/")
    redown = set()
    
    # Check for any in_progress files in the metadata folders
    for p in path_list:
        check_path = "dataset/metadata/" + str(p)
        if os.path.isfile(check_path):
            continue
    
    for pa in paths:
        page = 1
        with open(pa + '/page' + str(page) + ".json", 'r') as jsonfile:
            data = json.loads(jsonfile.read())
            
        # init audio directory and collect data
        if int(data['numRecordings']) > 0:
            bird_name = data['recordings'][0]['en'].replace(' ','')
            audio_dir = 'dataset/audio/' + bird_name
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir, exist_ok=True)
        all_recordings += data['recordings']
        page_num = min(3, data['numPages'])

        # combine multiple pages for multiprocessing
        if page_num > 1:
            for i in range(2, page_num+1):
                with open(pa + '/page' + str(i) + ".json", 'r') as jsonfile:
                    new_data = json.loads(jsonfile.read())
                    all_recordings += new_data['recordings']
                    
    # assign portion to each process
    portion = len(all_recordings) // pTotal
    if pid == 0:
        all_recordings = all_recordings[:portion]
    elif pid == pTotal - 1:
        all_recordings = all_recordings[portion*pid:]
    else:
        all_recordings = all_recordings[portion*pid: portion*(pid+1)]
    
    for curr_rec in tqdm(all_recordings, desc="process %d"%os.getpid()):
        if isFirst:
            with open('kill.sh','a') as f:
                f.write('kill -9 %d\n'%os.getpid())
            isFirst = False
            
        url = curr_rec['file']
        name = (curr_rec['en']).replace(' ', '')
        track_id = curr_rec['id']

        audio_path = 'dataset/audio/' + name + '/'
        audio_file = str(track_id) + '.mp3'

        # If the track has been included in the progress files, it can be corrupt and must be redownloaded regardless
        if int(track_id) in redown:
            print("File " + str(track_id) + ".mp3 must be redownloaded since it was not completed during a previous query.")
            print("Downloading " + str(track_id) + ".mp3")
            request.urlretrieve(url, audio_path + audio_file)
            continue

        if not os.path.exists(audio_path):
            os.makedirs(audio_path, exist_ok=True)

        # If the file exists in the directory, we will skip it
        if os.path.exists(audio_path + audio_file):
            continue

        try:
            request.urlretrieve(url, audio_path + audio_file)
        except:
            if url:
                print('Bad url: %s'%url)
                with open('bad_urls.txt','a') as f:
                    f.write(url+'\n')

        
if __name__ == '__main__':
    with open('kill.sh','w') as f:
        f.write('')
    
    with open('bad_urls.txt','w') as f:
        f.write('')
    
    args = parse_args()
    isFile = os.path.isfile(args.name)
    if isFile:
        with open(args.name, 'r') as f:
            all_birds = [n.lower() for n in f.read().split('\n') if n]
    else:
        all_birds = [args.name.lower()]
        
    # retrieve metadata
    metadata_path = metadata(all_birds)
    
    # multiprocessing
    worker_count = int(multiprocessing.cpu_count() * args.process_ratio)
    worker_pool = []
    for i in range(worker_count):
        p = Process(target=download, args=(i, worker_count, metadata_path))
        p.start()
        worker_pool.append(p)
    for p in worker_pool:
        p.join()  # Wait for all of the workers to finish.

    # Allow time to view results before program terminates.
    a = input("Finished")
