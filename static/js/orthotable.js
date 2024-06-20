function sequence_formatter(value, row) {
	var output = [];
	var full = model ? '' : '/full';

	for (const seq of value) {
		let qIdentifier = seq.name;
		let qAccess = seq.access;
		let content;

		if  (qAccess != access) {
			let OIlink = "<a title='OrthoInspector entry' class='id' data-access='"+qAccess+"' href='"+prefix+"/"+database+"/"+release+"/protein/"+qAccess+full+"'>"+qIdentifier+"</a>&nbsp;";
			let Unilink = "<a title='Uniprot entry' href='http://uniprot.org/uniprot/"+qAccess+"' target='_blank'><span class='glyphicon glyphicon-new-window'></span></a>";
			content = OIlink+Unilink;
		} else {
			content = "<b class='id'>"+qIdentifier+"</b>";
		}
		output.push('<li><span class="seq-link">'+content+'</span></li>');
	}
	return '<ul class="res-list">'+output.join('')+'</ul>';
}

function taxonomy_formatter(value, row) {
	const sep = ' - ';
	var names = [];
	for (const t of value) {
		names.push(t.name);
	}
	return names.join(sep) + sep;
}

function length_formatter(value, row) {
	var output = [];
	for (let s of value) {
		output.push('<li>'+s+' aa</li>');
	}
	return '<ul class="res-list">'+output.join('')+'</ul>';
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
	const FIELD_OPT_NAME = 'oi-displayed-fields';

	function save_displayed_fields() {
		let fields = [];
		for (const c of $('#orthotable').bootstrapTable('getVisibleColumns')) {
			fields.push(c.field);
		}
		localStorage.setItem(FIELD_OPT_NAME, fields.join(','));
	}

	function restore_displayed_fields() {
		let fields = localStorage.getItem(FIELD_OPT_NAME);
		if (!fields) {
			return;
		}
		let toshow = new Set(fields.split(','));
		for (const f of [...$('#orthotable').bootstrapTable('getVisibleColumns'), ...$('#orthotable').bootstrapTable('getHiddenColumns')]) {
			let col = f.field;
			let action = toshow.has(col) ? 'showColumn' : 'hideColumn';
			$('#orthotable').bootstrapTable(action, col)
		}
	}

	function update_nb_proteins() {
		var nb = $('#orthotable').bootstrapTable('getData').length;
		$('#prot-count span.nb').html(""+nb);
		$('#prot-count span.name').html(nb<=1? "ortholog": "orthologs");
	}

    $("table[data-search-placeholder]").each(function () {
        $(this).parents("div.bootstrap-table")
            .find("input[placeholder='Search']")
            .attr("placeholder", $(this).data("search-placeholder"));
    });

	$('#orthotable').bind('load-success.bs.table search.bs.table', function(e,data) {
		update_nb_proteins();
	});

	$('#orthotable').on('column-switch.bs.table', function(e, field, checked) {
		save_displayed_fields();
	});
	restore_displayed_fields();
});
