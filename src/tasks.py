from functools import lru_cache
import traceback


# FRONTEND
def submit_task(host, tasktype, params):
    import requests
    import json
    url = f"http://{host}/submit"
    postdata = {
        "type": tasktype,
        "data": json.dumps(params)
    }
    response = requests.post(url, postdata)
    return json.loads(response.text)

def check_task(host, taskid):
    import requests
    import json
    url = f"http://{host}/result/{taskid}"
    response = requests.get(url)
    return json.loads(response.text)

# BACKEND
def do_work(data):
    import json
    func = data["type"]
    params = json.loads(data["data"])
    
    try:
        return globals()[func](**params)
    except Exception:
        traceback.print_exc()
        return False

def get_config():
    import yaml
    with open('config.yml', 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

def get_warehouse(config):
    from src.warehouse import Warehouse
    return Warehouse(config['warehouse'])

def profile_search(database, release, query, present, absent):
    import json
    taxid = query['taxid']
    present = [p['taxid'] for p in present]
    absent = [p['taxid'] for p in absent]

    config = get_config()
    wh = get_warehouse(config)
    db = wh.get_db(database, release)

    prots = db.search_by_profile(taxid, present, absent)
    if len(prots) > 0 and db.has_distances:
        prots = cluster_result(db, prots)
    return prots

def blast_check_db(database):
    import os
    import time
    config = get_config()
    wh = get_warehouse(config)
    db = wh.get_db(database)
    if not db:
        return False
    dbdir = f"{config['worker_pool']['blast_db_dir']}/{database}"
    lockfile = f"{dbdir}/lock"
    if os.path.exists(dbdir):
        while os.path.exists(lockfile):
            time.sleep(10)
        return os.path.exists(f'{dbdir}/db.phr') or os.path.exists(f'{dbdir}/db.pal')
    os.makedirs(dbdir)
    open(lockfile, "a").close()
    import subprocess
    cmd = '/biolo/blast/bin/makeblastdb'
    fasta = f'{dbdir}/proteomes.fasta'
    with open(fasta, 'w') as f:
        for batch in db.get_proteome(batch_size=2048):
            f.write(batch)
            f.write('\n')
            f.flush()
    cmd = f'/biolo/blast/bin/makeblastdb -dbtype prot -title {database} -in {fasta} -out {dbdir}/db'
    process = subprocess.Popen(cmd, shell=True)
    return_code = process.wait()
    os.remove(fasta)
    os.remove(lockfile)
    return os.path.exists(f'{dbdir}/db.phr') or os.path.exists(f'{dbdir}/db.pal')

def blast_search(database, query, cutoff):
    if not blast_check_db(database):
        raise Exception(f"Unknown database {database}")
    import subprocess
    config = get_config()
    dbdir = f"{config['worker_pool']['blast_db_dir']}/{database}/db"
    cmd = f'/biolo/blast/bin/blastp -db {dbdir} -outfmt 0 -evalue {cutoff} -num_descriptions 100 -num_alignments 100'
    if query[0] != '>':
        query = ">QUERY\n" + query
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate(input=query.encode())
    return_code = process.wait()
    if return_code != 0:
        raise Exception(stderr)
    return stdout.decode('utf-8')

def fetch_protein_edges(db, access_list):
    if not db or not db.has_distances:
        return False
    return db.get_distances(access_list)

def cluster_result(db, proteins):
    proteins = {p['access']: p for p in proteins}
    access_list = proteins.keys()
    edges = fetch_protein_edges(db, access_list)
    if not edges:
        return False
    import networkx as nx
    g = nx.Graph()
    g.add_nodes_from(access_list)
    for edge in edges:
        u, v = edge['a'], edge['b']
        g.add_edge(u, v)
    components = list(nx.connected_components(g))
    clusters = [s for s in components if len(s) > 1]
    default_cluster = {s.pop() for s in components if len(s) == 1}
    # replace with actual rows
    clusters = [[proteins[access] for access in c] for c in clusters]
    default_cluster = [proteins[access] for access in default_cluster]
    return {'clusters': clusters, 'singletons': default_cluster}
