import os
import sys
from flask import Flask, request, render_template, Blueprint, abort, redirect, jsonify, Response, url_for
import jinja2
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
from secret import bp as bpsecret


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
    return render_template('404.html', dblist=wh.get_dblist()), 404

@bp.route("/")
def home():
    return render_template('index.html', dblist=wh.get_dblist(), stats=wh.gather_stats())

@bp.route("/<database>/<int:release>")
def db_home(database, release):
    db = wh.get_db(database, release)
    if not db:
        abort(404)
    status = db.get_status()
    stats = db.get_stats()
    species = db.get_species_list()
    return render_template('dbindex.html', dblist=wh.get_dblist(), db=db.get_info(), status=status, stats=stats, species=species)

@bp.route("/<database>/<int:release>/species")
def species_list(database, release):
    db = wh.get_db(database, release)
    if not db:
        abort(404)
    return jsonify(db.get_simple_species_list())

@bp.route("/<database>/<int:release>/tree/sun")
def species_tree_sun(database, release):
    db = wh.get_db(database, release)
    if not db:
        abort(404)
    tree = db.get_sun_tree(maxdepth=12)
    return jsonify(tree)

@bp.route("/<database>/<int:release>/tree/profile")
def species_tree_profile(database, release):
    db = wh.get_db(database, release)
    if not db:
        abort(404)
    tree = db.get_profile_tree()
    return jsonify(tree)

@bp.route("/<database>/<int:release>/search/protein")
def search_protein(database, release):
    db = wh.get_db(database, release)
    if not db:
        abort(404)
    pattern = request.args.get("term")
    return jsonify(db.search_protein(pattern))

@bp.route("/<database>/<int:release>/protein/<access>")
@bp.route("/<database>/<int:release>/protein/<access>/full")
def protein(database, release, access):
    db = wh.get_db(database, release)
    if not db:
        abort(404)
    model_only = not request.base_url.endswith('full')
    if not db.has_models and model_only:
        return redirect(url_for('bp.protein', database=database, release=release, access=access), code=302)
    prot = db.get_protein(access)
    if not prot:
        abort(404)
    return render_template('protein.html', dblist=wh.get_dblist(), db=db.get_info(), protein=prot, model=model_only)

@bp.route("/<dbname>/<int:release>/orthologs/<access>")
@bp.route("/<dbname>/<int:release>/orthologs/<access>/full")
def orthologs(dbname, release, access):
    db = wh.get_db(dbname, release)
    if not db:
        abort(404)
    model_only = not request.base_url.endswith('full')
    orthos = db.get_orthologs(access, model=model_only)
    return jsonify(orthos)

@bp.route("/<dbname>/<int:release>/proximal/<access>")
def proximal(dbname, release, access):
    db = wh.get_db(dbname, release)
    if not db or not db.has_distances:
        abort(404)
    return jsonify(db.get_proximal_proteins(access))

@bp.route("/<dbname>/<int:release>/distribution/<access>")
@bp.route("/<dbname>/<int:release>/distribution/<access>/full")
def distribution(dbname, release, access):
    db = wh.get_db(dbname, release)
    if not db or not db.has_distances:
        abort(404)
    if not db.has_profiles or not db.has_clades:
        abort(404)
    model_only = not request.base_url.endswith('full')
    prot = db.get_protein(access)
    dist = db.build_distribution(prot, model_only=model_only)
    return jsonify(dist)

@bp.route("/<database>/<int:release>/download/fasta", methods=['POST'])
def download_fasta(database, release):
    db = wh.get_db(database, release)
    if not db:
        abort(404)
    access_list = request.form['access_list'].split(',')
    fasta = db.get_fasta(access_list)
    res = Response(fasta, mimetype='text/plain')
    filename = request.form.get('filename', None)
    if filename:
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

@bp.route("/stats")
def do_stats():
    return render_template('dbstats.html', stats=wh.get_stats())

