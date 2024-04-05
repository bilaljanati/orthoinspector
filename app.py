import os
import sys
from flask import Flask, request, render_template, Blueprint, abort, redirect, jsonify, Response
import yaml

curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f'{curdir}/src')

from src.warehouse import Warehouse
from src.geneontology import GeneOntology
from src.taxonomy import Taxonomy
from src.interpro import Interpro


with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
wh = Warehouse(config['warehouse'])
go = GeneOntology(config['geneontology'])
taxo = Taxonomy()
interpro = Interpro()

app = Flask(__name__, static_url_path=f"/{config['prefix']}/static")
bp = Blueprint('bp', __name__)


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
    return render_template('dbindex.html', db=wh.get_dbinfo(database), status=status, stats=stats, species=species)

@bp.route("/<database>/tree.json")
def species_tree(database):
    db = wh.get_db(database)
    if not db:
        abort(404)
    tree = db.get_species_tree()
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
    return redirect(f'{config["prefix"]}/{database}/protein/{access}', code=302)

@bp.route("/<database>/protein/<access>")
def protein(database, access):
    db = wh.get_db(database)
    if not db:
        abort(404)
    prot = db.get_protein(access)
    if not prot:
        abort(404)
    dbinfo = {
        'name': database,
        'has_models': db.has_models,
        'has_profiles': db.has_profiles,
        'has_distances': db.has_distances
    }
    return render_template('protein.html', db=dbinfo, protein=prot)

@bp.route("/<dbname>/orthologs/<access>")
def orthologs(dbname, access):
    db = wh.get_db(dbname)
    if not db:
        abort(404)
    orthos = db.get_orthologs(access)
    return jsonify(orthos)

@bp.route("/<database>/download/fasta", methods=['POST'])
def download_fasta(database):
    db = wh.get_db(database)
    access_list = request.form['access_list'].split(',')
    fasta = db.get_fasta(access_list)
    res = Response(fasta, mimetype='text/plain')
    res.headers['Content-Disposition'] = f'attachment; filename="{access_list[0]}.fa"'
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
    return jsonify(wh.get_stats())

app.register_blueprint(bp, url_prefix=config['prefix'])
