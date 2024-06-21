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

function updateDBField(e) {
	const dbfieldid = $(e.target).data("dbfield");
	var select_db = $("#"+dbfieldid);
	var release = $(e.target).val();
	fillSelect(select_db, dbs[release], select_db.val());
}

function initDBFields(select_db, select_release) {
	var dblist = Object.keys(dbs);
	dblist = dblist.map(Number);
	dblist.sort();
	var last_release = dblist[dblist.length-1];
	fillSelect(select_release, dblist, last_release);
	fillSelect(select_db, dbs[last_release], default_db);

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
		var p = elem.parent();
		$(elem).find("input.searchbar").autocomplete("destroy");
		init_protein_autocomplete(p);
	}

	function init_protein_autocomplete(form) {

		var database = getSelectedDatabase(form);
		var release = getSelectedRelease(form);

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

	function update_db_list(e) {
		var elem = $(e.target);
		var form = $(elem).parent();
		var select = $(form).find('.sel-db');

		let previous_db = getSelectedDatabase(form);
		let release = getSelectedRelease(form);

		$(select).find("option").remove();
		for (let dbname of dbs[release]) {
			$(select).append(
				$('<option>', {
					value: dbname,
					text: dbname
				})
			);
		}
		var opt = $(select).find('option[value='+previous_db+']');
		if (opt.length == 0) {
			select.val("Eukaryota").change();
		} else {
			select.val(previous_db).change();
		}
		update_protein_autocomplete(elem);
	}

	$('.protein-srch').each(function(i, v) {
		init_protein_autocomplete(v);
		initDBFields($(v).find('.sel-db'), $(v).find('.sel-release'));
		$(v).find('.sel-db').change(db_change_callback);
	});
});
