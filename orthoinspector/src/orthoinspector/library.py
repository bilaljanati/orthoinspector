from flask import Flask, Blueprint, abort, jsonify, render_template, request
import os
import sys
import yaml
import urllib.request, json


open = urllib.request


def orthoDB():
    query = url + "/databases"
    response = open.urlopen(query)
    data = json.loads(response.read())
    return data


class Database:
    def __init__(self, name, release):
        self.database = name
        self.release = release
        self.url = f"http://localhost:5000/oi/api/{self.database}/{self.release}"
        self.species_list = None
        self.newick = None
        self.clades = None
        self.clade_species = None

    def __str__(self):
        return f"Database({self.name}, {self.release})"

    def __repr__(self):
        return self.__str__()

    def get_species_list(self):
        if self.species_list == None:
            query = self.url + "/species"
            response = open.urlopen(query)
            data = json.loads(response.read())
            liste = data["data"]
            self.species_list = {}
            for species in liste:
                self.species_list[species["taxid"]] = Species(
                    self, species["taxid"], species["name"]
                )
        return self.species_list

    def get_species(self, taxid):
        if self.species_list == None:
            self.get_species_list()
        sp = self.species_list[taxid]
        return sp

    def get_tree_newick(self):
        if self.newick == None:
            query = self.url + "/clades/newick"
            response = open.urlopen(query)
            self.newick = json.loads(response.read())
        return self.newick

    def get_all_clades(self):
        if self.clades == None:
            query = self.url + "/clades"
            response = open.urlopen(query)
            self.clades = json.loads(response.read())
        return self.clades

    def get_clade_species(self, clade):
        self.clade_species = None
        query = self.url + f"/{clade}/species"
        response = open.urlopen(query)
        self.clade_species = json.loads(response.read())
        return self.clade_species


class Species:  # passer par un objet bdd
    def __init__(self, db, taxid, name):
        self.taxid = taxid
        self.name = name
        self.db = db
        self.all_proteins = None
        self.profiles = None

    def __str__(self):
        return f"Species({self.name}, {self.taxid})"

    def __repr__(self):
        return self.__str__()

    def get_all_proteins(self):
        if self.all_proteins == None:
            query = self.db.url + f"/species/{self.taxid}/proteins"
            response = open.urlopen(query)
            self.all_proteins = {}
            data = json.loads(response.read())["data"]
            for prot in data:
                self.all_proteins[prot["access"]] = Protein(
                    self, prot["access"], prot["name"]
                )
        return self.all_proteins

    def get_proteins_profiles(self):
        if self.profiles == None:
            query = self.db.url + f"/species/{self.taxid}/profiles"
            response = open.urlopen(query)
            self.profiles = json.loads(response.read())
        return self.profiles

    def orthologs_with(self, taxid2):
        query = self.db.url + f"/species/{self.taxid}/orthologs/{taxid2}"
        response = open.urlopen(query)
        orthologs = json.loads(response.read())
        return orthologs

    def get_protein(self, access):
        if self.all_proteins == None:
            self.get_all_proteins()
        prot = self.all_proteins[access]
        return prot


