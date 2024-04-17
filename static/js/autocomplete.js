$(document).ready(function() {
	function init_protein_autocomplete(form) {

		$(form).find("input.searchbar").autocomplete({
			source: prefix+'/'+database+'/search/protein',
			minLength: 2,
	  
			select: function(event, ui) {
				if (!ui.item.noresults) {
					let access = ui.item.access;
					location.href = prefix+'/'+database+'/protein/'+access;
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

	$('form.protein-srch').each(function(i,v) {
		init_protein_autocomplete(v);
	});
});
