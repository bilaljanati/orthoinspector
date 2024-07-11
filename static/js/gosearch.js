$(document).ready(function() {

	const MAX_RESULTS = 10;
	var cache = {};

	function update_species_list(database, release) {
		let key = database+release;

		if (key in cache) {
			init_species_search(cache[key]);
			return;
		}

		$.ajax({url: prefix+'/'+database+'/'+release+'/species',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                cache[key] = data;
                init_species_search(data);
            },
            error: function(xhr, status, error) {
                console.error('Ajax error:', status, error);
            }
		});
	}

	function init_species_search(species) {
		let data = species.map(sp => {
			return {value: sp.taxid, label: sp.name};
		});
		$('#taxid,#species-name').val("");
		try {
			$('#srch-species').autocomplete("destroy");
		} catch (err) {}

		$('#srch-species').autocomplete({
			minLength: 2,
			source: function(request, response) {
				var results = $.ui.autocomplete.filter(data, request.term);
				response(results.slice(0, MAX_RESULTS));
			},
			select: function(e, ui) {
				e.preventDefault();
				$(e.target).val(ui.item.label);
				$('#taxid').val(ui.item.value);
				$('#species-name').val(ui.item.label);
				init_go_search();
			},
			focus: function(e, ui) {
				$(e.target).val(ui.item.label);
			}
		});
	}

	function init_go_search() {
		const id = '#srch-go';
		$(id).prop('disabled', false);

		try {
			$('#srch-species').autocomplete("destroy");
		} catch (err) {}

		let taxid = $('#taxid').val();
		$(id).autocomplete({
			source: prefix+'/go/autocomplete/'+taxid,
			select: function(e, ui) {
				e.preventDefault();
				let item = ui.item;
				$(e.target).val(item.label);
				$('#go-term-id').val(item.value);
				$('#go-term-name').val(item.label);
				init_go_search();
			},
			focus: function(e, ui) {
				$(e.target).val(ui.item.label);
			}
		});
	}

	function disable_go_search() {
		$('#srch-go').prop('disabled', true);
	}

	function toggle_submit_btn(enable) {
		$('#btn-go-query').prop('disabled', !enable);
	}

	function do_submit() {
		let dataa = [
			$('#sel-db-go').val(),
			$('#sel-release-go').val(),
			$('#taxid').val(),
			$('#go-term-name').val(),
		];
		console.log(dataa);
		var data = {
			'database': $('#sel-db-go').val(),
			'release': $('#sel-release-go').val(),
			'taxid': $('#taxid').val(),
			'species_name': $('#species-name').val(),
			'goid': $('#go-term-id').val(),
			'goname': $('#go-term-name').val(),
		}
		if (!Object.values(data).every(value => Boolean(value))) {
			console.error('Invalid input');
			return;
		}
		var form = $('<form>', {
			action: prefix+'/gosearch/result', // Replace with your URL
			method: 'POST',
			target: '_blank'
		});
		$.each(data, function(key, value) {
			$('<input>').attr({
				type: 'hidden',
				name: key,
				value: value
			}).appendTo(form);
		});
		form.appendTo('body');
		form.submit();
		form.remove();
	}

	initDBFields($('#sel-db-go'), $('#sel-release-go'));
	update_species_list($('#sel-db-go').val(), $('#sel-release-go').val());
	$('#sel-db-go').change(function(e) {
		update_species_list($('#sel-db-go').val(), $('#sel-release-go').val());
	});
	$('#srch-species').change(function(e) {
		if ($(e.target).val().trim() == "") {
			disable_go_search();
		}
	});
	$('#srch-go').change(function(e) {
		const empty = $(e.target).val().trim() == "";
		toggle_submit_btn(!empty);
	});
	$("#btn-go-query").click(do_submit);
});
