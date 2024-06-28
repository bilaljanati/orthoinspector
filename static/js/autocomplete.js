/* DB & releases fields */

const default_db = "Eukaryota";

function fillSelect(select, values, selected=undefined) {
	$(select).find("option").remove();
	for (const v of values) {
		$(select).append(
			$('<option>', {
				value: v,
				text: v
			})
		);
	}
	if (!selected || $(select).find('option[value='+selected+']').length == 0) {
		selected = default_db;
	}
	$(select).val(selected).change();
}

function hasOption(select, option) {
	var opts = $(select).find('option[value='+option+']');
	return opts.length > 0;
}

function updateDBField(e) {
	const dbfieldid = $(e.target).data("dbfield");
	var select_db = $("#"+dbfieldid);
	var release = $(e.target).val();
	fillSelect(select_db, dbs[release], select_db.val());

	var previous_db = $(select_db).val();
	if (hasOption(select_db, previous_db)) {
		select_db.val(previous_db).change();
	} else if (typeof(database) != 'undefined' && hasOption(select_db, database)) {
		select_db.val(database).change();
	} else if (hasOption(select_db, "Eukaryota")) {
		select_db.val("Eukaryota").change();
	}
}

function initDBFields(select_db, select_release) {
	var dblist = Object.keys(dbs);
	dblist = dblist.map(Number);
	dblist.sort();
	var last_release = dblist[dblist.length-1];
	fillSelect(select_release, dblist, last_release);
	fillSelect(select_db, dbs[last_release], default_db);

	if (typeof(database) != 'undefined' && typeof(release) != 'undefined') {
		$(select_db).val(database);
		$(select_release).val(release);
	}

	$(select_release).data("dbfield", $(select_db)[0].id);
	$(select_release).change(updateDBField);
}

$(document).ready(function() {

	/* Protein search */

	function getSelectedDatabase(form) {
		var sdb = $(form).find(".sel-db").val();
		return sdb;
	}

	function getSelectedRelease(form) {
		var sr = $(form).find(".sel-release").val();
		return sr;
	}

	function db_change_callback(e) {
		var elem = $(e.target);
		update_protein_autocomplete(elem);
	}

	function update_protein_autocomplete(elem) {
		var p = elem.closest(".protein-srch");
		$(p).find("input.searchbar").autocomplete("destroy");
		init_protein_autocomplete(p);
	}

	function init_protein_autocomplete(form) {

		const database = getSelectedDatabase(form);
		const release = getSelectedRelease(form);

		if (!database || !release) {
			console.error("No db info available");
			return;
		}

		$(form).find("input.searchbar").autocomplete({
			source: prefix+'/'+database+'/'+release+'/search/protein',
			minLength: 2,
			select: function(event, ui) {
				let database = getSelectedDatabase(form);
				let release = getSelectedRelease(form);
				if (!ui.item.noresults) {
					let access = ui.item.access;
					location.href = prefix+'/'+database+'/'+release+'/protein/'+access;
				}
			},
			open: function(event, ui) {
				$(form).find(".ui-autocomplete").css("z-index", 10000);
			},
			response: function(event, ui) {
				if (!ui.content.length) {
					let noResult = { name: "No results found", access: "Unknown protein", noresults: true};
					ui.content.push(noResult);
				} else {
					$(form).find("#message").empty();
				}
			},
		}).focus(function() {
			if (this.value != ""){
				$(this).autocomplete("search");
			}
		}).data("ui-autocomplete")._renderItem = function(ul, item) {
			return $("<li>")
				.append("<div><b>" + item.name + "</b><br><p>" + item.access + "</p></div>")
				.appendTo(ul);
		};
	}

	$('.protein-srch').each(function(i, v) {
		initDBFields($(v).find('.sel-db'), $(v).find('.sel-release'));
		init_protein_autocomplete(v);
		$(v).find('.sel-db').change(db_change_callback);
	});
});