class Protein:
    def __init__(self, sp, access, name):
        self.access = access
        self.name = name
        self.sp = sp
        self.info = None
        self.orthologs = []
        self.prof = None
        self.taxid2 = None

    def __str__(self):
        return f"Protein({self.access}, {self.name})"

    def __repr__(self):
        return self.__str__()

    def desc(self):
        if self.info == None:
            query = self.db.url + f"/protein/{self.access}"
            response = open.urlopen(query)
            self.info = json.loads(response.read())
        return self.info

    def get_orthologs(self, taxid2=None):
        self.taxid2 = taxid2
        if self.orthologs != []:
            return self.orthologs
        if self.taxid2 != None:
            query = self.sp.db.url + f"/protein/{self.access}/orthologs/{self.taxid2}"
            response = open.urlopen(query)
            list_orthologs = json.loads(response.read())
            for orth in list_orthologs:
                sp1 = self.sp
                taxid2 = orth["taxid"]
                # sp2 = db.get_species(orth["taxid"])
                if orth["type"] == "One-to-one":
                    pr1 = self
                    position = orth["orthologs"].index(",")
                    access2 = orth["orthologs"][:position]
                    # pr2 = sp2.get_protein(access2)
                    self.orthologs.append(
                        Orthologs(
                            sp1,
                            taxid2,
                            pr1,
                            access2,
                            inparalogs1,
                            inparalogs2,
                            orth["type"],
                        )
                    )
                if orth["type"] == "Many-to-One":
                    pr1 = self
                    inpar_temp = orth["inparalogs"].split(",")
                    inparalogs1 = []
                    for identifier in inpar_temp:
                        if "_" not in identifier:
                            inparalogs1.append(identifier)
                    position = orth["orthologs"].index(",")
                    access2 = orth["orthologs"][:position]
                    # pr2 = sp2.get_protein(access2)
                    self.orthologs.append(
                        Orthologs(
                            sp1,
                            taxid2,
                            pr1,
                            access2,
                            inparalogs1,
                            inparalogs2,
                            orth["type"],
                        )
                    )
                if orth["type"] == "Many-to-One":
                    pr1 = self
                    inpar_temp = orth["inparalogs"].split(",")
                    inparalogs1 = []
                    for identifier in inpar_temp:
                        if "_" not in identifier:
                            inparalogs1.append(identifier)
                    position = orth["orthologs"].index(",")
                    access2 = orth["orthologs"][:position]
                    # pr2 = sp2.get_protein(access2)
                    self.orthologs.append(
                        Orthologs(
                            sp1,
                            taxid2,
                            pr1,
                            access2,
                            inparalogs1,
                            inparalogs2,
                            orth["type"],
                        )
                    )
                if orth["type"] == "One-to-Many":
                    pr1 = self
                    inpar_temp = orth["orthologs"].split(",")
                    inparalogs2 = []
                    for identifier in inpar_temp:
                        if "_" not in identifier:
                            inparalogs2.append(identifier)
                    access2 = inparalogs2[0]
                    # pr2 = sp2.get_protein(access2)
                    self.orthologs.append(
                        Orthologs(
                            sp1,
                            taxid2,
                            pr1,
                            access2,
                            inparalogs1,
                            inparalogs2,
                            orth["type"],
                        )
                    )
                if orth["type"] == "Many-to-Many":
                    pr1 = self
                    inpar_temp = orth["inparalogs"].split(",")
                    inparalogs1 = []
                    for identifier in inpar_temp:
                        if "_" not in identifier:
                            inparalogs1.append(identifier)
                    inpar_temp = orth["orthologs"].split(",")
                    inparalogs2 = []
                    for identifier in inpar_temp:
                        if "_" not in identifier:
                            inparalogs2.append(identifier)
                    access2 = inparalogs2[0]
                    # pr2 = sp2.get_protein(access2)
                    self.orthologs.append(
                        Orthologs(
                            sp1,
                            taxid2,
                            pr1,
                            access2,
                            inparalogs1,
                            inparalogs2,
                            orth["type"],
                        )
                    )
            return self.orthologs
        if self.taxid2 == None:
            query = f"http://localhost:5000/oi/{self.sp.db.database}/{self.sp.db.release}/orthologs/{self.access}"
            response = open.urlopen(query)
            print(query)
            list_orthologs = json.loads(response.read())
            print(len(list_orthologs))
            for item in list_orthologs:
                sp1 = self.sp
                taxid2 = item["species"]["taxid"]
                # sp2 = self.db.get_species(id2)
                inparalogs1 = []
                inparalogs2 = []
                for inpar in item["orthologs"]:
                    inparalogs2.append(inpar["access"])
                pr1 = self
                access2 = inparalogs2[0]
                # pr2 = sp2.get_protein(access2)
                orthologtemp = Ortholog(
                    sp1, taxid2, pr1, access2, inparalogs1, inparalogs2, item["type"]
                )
                self.orthologs.append(orthologtemp)
            return self.orthologs

    def profile(self):
        if self.prof == None:
            query = self.url + f"/protein/{self.access}/profile"
            response = open.urlopen(query)
            self.prof = json.loads(response.read())
        return self.prof


class Ortholog:
    def __init__(self, sp1, taxid2, prot1, access2, inparalog1, inparalog2, type):
        self.sp1 = sp1
        self.sp2 = taxid2
        self.prot1 = prot1
        self.prot2 = access2
        self.type = type
        self.inparalog1 = inparalog1
        self.inparalog2 = inparalog2

    def __str__(self):
        return f"Ortholog[{self.type}, {self.prot2}]"

    def __repr__(self):
        return self.__str__()
