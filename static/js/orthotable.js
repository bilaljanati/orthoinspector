function sequence_formatter(value, row) {
	var output = "";
	var outputArray = [];

	for (const seq of value) {
		let qIdentifier = seq.name;
		let qAccess = seq.access;

		if  (qIdentifier != protid) {
			let OIlink = "<a title='OrthoInspector entry' class='id' data-access='"+qAccess+"' href='"+prefix+"/"+database+"/"+version+"/protein/"+qAccess+"'>"+qIdentifier+"</a> ";
			let Unilink = "<a title='Uniprot entry' href='http://uniprot.org/uniprot/"+qAccess+"' target='_blank'><span class='glyphicon glyphicon-new-window'></span></a>";
			outputArray.push(OIlink+Unilink);
		} else {
			outputArray.push("<b class='id'>"+qIdentifier+"</b>");
		}
	}
	output = outputArray.join('<br>');
	return output;
}

function taxonomy_formatter(value, row) {
	const sep = ' - ';
	return value.join(sep) + sep;
}

function size_formatter(value, row) {
	var output = [];
	for (let s of value.split(',')) {
		output.push(s+' aa');
	}
	return output.join('<br />');
}

function species_formatter(value, row) {
	return "<a href='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id="
	+ value.taxid
	+ "' target='_blank'>"
	+ value.name
	+ "</a>";
}

function taxid_search_formatter(value) {
	return value.taxid;
}

$(document).ready(function() {
    $("table[data-search-placeholder]").each(function () {
        $(this).parents("div.bootstrap-table")
            .find("input[placeholder='Search']")
            .attr("placeholder", $(this).data("search-placeholder"));
    });
});
