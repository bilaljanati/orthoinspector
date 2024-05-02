from functools import lru_cache


# FRONTEND
def submit_task(host, tasktype, params):
    import requests
    import json
    url = f"http://{host}/submit"
    params['type'] = tasktype
    response = requests.post(url, params)
    return json.loads(response.text)

def check_task(host, taskid):
    import requests
    import json
    url = f"http://{host}/result/{taskid}"
    response = requests.get(url)
    return json.loads(response.text)

# BACKEND
def do_work(val):
    func = val.pop('type')
    try:
        return globals()[func](**val)
    except Exception:
        return False

def get_config():
    import yaml
    with open('config.yml', 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

def get_warehouse(config):
    from src.warehouse import Warehouse
    return Warehouse(config['warehouse'])

def profile_search(database, query, present, absent):
    import json
    taxid = json.loads(query).get('taxid')
    present = [p['taxid'] for p in json.loads(present)]
    absent = [p['taxid'] for p in json.loads(absent)]

    config = get_config()
    wh = get_warehouse(config)
    db = wh.get_db(database)

    return db.search_by_profile(taxid, present, absent)

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
