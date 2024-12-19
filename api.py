from flask import Flask, Blueprint, abort, jsonify, render_template, request
import os
import sys
import yaml
from src.geneontology import GeneOntology
from src.taxonomy import Taxonomy
from src.interpro import Interpro


curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f"{curdir}/src")

from src.warehouse import Warehouse

with open("config.yml", "r") as config_file:
    config = yaml.safe_load(config_file)
wh = Warehouse(config["warehouse"])
go = GeneOntology(config["geneontology"])
taxo = Taxonomy()
interpro = Interpro()

bp = Blueprint("api", __name__)


def api_response(data, nb=-1):
    res = {"meta": {"status": "success"}}
    res["meta"]["nbResults"] = nb if nb >= 0 else len(data)
    res["data"] = data
    return res


@bp.errorhandler(404)
def page_not_found(e):
    return jsonify({"meta": {"status": "error", "msg": e.description}}), 404

# 
@bp.route("/<database>")
def api_index(database):
    db = wh.get_db(database)
    if not db:
        abort(404, f'Unknown database "{database}".')
    return render_template("apiui.html", db=database, prefix=config["prefix"])


# 
@bp.route("/desc/<database>.yml")
def api_desc(database):
    db = wh.get_db(database)
    if not db:
        abort(404, f'Unknown database "{database}".')
    return render_template("apidesc.yml", db=database, prefix=config["prefix"])


# works correctly ******added yml*****
@bp.route("/<database>/<int:release>/species")
def list_species(database, release):
    db = wh.get_db(database, release)
    if not db:
        abort(404, f'Unknown database "{database}".')
    species = db.get_species_list()
    return jsonify(api_response(species))


# works ****added yml****
@bp.route("/<database>/<int:release>/species/<taxid>/proteins")
def list_proteins(database, release, taxid):
    db = wh.get_db(database, release)
    if not db:
        abort(404, f'Unknown database "{database}".')
    res = db.get_species_proteins(taxid)
    return jsonify(api_response(res))


# works *****added yml****
@bp.route("/<database>/<int:release>/protein/<access>")
def desc_protein(database, release, access):
    db = wh.get_db(database, release)
    if not db:
        abort(404, f'Unknown database "{database}".')
    return jsonify(api_response(db.get_protein_api(access), nb=1))


# works ****added yml****
@bp.route("/<database>/<int:release>/protein/<access>/orthologs")
def orthologs(database, release, access):
    db = wh.get_db(database, release)
    if not db:
        abort(404, f'Unknown database "{database}".')
    return jsonify(api_response(db.get_orthologs_api(access)))


##############################################"

# Added API:

# get info species ****added yml****
@bp.route("/<database>/<int:release>/species/<taxid>")
def get_species_info(database, release, taxid):
    db = wh.get_db(database, release)
    sql = db._get_sql("speciesinfo")
    result = db._query(
        sql, {"taxid": taxid}
    )
    return jsonify(result)

# get all clades present in the sun tree, more detailed ****added yml****
@bp.route("/<database>/<int:release>/clades")
def get_clades_detailed(database, release):
    db = wh.get_db(database, release)
    tree = db.get_sun_tree()
    clade_list = []
    for clade in tree:
        # Use a dictionary to store clade information
        infos = {"id": clade["id"], "name": clade["name"]}
        clade_list.append(infos)
    return jsonify(clade_list)

#Newick depuis n'importe quel clade ****added yml****
# get tree in Newick format -- ajouter option pour avoir les noms au lieu de taxid
# option pour obtenir avec taxid ou nom de clade
@bp.route("/<database>/<int:release>/clades/newick")
def get_newick(database, release):
    db = wh.get_db(database, release)
    tree = db.get_profile_tree()
    new = []
    def recur(arbre, newick):
        children = arbre["children"]
        if arbre["folder"] == True:
            subnwk = []
            for child in children:
                subnwk.append(recur(child, newick))
            newick = f"({','.join(subnwk)})'{arbre['title']}'"
        else:
            newick = "'" + arbre["title"] + "'"
        return newick
    result = recur(tree, new)
    return jsonify(result)



# profiles of all the proteins in a species ****added yml****
# need to add a way to return an error message 400 if sql comes back empty
@bp.route("/<database>/<int:release>/species/<taxid>/profiles")
def get_all_profiles(database, release, taxid):
    db = wh.get_db(database, release)
    proteins = db.get_species_proteins(taxid)
    profiles = {}
    for entry in proteins:
        # build the list of profiles
        prot = db.get_protein(entry["access"])
        # dist = db.build_distribution(prot, model_only=1) Could be used to get all the distributions
        profiles[prot["access"]] = prot[
            "profile"
        ]  # for later: include the model_only argument as used by the profiles function
    return jsonify(
        profiles
    )  # each bit is organized in the order of the species in the database from whence they came


# get list of databases ****is in yml****
@bp.route("/databases")
def databases_list():
    databases = {}
    years = config["warehouse"]["databases"].keys()
    for year in years:
        databases[year] = list(config["warehouse"]["databases"][year].keys())
    return jsonify(databases)


# list of species in clade ****added yml****
@bp.route("/<database>/<int:release>/<clade>/species")
def get_clade_species(database, release, clade):
    db = wh.get_db(database, release)
    species_list = []
    sql = db._get_sql("get_clade_species")
    result = db._query(
        sql, {"clade": "%" + clade + "%"}
    )  # uses the text contained in the get_clade_species.sql file as template for the query
    for species in result:
        species_list.append({"taxid": species["taxid"], "name": species["name"]})
    return jsonify(species_list)


# orthologs btw 2 species *****added yml*****
@bp.route("/<database>/<int:release>/species/<taxid1>/orthologs/<taxid2>")
def orthologs_two_species(database, release, taxid1, taxid2):
    db = wh.get_db(database, release)
    sql = db._get_sql("ortholog2format")
    orthologs = db._query(sql, {"species1": taxid1, "species2": taxid2})
    return jsonify(orthologs)


# orthologs of a protein in a specified species ****added yml****
@bp.route("/<database>/<int:release>/protein/<access>/orthologs/<taxid>")
def orthologs_species(database, release, access, taxid):
    db = wh.get_db(database, release)
    sql = db._get_sql("orthologswspecies")
    orthologs = db._query(sql, {"qsp": taxid, "access": access})
    return jsonify(orthologs)

# profile of a protein ****added yml****
@bp.route("/<database>/<int:release>/protein/<access>/profile")
def protein_profile(database, release, access):
    db = wh.get_db(database, release)
    prot = db.get_protein(access)
    profile = prot["profile"]
    return jsonify(profile)


#######################################
