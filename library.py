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

class database(object):
	def __init__(self, name, release):
		self.database = name
		self.release = release
		self.url = f"http://localhost:5000/oi/api/{self.database}/{self.release}"
		species_list = None
		newick = None
		clades = None
	def get_species_liste(self):
		if self.species_list == None:
			query = self.url + "/species"
			response = open.urlopen(query)
			self.species_list = json.loads(response.read())
		return self.species_list
	def get_tree_newick(self):
		if self.newick == None:
                        query = self.url + "/clades/Newick"
                        response = open.urlopen(query)
                        self.newick = json.loads(response.read())
		return self.newick
	def get_all_clades(self):
		if self.clades == None:
                        query = self.url + "/clades"
                        response = open.urlopen(query)
                        self.clades = json.loads(response.read())
		return self.clades

class species(object): #passer par un objet bdd
	def __init__(self, db, taxid):
		self.taxid = taxid
		self.database = self.db.database
		self.release = self.db.release
		self.url = self.db.url
		self.proteins = None
		self.profiles = None
	def get_all_protein(self):
		if self.proteins == None:
			query = self.url + f"/species/{self.taxid}/proteins"
			response = open.urlopen(query)
			self.proteins = json.loads(response.read())
		return self.proteins
	def get_proteins_profiles(self):
		if self.profiles == None:
                	query = url + f"/species/{self.taxid}/profiles"
                	response = open.urlopen(query)
                	self.profiles = json.loads(response.read())
		return self.profiles
	def orthologs_with(self, taxid2):
                query = url + f"/species/{self.taxid}/orthologs/{taxid2}"
                response = open.urlopen(query)
                orthologs = json.loads(response.read())
                return orthologs


class protein(object):
	def __init__(self, access, sp):
		self.access = access
		self.taxid = self.sp.taxid
		self.database = self.sp.database
		self.url = self.sp.url
		self.release = self.sp.release
		self.info = None
		self.orthologs = None
		self.profile = None
	def info(self):
		if self.info == None:
			query = url + f"/protein/{self.access}"
                	response = open.urlopen(query)
                	self.info = json.loads(response.read())
		return sel.info
	def orthologs(self, taxid2 = None):
		if self.taxid2 != None:
			query = url + "/protein/{self.access}/orthologs/{self.taxid2}"
			response = open.urlopen(query)
			orthologswith = json.loads(response.read())
			return orthologswith
		elif self.orthologs == None:
			query = url + f"/protein/{self.access}/orthologs"
			response = open.urlopen(query)
			self.orthologs = json.loads(response.read())
			return self.orthologs
	def profile(self):
		if self.profile == None:
			query = url + f"/protein/{self.access}/profile"
			reponse = open.urlopen(query)
			self.profile = json.loads(response.read())
		return self.profile


