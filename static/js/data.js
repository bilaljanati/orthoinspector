$(document).ready(function() {

	var cache = {};

	function getDb() {
		return $('#sel-db-data').val();
	}

	function getRelease() {
		return $('#sel-release-data').val();
	}

	function prepareData(species) {
		const db = getDb();
		const release = getRelease();
		var res = [];
		for (const s of species) {
			let taxid = s["taxid"];
			let name = s["name"];
			res.push({
				"proteome": "<a href=\""+data_url+"/"+db+release+"/proteomes/"+taxid+".fasta.gz\">"+taxid+".fasta.gz</a>",
				"data": "<a href=\""+data_url+"/"+db+release+"/data/"+taxid+".tsv.gz\">"+taxid+".tsv.gz</a>",
				"species": name
			});
		}
		return res;
	}

	function formatScript(taxids, url) {
		var filename = url.split("/").slice(-1).join();
		var s = "#!/bin/bash\n\nfor taxid in "
				+ taxids.join(" ")
				+ "; do\n"
				+ "\tcurl -so " + filename + " \"" + url + "\"\n"
				+ "done";
		return s;
	}

	function displayCommands(species) {
		const db = getDb();
		const release = getRelease();
		var taxids = [];
		for (const s of species) {
			taxids.push(s["taxid"]+"");
		}
		$("#cmd-proteomes").html(formatScript(taxids, data_url+"/"+db+release+"/data/$taxid.fasta.gz"));
		$("#cmd-orthology").html(formatScript(taxids, data_url+"/"+db+release+"/data/$taxid.tsv.gz"));
	}

	function displayData(species) {
		$("#table-data").bootstrapTable("load", prepareData(species));
		displayCommands(species);
	}
	
	function displayDataPage() {
		const db = getDb();
		const release = getRelease();
		const key = db+release;

		if (key in cache) {
			displayData(cache[key]);
			return;
		}

		$.ajax({
			type: "GET",
			url: prefix+"/data/"+db+"/"+release,
			contentType : false,
			processData : false,
			success: function(res, status) {
				let species = res["species"];
				cache[db+release] = species;
				displayData(species);
			}
		});
	}

	initDBFields($('#sel-db-data'), $('#sel-release-data'));
	displayDataPage();
	$('#sel-db-data').change(displayDataPage);
	$('#sel-release-data').change(displayDataPage);
});
