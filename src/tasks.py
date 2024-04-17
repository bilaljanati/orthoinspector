from functools import lru_cache


# FRONTEND
def submit_task(port, tasktype, params):
    import requests
    import json
    url = f'http://localhost:{int(port)}/submit'
    params['type'] = tasktype
    response = requests.post(url, params)
    return json.loads(response.text)

@lru_cache(32)
def check_task(port, taskid):
    import requests
    import json
    url = f'http://localhost:{int(port)}/result/{taskid}'
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
