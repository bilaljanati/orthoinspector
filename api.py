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


# No function to get the list of databases --> fixed
# Does not work on localhost
@bp.route("/<database>")
def api_index(database):
    db = wh.get_db(database)
    if not db:
        abort(404, f'Unknown database "{database}".')
    return render_template("apiui.html", db=database, prefix=config["prefix"])


# Does not work on localhost
@bp.route("/desc/<database>.yml")
def api_desc(database):
    db = wh.get_db(database)
    if not db:
        abort(404, f'Unknown database "{database}".')
    return render_template("apidesc.yml", db=database, prefix=config["prefix"])


# works correctly
@bp.route("/<database>/<int:release>/species")
def list_species(database, release):
    db = wh.get_db(database, release)
    if not db:
        abort(404, f'Unknown database "{database}".')
    species = db.get_species_list()
    return jsonify(api_response(species))


# works
@bp.route("/<database>/<int:release>/species/<taxid>/proteins")
def list_proteins(database, release, taxid):
    db = wh.get_db(database, release)
    if not db:
        abort(404, f'Unknown database "{database}".')
    res = db.get_species_proteins(taxid)
    return jsonify(api_response(res))


# works
@bp.route("/<database>/<int:release>/protein/<access>")
def desc_protein(database, release, access):
    db = wh.get_db(database, release)
    if not db:
        abort(404, f'Unknown database "{database}".')
    return jsonify(api_response(db.get_protein_api(access), nb=1))


# works
@bp.route("/<database>/<int:release>/protein/<access>/orthologs")
def orthologs(database, release, access):
    db = wh.get_db(database, release)
    if not db:
        abort(404, f'Unknown database "{database}".')
    return jsonify(api_response(db.get_orthologs_api(access)))


##############################################"

# Added API:


# get the clades stored in the config.yml file
@bp.route("/<database>/<int:release>/clades/rough")
def get_clades_rough(database, release):
    db = wh.get_db(database, release)
    return jsonify(db.clades)


# get all clades present in the sun tree, more detailed
@bp.route("/<database>/<int:release>/clades/detailed")
def get_clades_detailed(database, release):
    db = wh.get_db(database, release)
    tree = db.get_sun_tree()
    clade_list = []
    for clade in tree:
        # Use a dictionary to store clade information
        infos = {"id": clade["id"], "name": clade["name"]}
        clade_list.append(infos)
    return jsonify(clade_list)


# get tree in Newick format
@bp.route("/<database>/<int:release>/clades/Newick")
def get_newick(database, release):
    db = wh.get_db(database, release)
    tree = db.get_sun_tree()
    # Creates a dictionnary, with parent nodes as key and a list of children nodes as value.
    # thanks to the way the sun tree is formated, the nodes are given in hierachical order, which
    # is practical for later
    node = {"": []}
    for level in tree:
        if level["id"] not in node:
            node[level["id"]] = []
        node[level["parent"]].append(level["id"])
    node.pop("")

    # Newick_l contains the list of elements of the Newick being built.
    # We search the parent in the Newick_l list, and add all its children to its left in the following format:
    # ["(", "children1", ",", "children2", ")"]
    Newick_l = [next(iter(node)), ";"]
    for parent in node:
        if (
            parent in Newick_l and node[parent] != []
        ):  # so that we don't get empty nodes
            subtree = ["("]
            for children in node[parent]:
                subtree.append(children)
                subtree.append(",")
            del subtree[-1]  # removes the last "," before closing the parenthesis
            subtree.append(")")
            where = Newick_l.index(parent)
            Newick_l[where:where] = subtree
    Newick = ""
    for element in Newick_l:
        Newick = Newick + str(element)
    return jsonify(Newick)


# profiles of all the proteins in a species
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


# get list of databases
@bp.route("/databases")
def databases_list():
    databases = {}
    years = config["warehouse"]["databases"].keys()
    for year in years:
        databases[year] = list(config["warehouse"]["databases"][year].keys())
    return jsonify(databases)


# list of species in clade
@bp.route("/<database>/<int:release>/<clade>/species")
def get_clade_species(database, release, clade):
    db = wh.get_db(database, release)
    species_list = []
    sql = db._get_sql("get_clade_species")
    result = db._query(
        sql, {"clade": clade}
    )  # uses the text contained in the get_clade_species.sql file as template for the query
    for species in result:
        species_list.append({"taxid": species["taxid"], "name": species["name"]})
    return jsonify(species_list)


# orthologs btw 2 species
@bp.route("/<database>/<int:release>/species/<taxid1>/orthologs/<taxid2>")
def orthologs_two_species(database, release, taxid1, taxid2):
    db = wh.get_db(database, release)
    sql = db._get_sql("ortholog2format")
    orthologs = db._query(sql, {"species1": taxid1, "species2": taxid2})
    return jsonify(orthologs)


# orthologs of a protein in a specified species
@bp.route("/<database>/<int:release>/protein/<access>/orthologs/<taxid>")
def orthologs_species(database, release, access, taxid):
    db = wh.get_db(database, release)
    sql = db._get_sql("orthologswspecies")
    orthologs = db._query(sql, {"qsp": taxid, "access": access})
    return jsonify(orthologs)


#######################################
