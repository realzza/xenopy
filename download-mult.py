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
    parser.add_argument('--time-limit', type=float, default=15, help="length of downloaded audio of each birds")
    parser.add_argument('--process-ratio', type=float, default=0.8, help="float[0~1], define cpu utilities in downloading audios [default: 0.8]")
    parser.add_argument('--output', type=str, default="dataset/audio/", help="path of output directory")
    return parser.parse_args()

def metadata(pid, filt, nproc, path_only=False):
    isFirst = True
    
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
    
    if path_only:
        return paths

    # assign portion to each process
    portion = len(filt_url) // nproc
    if pid == 0:
        filt_url = filt_url[:portion]
    elif pid == nproc - 1:
        filt_url = filt_url[portion*pid:]
    else:
        filt_url = filt_url[portion*pid: portion*(pid+1)]
            
    # Save all pages of the JSON response    
    for fu in tqdm(filt_url, desc="process %d"%os.getpid()):
        if isFirst:
            with open('kill_meta.sh','a') as f:
                f.write('kill -9 %d\n'%os.getpid())
            isFirst = False
        
        path = 'dataset/metadata/' + fu.replace('%20','')
        page, page_num = 1, 1
        while page < page_num + 1:
            url = 'https://www.xeno-canto.org/api/2/recordings?query={0}&page={1}'.format(fu, page)
            attempts = 0
            while attempts < 3:
                try:
                    r = request.urlopen(url)
                    break
                except error.HTTPError as e:
                    attempts += 1
                    if attempts == 3:
                        print('An error has occurred: ' + str(e))
                        print('Bad filter url: %s'%fu)
                    
#             print("Downloading metadate page " + str(page) + "...")
            data = json.loads(r.read().decode('UTF-8'))
            filename = path + '/page' + str(page) + '.json'
            with open(filename, 'w') as saved:
                json.dump(data, saved)
            # restrict recording number to 1500 recordings/species
            page_num = min(3, data['numPages'])
            # no restrict
            # page_num = data['numPages']
            page += 1

    # Return the path to the folder containing downloaded metadata
    return paths

def str2seconds(time_str):
    return sum(x * int(t) for x, t in zip([60, 1], time_str.split(":"))) 

def listdir_nohidden(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f

def download(pid, pTotal, metadata_paths, length_max, output_dir):
    isFirst = True
    
    all_recordings = []

    # Retrieve metadata to parse for download links
    paths = metadata_paths
    # paths = metadata(metadata_paths)

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
        pa_time = 0
        with open(pa + '/page' + str(page) + ".json", 'r') as jsonfile:
            data = json.loads(jsonfile.read())
            
        # init audio directory and collect data
        if int(data['numRecordings']) > 0:
            bird_name = data['recordings'][0]['en'].replace(' ','')
            audio_dir = output_dir + bird_name
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir, exist_ok=True)
        all_recordings += data['recordings']
        page_num = min(1, data['numPages'])

        # combine multiple pages for multiprocessing
        if page_num > 1:
            for i in range(2, page_num+1):
                with open(pa + '/page' + str(i) + ".json", 'r') as jsonfile:
                    new_data = json.loads(jsonfile.read())
                    all_recordings += new_data['recordings']
                    
    all_recordings = sorted(all_recordings, key = lambda i: str2seconds(i['length']))
    all_recordings = [wav for wav in all_recordings if str2seconds(wav['length'])>=6]
    all_rec_new = []
    all_spec2time = {}
    # limit by time
    for rec in tqdm(all_recordings, desc="filtering with length_max"):
        spec_name = "%s_%s"%(rec['gen'],rec['sp'])
        if not spec_name in all_spec2time:
            all_spec2time[spec_name] = 0
        all_spec2time[spec_name] += str2seconds(rec['length'])
        if all_spec2time[spec_name] > length_max:
            continue
        all_rec_new.append(rec)
        
    # print("%d -> %d"%(len(all_recordings), len(all_rec_new)))
    all_recordings = all_rec_new
    
    
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

        audio_path = output_dir + name + '/'
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

        attempts = 0
        while attempts < 10:
            try:
                request.urlretrieve(url, audio_path + audio_file)
                break
            except:
                attempts += 1
                if url and (attempts == 10):
                    print('Bad url: %s'%url)
                    with open('bad_urls.txt','a') as f:
                        f.write(url+'\n')

        
if __name__ == '__main__':
    with open('kill.sh','w') as f:
        f.write('')
        
    with open('kill_meta.sh','w') as f:
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
        
    
    
    # multiprocessing
    worker_count = int(multiprocessing.cpu_count() * args.process_ratio)
    worker_pool = []
    
    # retrieve metadata
    for i in range(worker_count):
        p = Process(target=metadata, args=(i, all_birds, worker_count))
        p.start()
        worker_pool.append(p)
    for p in worker_pool:
        p.join()
        
    metadata_path = metadata(None, all_birds, worker_count, path_only=True)
    
    
    for i in range(worker_count):
        p = Process(target=download, args=(i, worker_count, metadata_path, int(args.time_limit*60), args.output.rstrip('/')+'/'))
        p.start()
        worker_pool.append(p)
    for p in worker_pool:
        p.join()  # Wait for all of the workers to finish.

    # Allow time to view results before program terminates.
    a = input("Finished")
