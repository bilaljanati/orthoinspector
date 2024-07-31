from flask import Flask, Blueprint, abort, jsonify, render_template, request, Response
import os
import sys
import yaml
from functools import wraps

curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f'{curdir}/src')

from src.warehouse import Warehouse

with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
wh = Warehouse(config['warehouse'])

bp = Blueprint('secret', __name__)

@bp.context_processor
def inject_globals():
    return config

def check_auth(username, password):
    return username == 'admin' and password == 'IFftn4K8OSIsU1HdHoDh8GIP0M0D'

def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@bp.route('/')
def home():
    return "Welcome to the public page!"

@bp.route('/dashboard')
@requires_auth
def secret_page():
    data = []
    for release, dbnames in wh.get_dblist().items():
        for dbname in dbnames:
            db = wh.get_db(dbname, release)
            dbinfo = {k: v for k, v in db.get_info().items() if k.startswith('has_')}
            dbinfo['name'] = f"{db.display_name} {db.release}"
            data.append(dbinfo)
    return render_template("dashboard.html", data=data, dblist={})
