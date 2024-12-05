import os
import sys
from flask import Flask, request, Blueprint, abort, redirect, jsonify, Response
import yaml
from src.pool import WorkerPool
from src.tasks import do_work

curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f"{curdir}/src")

with open("config.yml", "r") as config_file:
    config = yaml.safe_load(config_file)

job_types = ["profile_search", "go_search", "blast_search"]
pool = WorkerPool(nworkers=config["worker_pool"]["nworkers"])

app = Flask(__name__)


@app.route("/submit", methods=["POST"])
def submit():
    params = request.form.to_dict()
    job_type = params["type"]
    if job_type not in job_types:
        abort(404)
    taskid = pool.submit(job_type, params)
    return jsonify({"status": "OK", "id": taskid})


@app.route("/result/<taskid>")
def res(taskid):
    status, res = pool.get_result(taskid)
    data = {"status": status}
    if status == WorkerPool.DONE:
        data["result"] = res
    return jsonify(data)
