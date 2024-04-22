from flask import Flask, Blueprint, abort, jsonify, render_template
import os
import sys
import yaml

curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f'{curdir}/src')

from src.warehouse import Warehouse

with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
wh = Warehouse(config['warehouse'])

bp = Blueprint('api', __name__)

def api_response(data, nb=-1):
    res = {'meta': {'status': 'success'}}
    res['meta']['nbResults'] = nb if nb >= 0 else len(data)
    res['data'] = data
    return res

@bp.errorhandler(404)
def page_not_found(e):
    return jsonify({'meta': {'status': 'error', 'msg': e.description}}), 404

@bp.route("/<database>")
def api_index(database):
    db = wh.get_db(database)
    if not db:
        abort(404, f'Unknown database "{database}".')
    return render_template('apiui.html', db=database, prefix=config['prefix'])

@bp.route("/desc/<database>.yml")
def api_desc(database):
    db = wh.get_db(database)
    if not db:
        abort(404, f'Unknown database "{database}".')
    return render_template('apidesc.yml', db=database, prefix=config['prefix'])

@bp.route("/<database>/species")
def list_species(database):
    db = wh.get_db(database)
    if not db:
        abort(404, f'Unknown database "{database}".')
    species = db.get_species_list()
    return jsonify(api_response(species))

@bp.route("/<database>/species/<taxid>/proteins")
def list_proteins(database, taxid):
    db = wh.get_db(database)
    if not db:
        abort(404, f'Unknown database "{database}".')
    res = db.get_species_proteins(taxid)
    return jsonify(api_response(res))

@bp.route("/<database>/protein/<access>")
def desc_protein(database, access):
    db = wh.get_db(database)
    if not db:
        abort(404, f'Unknown database "{database}".')
    return jsonify(api_response(db.get_protein_api(access), nb=1))

@bp.route("/<database>/protein/<access>/orthologs")
def orthologs(database, access):
    db = wh.get_db(database)
    if not db:
        abort(404, f'Unknown database "{database}".')
    return jsonify(api_response(db.get_orthologs_api(access)))

@bp.route("/<database>/protein/<access>/orthologs/{taxid}")
def orthologs_species(database, access, taxid):
    pass

@bp.route("/<database>/species/<taxid1>/orthologs/<taxid2>")
def orthologs_two_species(database, taxid1, taxid2):
    pass
