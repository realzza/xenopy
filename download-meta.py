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
    parser.add_argument('--gen', type=str, default=None, help="genus")
    parser.add_argument('--ssp', type=str, default=None, help="subspecies")
    parser.add_argument('--cnt', type=str, default=None, help="country")
    parser.add_argument('--type', type=str, default=None, help="type")
    parser.add_argument('--rmk', type=str, default=None, help="remark")
    parser.add_argument('--lat', type=str, default=None, help="latitude")
    parser.add_argument('--lon', type=str, default=None, help="longtitude")
    parser.add_argument('--loc', type=str, default=None, help="location")
    parser.add_argument('--box', type=str, default=None, help="box:LAT_MIN,LON_MIN,LAT_MAX,LON_MAX")
    parser.add_argument('--area', type=str, default=None, help="Continent")
    parser.add_argument('--since', type=str, default=None, help="e.g. since:2012-11-09")
    parser.add_argument('--year', type=str, default=None, help="year")
    parser.add_argument('--month', type=str, default=None, help="month")
    parser.add_argument('--output', type=str, default="dataset/metadata/", help="directory to output directory. default: `dataset/metadata/`")
    parser.add_argument('--attempts', type=int, default=8)
    return parser.parse_args()

def metadata(qry, output_dir, n_attempts):
    filt_path = [qry.replace(' ', '%20')]
    filt_url = [qry]
    print("Retrieving metadata...")

    paths = [output_dir + pa for pa in filt_path]

    # Overwrite metadata query folder 
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path.replace("%20",""), exist_ok=True)
            
    # Save all pages of the JSON response    
    for fu in tqdm(filt_url, desc="retrieving metadata"):
        path = output_dir + fu.replace('%20','')
        page, page_num = 1, 1
        while page < page_num + 1:
            url = 'https://www.xeno-canto.org/api/2/recordings?query={0}&page={1}'.format(fu, page)
            attempts = 0
            while attempts < n_attempts:
                try:
                    print(url)
                    r = request.urlopen(url)
                    break
                except error.HTTPError as e:
                    attempts += 1
                    if attempts == n_attempts:
                        print('An error has occurred: ' + str(e))
                        print('Bad filter url: %s'%fu)
                    
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
    query_options = {k:v for k,v in vars(args).items() if v and k != 'output' and k != "attempts"}
    assert query_options, "empty query, please add query options"
    query = '%20'.join(["%s:%s"%(k,v) for k,v in query_options.items()])
    print(query.replace('%20',' '))
        
    # retrieve metadata
    metadata_path = metadata(query, args.output.rstrip('/')+'/', args.attempts)