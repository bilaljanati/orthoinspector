"use strict";


$(document).ready(function() {

	const DONE    = 0;
	const RUNNING = 1;
	const FAILED  = 2;
	const UNKNOWN = 3;

	var results = [];

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
		display_results(results);
	}

	function display_results(res) {
		$('.loader').hide();

		display_sequences(res);

		$('#numres b').html(res.length);
		$('#numres').show();
		$('#toolbar').show();
	}

	function display_sequences(sequences) {
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

	$('#download-fasta').click(download_fasta);
	$('#download-list').click(download_list);
});
