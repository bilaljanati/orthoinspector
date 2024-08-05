class SearchResultPage {

	constructor(params) {
		this.DONE = 0;
		this.RUNNING = 1;
		this.FAILED = 2;
		this.UNKNOWN = 3;
		this.start_interval = 1500;
		this.interval_multiplier = 1.75;
		this.max_interval = 15000;

		this.name = params.name;
		this.div = params.div;
		this.taskid = params.taskid;
		this.result_url_prefix = params.result_url_prefix;
		this.protein_url_prefix = params.protein_url_prefix;
		this.fasta_url = params.fasta_url;
		this.toolbar = params.toolbar;
		this.result_count = params.result_count;

		this.results = [];

		this.start();
	}

	start() {
		function do_change_page() {
			this.change_page();
		}

		$('#pagesize').change(do_change_page);
		$('#pagechoice a').click(do_change_page);
		$('#download-fasta').click(() => {
			this.download_fasta();
		});
		$('#download-list').click(() => {
			this.download_list();
		});

		this.check_result();
	}

	/* Pagination */

	get_page_size() {
		return parseInt($('#pagesize select').val());
	}

	change_page(e) {
		const pagesize = this.get_page_size();
		var selected = 1;
		if (e && $(e.target).attr('data-page')) {
			selected = parseInt($(e.target).attr('data-page')) || 1;
		}
		this.display_results(this.results, pagesize, selected);
		this.display_pagination(selected);
	}

	display_pagination(selected=1) {
		const pagesize = this.get_page_size();
		const nbpages = Math.ceil(this.results.length/pagesize);

		if (nbpages == 1) {
			return;
		}

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

		ul.find('li:not(.disabled) a').click(() => {
			this.change_page();
		});
	}

	/* Data retrieval */

	check_result(interval=-1) {
		var interval = Math.max(interval, this.start_interval);
		$.ajax({
			url: this.result_url_prefix + this.taskid,
			type: 'GET',
			success: (response) => {
				switch (response.status) {
					case this.DONE:
						this.handle_results(response.result);
						break;
					case this.FAILED:
						this.display_error();
						break;
					case this.UNKNOWN:
						this.display_error();
					case this.RUNNING:
						interval = Math.min(this.max_interval, Math.round(interval*1.75));
						setTimeout(() => {
							this.check_result(interval);
						}, interval);
						break;
				}
			}
		});
	}

	display_error() {
		$('.loader').hide();
		$('#result').html('Error ! Please retry later.').show();
	}

	handle_results(res) {
		this.results = res;
		this.display_toolbar();
		this.change_page();
	}

	display_toolbar() {
		/*
		if (!this.toolbar) {
			return;
		}
		let toolbar = $(this.toolbar);
		toolbar.html("");
		toolbar.append('<button id="download-fasta" class="btn btn-primary" title="Download all sequences as FASTA">Get FASTA</button>');
		toolbar.append('<button id="download-list" class="btn btn-primary" title="Download ID list">Get ID list</button>');
		*/
		this.toolbar.show();
	}

	draw_distribution(prot) {
		if (prot.distribution) {
			return create_heatmap(prot);
		}
		return create_heatmap_without_clades(prot.profile);
	}

	display_one_cluster(cluster, name, id) {
		var c = $(`<div class="panel panel-default panel-cluster">
					<div class="panel-heading">
						<div class="oi_row">
							<div class="oi_cell left"></div>
							<div class="oi_cell center">
								<h3>
									<a data-toggle="collapse" href="#collapse0" aria-expanded="false" aria-controls="collapse0" style="color: #673ab7" class="collapsed cluster-name"></a>
								</h3>
							</div>
							<div class="oi_cell right cluster-size"></div>
						</div>
					</div>
					<div class="panel-body">
						<div class="oi_row">
							<div class="oi_cell left cluster-desc">
								<h4></h4>
							</div>
						</div>
						<div class="banner"></div>
						<div id="collapsen" class="panel panel-collapse proteins collapse" aria-expanded="false"></div>
					</div>
				</div>`);
		c.find('.banner').append(this.draw_distribution(cluster[0]));
		var link = c.find('.cluster-name')
		link.html(name)
			.attr('href', '#collapse'+id)
			.attr('aria-controls', 'collapse'+id);
		c.find('#collapsen').attr('id', 'collapse'+id);
		c.find('.cluster-size').html(' '+cluster.length+' proteins');
		c.find('.cluster-desc h4').html('Example of distribution with '+cluster[0].name);

		var prots = c.find('.proteins:first');
		for (const p of cluster) {
			prots.append(this.draw_sequence(p));
		}

		return c;
	}

	display_clusters(res) {
		var i = 1;
		var dest = $('#result');

		dest.empty();
		for (const c of res['clusters']) {
			dest.append(this.display_one_cluster(c, 'Cluster '+i, i));
			i++;
		}
		dest.append(this.display_one_cluster(res['singletons'], 'Singletons', i));
	}

	display_plain_results(res, pagesize, page) {
		this.display_sequences(res.slice((page-1)*pagesize, page*pagesize));
		$('#toolbar').show();
		$('#page').show();
	}

	count_result_proteins(res) {
		if (Array.isArray(res)) {
			return res.length;
		}
		var n = res['singletons'].length;
		for (const cluster of res['clusters']) {
			n += cluster.length;
		}
		return n;
	}

	display_results(res, pagesize, page=1) {
		$('.loader').hide();
		var nelems = this.count_result_proteins(res);
		let div = $(this.result_count);
		div.find('b').html(nelems);
		div.show();

		if ('clusters' in res) {
			this.display_clusters(res);
		} else if (res.length > 0) {
			this.display_plain_results(results, this.get_page_size(), page);
		}
	}

	display_sequences(sequences) {
		$('#result').empty();
		for (const s of sequences) {
			$('#result').append(this.draw_sequence(s));
		}
	}

	format_sequence_description(str) {
		const regex = /^[^ ]* ([^=]*) [A-Z]{2}.*/;
		let result = str.match(regex);

		if (result) {
			return result[1];
		}
		return '';
	}

	draw_sequence(s) {
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
		head.find('a.inlink').html(s.name).attr('href', prefix+'/'+database+'/'+release+'/protein/'+s.access)
		head.find('a.outlink').attr('href', 'http://uniprot.org/uniprot/'+s.access);

		let body = `<div class="panel-body">
						<row class="oi_row">
							<div class="oi_cell"><h4>Distribution</h4></div>
						</row>
						<row class="oi_row">
							<div class="oi_cell">
								<div class="distribution">
									<div class="banner"></div>
								</div>
							</div>
						</row>
					</div>`;
		let footer = '<div class="panel-footer"></div>';
		p.append(head, body, footer);
		p.find('.banner').append(this.draw_distribution(s));
		return p;
	}

	add_form_field(form, key, val) {
		var f = document.createElement("input");
		f.setAttribute("type", "hidden");
		f.setAttribute("name", key);
		f.setAttribute("value", val);
		form.appendChild(f);
	}

	get_access_list() {
		var access_list = [];

		if (Array.isArray(this.results)) {
			for (const seq of this.results) {
				access_list.push(seq.access);
			}
		} else {
			for (const seq of this.results['singletons']) {
				access_list.push(seq.access);
			}
			for (const cluster of Object.values(this.results['clusters'])) {
				for (const seq of cluster) {
					access_list.push(seq.access);
				}
			}
		}
		return access_list;
	}

	download_fasta() {
		var access_list = this.get_access_list();
		if (access_list.length == 0) {
			return;
		}

		var form = document.createElement("form");
		form.setAttribute("method", "POST");
		form.setAttribute("action", prefix+'/'+database+'/'+release+'/download/fasta');
		form.setAttribute("target", "_blank");
		this.add_form_field(form, "access_list", access_list.join(','));
		this.add_form_field(form, "filename", this.name+"_"+taxid+".fasta");
		document.body.appendChild(form);
		form.submit();
		form.remove();
	}

	download_list() {
		var access_list = this.get_access_list();
		if (access_list.length == 0) {
			return;
		}

		var data = access_list.join('\n');
		var blob = new Blob([data], { type: "text/plain" });
		var url = URL.createObjectURL(blob);

		var downloadLink = $("<a />", {
			href: url,
			download: this.name+"_"+taxid+".list",
			style: "display: none;"
		});
		document.body.append(downloadLink);
		downloadLink[0].click();

		downloadLink.remove();
		URL.revokeObjectURL(url);
	}
}
