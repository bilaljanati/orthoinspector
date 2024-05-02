import os
import sys
from flask import Flask, request, render_template, Blueprint, abort, redirect, jsonify, Response, url_for
import yaml
import json
import re

curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f'{curdir}/src')

from src.warehouse import Warehouse
from src.geneontology import GeneOntology
from src.taxonomy import Taxonomy
from src.interpro import Interpro
from src.tasks import submit_task, check_task
from api import bp as bpapi


with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
wh = Warehouse(config['warehouse'])
go = GeneOntology(config['geneontology'])
taxo = Taxonomy()
interpro = Interpro()

app = Flask(__name__, static_url_path=f"/{config['prefix']}/static")
bp = Blueprint('bp', __name__)

def regex_match(string, pattern):
    return re.match(pattern, string) is not None

app.jinja_env.filters['regex_match'] = regex_match

@bp.context_processor
def inject_globals():
    return config

@bp.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@bp.route("/")
def home():
    return render_template('index.html', dblist=wh.get_dblist())

@bp.route("/<database>")
def db_home(database):
    db = wh.get_db(database)
    if not db:
        abort(404)
    status = db.get_status()
    stats = db.get_stats()
    species = db.get_species_list()
    return render_template('dbindex.html', db=db.get_info(), status=status, stats=stats, species=species)

@bp.route("/<database>/tree/sun")
def species_tree_sun(database):
    db = wh.get_db(database)
    if not db:
        abort(404)
    tree = db.get_sun_tree(maxdepth=12)
    return jsonify(tree)

@bp.route("/<database>/tree/profile")
def species_tree_profile(database):
    db = wh.get_db(database)
    if not db:
        abort(404)
    tree = db.get_profile_tree()
    return jsonify(tree)

@bp.route("/<database>/search/protein")
def search_protein(database):
    db = wh.get_db(database)
    if not db:
        abort(404)
    pattern = request.args.get("term")
    return jsonify(db.search_protein(pattern))

@bp.route("/<database>/protein/random")
def random_protein(database):
    db = wh.get_db(database)
    if not db:
        abort(404)
    access = db.get_random_access()
    return redirect(url_for('bp.protein', database=database, access=access), code=302)

@bp.route("/<database>/protein/<access>")
@bp.route("/<database>/protein/<access>/full")
def protein(database, access):
    db = wh.get_db(database)
    if not db:
        abort(404)
    model_only = not request.base_url.endswith('full')
    if not db.has_models and model_only:
        return redirect(url_for('bp.protein', database=database, access=access), code=302)
    prot = db.get_protein(access)
    if not prot:
        abort(404)
    return render_template('protein.html', db=db.get_info(), protein=prot, model=model_only)

@bp.route("/<dbname>/orthologs/<access>")
@bp.route("/<dbname>/orthologs/<access>/full")
def orthologs(dbname, access):
    db = wh.get_db(dbname)
    if not db:
        abort(404)
    model_only = not request.base_url.endswith('full')
    orthos = db.get_orthologs(access, model=model_only)
    return jsonify(orthos)

@bp.route("/<database>/download/fasta", methods=['POST'])
def download_fasta(database):
    db = wh.get_db(database)
    if not db:
        abort(404)
    access_list = request.form['access_list'].split(',')
    filename = request.form['filename']
    fasta = db.get_fasta(access_list)
    res = Response(fasta, mimetype='text/plain')
    res.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return res

@bp.route("/annotations/go/<access>")
def go_annotations(access):
    return jsonify(go.get_annotations(access))

@bp.route("/annotations/interpro/<access>")
def interpro_annotations(access):
    annots = interpro.get_domains(access)
    if not annots:
        abort(404)
    return jsonify(annots)

# Test route for taxonomy
@bp.route("/taxo/<taxid>")
def taxo_test(taxid):
    if not taxid.isdigit():
        return jsonify([]), 404
    return jsonify(taxo.get_lineage(taxid))

@bp.route("/stats")
def do_stats():
    return render_template('dbstats.html', stats=wh.get_stats())

@bp.route("/<database>/blastsearch", methods=['GET', 'POST'])
def blast_search(database):
    db = wh.get_db(database)
    if not db:
        abort(404)
    query = request.form['query'] if request.method == 'POST' else ''
    return render_template('blastsearch.html', db=db.get_info(), query=query)

@bp.route("/<database>/blastsearch/submit", methods=['POST'])
def blast_search_run(database):
    db = wh.get_db(database)
    if not db:
        abort(404)
    res = submit_task(config['worker_pool']['host'], 'blast_search', request.form.to_dict())
    return jsonify(res)

@bp.route("/<database>/blastsearch/result/<taskid>")
def blast_search_res(database, taskid):
    db = wh.get_db(database)
    if not db:
        abort(404)
    res = check_task(config['worker_pool']['host'], taskid)
    return jsonify(res)

@bp.route("/<database>/profilesearch")
def profile_search(database):
    db = wh.get_db(database)
    if not db:
        abort(404)
    return render_template('profilesearch.html', db=db.get_info())

@bp.route("/<database>/profilesearch/result", methods=['POST'])
def profile_search_run(database):
    db = wh.get_db(database)
    if not db:
        abort(404)
    params = {'database': database}
    fields = ['query', 'present', 'absent']
    for key in ['query', 'present', 'absent']:
        params[key] = request.form[key]
    res = submit_task(config['worker_pool']['host'], 'profile_search', params)
    parsed_params = {k: json.loads(v) for k, v in request.form.items() if k in ['query', 'display']}
    return render_template('profilesearchresult.html', db=db.get_info(), params=parsed_params, taskid=res['id'])

@bp.route("/<database>/profilesearch/result/<taskid>")
def profile_search_res(database, taskid):
    db = wh.get_db(database)
    if not db:
        abort(404)
    res = check_task(config['worker_pool']['host'], taskid)
    return jsonify(res)

@bp.route("/<database>/data")
def data(database):
    db = wh.get_db(database)
    if not db:
        abort(404)
    return render_template('data.html', db=db.get_info(), species=db.get_species_list(), base_url=config['warehouse']['data_server_url'])

app.register_blueprint(bp, url_prefix=config['prefix'])
app.register_blueprint(bpapi, url_prefix=config['prefix']+'/api')
