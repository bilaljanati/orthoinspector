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

# Jinja custom filter
#def regex_replace(s, pattern_match, pattern_out):
#    import re
#    return re.sub(pattern_match, pattern_out, s)
#
#app.jinja_env.filters['regex_replace'] = regex_replace

@bp.context_processor
def inject_globals():
    return config

@bp.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@bp.route("/")
def home():
    return render_template('index.html')

def db():
    db = wh.get_db('2023', 'Archaea')
    db.get_fasta(['A4YCN4', 'A4YCQ3'])
    return f"<p>DB has model organism: {db.has_models}, profiles: {db.has_profiles}, distances: {db.has_distances}</p>"

@bp.route("/<dbname>/<version>/orthologs/<access>")
@bp.route("/<dbname>/<version>/orthologs/<access>/full")
def orthologs(dbname, version, access):
    db = wh.get_db(dbname, version)
    orthos = db.get_orthologs(access)
    if not orthos:
        abort(404)
    return jsonify(orthos)

@bp.route("/<database>/<version>/protein/<access>")
@bp.route("/<database>/<version>/protein/<access>/full")
def protein(database, version, access):
    full = request.path.endswith('/full')
    db = wh.get_db(database, version)
    if not db.has_models and not full:
        return redirect(f'{config["prefix"]}/{database}/{version}/protein/{access}/full', code=301)

    prot = db.get_protein(access)
    if not prot:
        abort(404)
    dbinfo = {
        'name': database,
        'version': version,
        'full':  full,
        'has_transverse': db.has_transverse,
        'has_models': db.has_models,
        'has_profiles': db.has_profiles,
        'has_distances': db.has_distances
    }
    return render_template('protein.html', db=dbinfo, protein=prot)

@bp.route("/<database>/<version>/download/fasta", methods=['POST'])
def download_fasta(database, version):
    db = wh.get_db(database, version)
    fasta = db.get_fasta(request.form['access_list'])
    return Response(fasta, mimetype='text/plain')

@bp.route("/annotations/go/<access>")
def go_annotations(access):
    return jsonify(go.get_annotations(access))

@bp.route("/annotations/interpro/<access>")
def interpro_annotations(access):
    annots = interpro.get_domains(access)
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