@bp.route("/blast", methods=['GET', 'POST'])
def blast_search():
    query = request.form['query'] if request.method == 'POST' else ''
    return render_template('blastsearch.html', dblist=wh.get_dblist(), query=query)

@bp.route("/blast/submit", methods=['POST'])
def blast_search_run():
    res = submit_task(config['worker_pool']['host'], 'blast_search', request.form.to_dict())
    return jsonify(res)

@bp.route("/blast/result/<taskid>")
def blast_search_res(taskid):
    res = check_task(config['worker_pool']['host'], taskid)
    return jsonify(res)

@bp.route("/profilesearch")
def profile_search():
    return render_template('profilesearch.html', dblist=wh.get_dblist())

@bp.route("/profilesearch/result", methods=['POST'])
def profile_search_run():
    params = {}
    for key in ['database', 'release', 'query', 'present', 'absent', 'display']:
        params[key] = request.form[key]
    params = {k: json.loads(v) for k, v in params.items()}
    job_params = {k: v for k, v in params.items() if k != "display"}
    res = submit_task(config['worker_pool']['host'], 'profile_search', job_params)
    return render_template('profilesearchresult.html', params=params, taskid=res['id'], dblist=wh.get_dblist())

@bp.route("/go/autocomplete/<int:taxid>")
def go_autocomplete(taxid):
    pattern = request.args.get("term")
    return jsonify(go.search_term(pattern, taxid))

@bp.route("/gosearch")
def go_search():
    return render_template('gosearch.html', dblist=wh.get_dblist())

@bp.route("/gosearch/result", methods=['POST'])
def go_search_run():
    params = {}
    for key in ['database', 'release', 'taxid', 'goid', 'species_name', 'goname']:
        params[key] = request.form[key]
    job_params = {k: v for k, v in params.items() if k not in ['species_name', 'goname']}
    res = submit_task(config['worker_pool']['host'], 'go_search', job_params)
    return render_template('gosearchresult.html', params=params, taskid=res['id'], dblist=wh.get_dblist())

@bp.route("/go/match/<database>/<int:release>/<int:taxid>/<goid>")
def go_match(database, release, taxid, goid):
    db = wh.get_db(database, release)
    if not db:
        abort(404)
    return jsonify(db.search_by_go(goid, taxid, goservice=go))

@bp.route("/profilesearch/result/<taskid>")
@bp.route("/gosearch/result/<taskid>")
def profile_search_res(taskid):
    res = check_task(config['worker_pool']['host'], taskid)
    return jsonify(res)

@bp.route("/downloads")
def data():
    return render_template('data.html', dblist=wh.get_dblist(), base_url=config['warehouse']['data_server_url'])

@bp.route("/data/<database>/<int:release>")
def db_data(database, release):
    db = wh.get_db(database, release)
    if not db:
        abort(404)
    data = {
        "species": db.get_species_list()
    }
    return jsonify(data)

@bp.route("/database/<database>/<int:release>")
def db_details(database, release):
    db = wh.get_db(database, release)
    if not db:
        abort(404)
    return render_template("database.html",
                            db=db.get_info(),
                            stats=db.get_stats(),
                            species=db.get_species_list(),
                            dblist=wh.get_dblist()
                        )

@bp.route("/databases")
def db_list():
    return render_template('dblist.html', dblist=wh.get_dblist(), dbstats=wh.gather_stats())

@bp.route("/api")
def page_api():
    return redirect("https://lbgi.fr/api/index.rvt?api=orthoinspector")

@bp.route("/<page>")
def default(page):
    try:
        return render_template(f"{page}.html", dblist=wh.get_dblist())
    except jinja2.exceptions.TemplateNotFound:
        abort(404)

app.register_blueprint(bp, url_prefix=config['prefix'])
app.register_blueprint(bpapi, url_prefix=config['prefix']+'/api')
app.register_blueprint(bpsecret, url_prefix=config['prefix'])
