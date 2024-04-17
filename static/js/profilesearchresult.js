"use strict";


$(document).ready(function() {

	const DONE    = 0;
	const RUNNING = 1;
	const FAILED  = 2;
	const UNKNOWN = 3;

	var results = [];

	/* Pagination */

	function get_page_size() {
		return parseInt($('#pagesize select').val());
	}

	function change_page(e) {
		const pagesize = get_page_size();
		var selected = 1;
		if (e && $(e.target).attr('data-page')) {
			selected = parseInt($(e.target).attr('data-page')) || 1;
		}
		display_results(results, get_page_size(), selected);
		display_pagination(selected);
	}

	function display_pagination(selected=1) {
		const pagesize = get_page_size();
		const nbpages = Math.ceil(results.length/pagesize);

		var ul = $("ul.pagination");
		ul.empty();
		let elem = $('<li><a href="#" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a></li>');
		if (selected == 1) {
			elem.addClass('disabled');
			elem.find('a').attr('href', 'javascript:void(0)');
		} else {
			elem.find('a').attr('data-page', selected-1);
		}
		ul.append(elem);
		for (let i=1; i<=nbpages; i++) {
			let active = (i==selected) ? ' class="active"' : '';
			let elem = $('<li><a href="#">'+i+'</a></li>');
			elem.find('a').attr('data-page', i);
			if (i == selected) {
				elem.addClass('active');
				elem.attr('href', 'javascript:void(0)');
			}
			ul.append(elem);
		}
		elem = $('<li><a href="#" aria-label="Next"><span aria-hidden="true">&raquo;</span></a></li>');
		if (selected == nbpages) {
			elem.addClass('disabled');
			elem.find('a').attr('href', 'javascript:void(0)');
		} else {
			elem.find('a').attr('data-page', selected+1);
		}
		ul.append(elem);

		ul.find('li:not(.disabled) a').click(change_page);
	}

	/* Data retrieval */

	function check_result() {
		$.ajax({
			url: prefix+"/"+database+"/profilesearch/result/"+taskid,
			type: 'GET',
			success: function(response) {
				switch (response.status) {
					case DONE:
						handle_results(response.result);
						break;
					case FAILED:
						display_error();
						break;
					case UNKNOWN:
						display_error();
					case RUNNING:
						break;
				}
			}
		});
	}

	function display_error() {
		$('.loader').hide();
		$('#result').html('Error ! Please retry later.').show();
	}

	function handle_results(res) {
		results = res;
		change_page();
	}

	function display_results(res, pagesize, page=1) {
		$('.loader').hide();

		$('#numres b').html(res.length);
		$('#numres').show();
		if (res.length > 0) {
			console.log((page-1)*pagesize, page*pagesize);
			display_sequences(res.slice((page-1)*pagesize, page*pagesize));
			$('#toolbar').show();
		}
		$('#page').show();
	}

	function display_sequences(sequences) {
		$('#result').empty();
		for (const s of sequences) {
			$('#result').append(draw_sequence(s));
		}
	}

	function format_sequence_description(str) {
		const regex = /^[^ ]* ([^=]*) [A-Z]{2}.*/;
		let result = str.match(regex);

		if (result) {
			return result[1];
		}
		return '';
	}

	function draw_sequence(s) {
		var p = $('<div class="panel panel-default protein-card"></div>');
		let head = $(`<div class="panel-heading">
						<div class="oi_row">
							<div class="oi_cell left">
								<p><a class="inlink" target="_blank"></a>&nbsp;<a class="outlink" target="_blank"><span class="glyphicon glyphicon-new-window"></span></a></p>
							</div>
							<div class="oi_cell center"><b class="prot-desc"></b></div>
							<div class="oi_cell right">
							<p class="prot-length"></p>
						</div>
					</div>
				</div>`);
		head.find('.prot-desc').html(s.short_desc);
		head.find('.prot-length').html(s.length+' aa');
		head.find('a.inlink').html(s.name).attr('href', prefix+'/'+database+'/protein/'+s.access)
		head.find('a.outlink').attr('href', 'http://uniprot.org/uniprot/'+s.access);

		let body = `<div class="panel-body">
						<row class="oi_row">
							<div class="oi_cell"><h4>Distribution</h4></div>
						</row>
						<row class="oi_row">
							<div class="oi_cell">
								<div class="distribution">
									<div class="banner">
										<div class="hm_row">
											<div class="hm_rect"></div>
										</div>
										<div class="hm_row"></div>
									</div>
								</div>
							</div>
						</row>
					</div>`;
		let footer = '<div class="panel-footer"></div>';
		p.append(head, body, footer);
		return p;
	}

	function draw_profile(prof) {
	}

	function add_form_field(form, key, val) {
		var f = document.createElement("input");
		f.setAttribute("type", "hidden");
		f.setAttribute("name", key);
		f.setAttribute("value", val);
		form.appendChild(f);
	}

	function get_access_list() {
		var access_list = [];
		for (const seq of results) {
			access_list.push(seq.access);
		}
		return access_list;
	}

	function download_fasta() {
		var access_list = get_access_list();
		if (access_list.length == 0) {
			return;
		}

		var form = document.createElement("form");
		form.setAttribute("method", "POST");
		form.setAttribute("action", prefix+'/'+database+'/download/fasta');
		form.setAttribute("target", "_blank");
		add_form_field(form, "access_list", access_list.join(','));
		add_form_field(form, "filename", "profile_"+query_taxid+".fasta");
		document.body.appendChild(form);
		form.submit();
		form.remove();
	}

	function download_list() {
		var access_list = get_access_list();
		if (access_list.length == 0) {
			return;
		}

		var data = access_list.join('\n');
		var blob = new Blob([data], { type: "text/plain" });
		var url = URL.createObjectURL(blob);

		var downloadLink = $("<a />", {
			href: url,
			download: "profile_"+query_taxid+".list",
			style: "display: none;"
		});
		document.body.append(downloadLink);
		downloadLink[0].click();

		downloadLink.remove();
		URL.revokeObjectURL(url);
	}

	var delay = ( function() {
		var timer = 0;
		return function(callback, ms) {
			clearTimeout (timer);
			timer = setTimeout(callback, ms);
		};
	})();
	delay(function(){
		check_result();
	}, 200 );

	$('#pagesize select').change(change_page);
	$('#pagechoice a').click(change_page);
	$('#download-fasta').click(download_fasta);
	$('#download-list').click(download_list);

});
