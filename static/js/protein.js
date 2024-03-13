$(function() {

	const FIELD_OPT_NAME = 'oi-displayed-fields';

    // Submit the table form
    function tableform(){
            var form = $('#sastableform');
            form.submit();
            $('#fitsform').hide();
    }

    $('a.read_more').on('click',function(event){ /* find all a.read_more elements and bind the following code to them */
        $(this).hide();
        event.preventDefault(); /* prevent the a from changing the url */
        $(this).parent().find('.more_text').show(); /* show the .more_text span */
    });

// Delete rows from data table

	function add_form_input(form, key, val) {
		var h = document.createElement("input");
		h.setAttribute("type", "hidden");
		h.setAttribute("name", key);
		h.setAttribute("value", val);
		form.appendChild(h);
	}

	function downloadSequences(format) {
		var form = document.createElement("form");
		form.setAttribute("method", "POST");
		form.setAttribute("action", prefix+'/'+database+'/'+version+'/download/'+format);
		form.setAttribute("target", "_blank");

		var access_list = [access];
		for (let a of extractAccess($('#orthotable'))) {
			access_list.push(a);
		}
		add_form_input(form, "access_list", access_list.join(','));

		document.body.appendChild(form);
		form.submit();
	}

	$('#fasta').click(function() {
		downloadSequences('fasta');
    });
	$('#orthoxml').click(function() {
		downloadSequences('orthoxml');
    });

	function determineScale(seqlen) {
		var allowed = [10,20,50,100,200,500,1000,2000,5000]
		var estimate = seqlen/8
		var scale = 100
		var diff = Number.MAX_SAFE_INTEGER

		$.each(allowed, function(i,s) {
			let curdiff = Math.abs(estimate-s)
			if (curdiff < diff) {
				scale = s
				diff = curdiff
			} else {
				return false
			}
		})
		return scale
	}

	function drawDomains(doms, id) {
		if (doms.length == 0) {
			$(id).html('No data')
			return
		}

		$(id).html(
			$('<div>').addClass('bars').append(
				$('<ul>').addClass('signatures')
			)
		).append(
			$('<div>').addClass('scale')
		)

		const colors = ['#ecd87a','#4ba7cb','#82ca9c','#a799b7','#d77a61','#928779','#030301'];
		// bars
		$.each(doms, function(i, d) {

			let line = $('<div>').attr('id', d.interproid).addClass('dom-line');
			$('ul.signatures').append(
				$('<li>').addClass('signature').append(line)
			);
			$.each(d.fragments, function(j, f) {
				let left = f.start/seqLength*100;
				let width = (f.end-f.start)/seqLength*100;
				let sources = d.source.join(', ').toUpperCase();
				let color = colors[i%colors.length];
				let interproid = d.interproid
				let url = 'https://www.ebi.ac.uk/interpro/entry/InterPro/'+interproid
				let title = '<a class="no-underline" href="'+url+'" target="_blank" title="InterPro"><b>'+interproid+'</b> <span class="glyphicon glyphicon-new-window" aria-hidden="true"></span></a>'
				let details = '<b title="Source">'+sources+'</b><br />'+d.interproname+'<br /><small title="Position">'+f.start+' - '+f.end+'</small>'

				line.append(
					$('<div>').addClass('bar').css('width', width+'%').css('left', left+'%').attr('data-toggle', 'popover').attr('title', title).attr('data-content', details).attr('data-container', '#'+interproid).attr('data-placement', 'auto top').attr('data-html', true).attr('data-trigger', 'click').css('background-color', color)
				);
			});
		});
		// scale
		var scale = determineScale(seqLength)
		var nb = Math.round(seqLength/scale)
		nb -= (seqLength-scale*nb < scale/2) ? 1: 0

		function addScale(number, pos, nbpos) {
			$('.scale').append(
				$('<span>').addClass('scale-bar').css('left', pos+'%')
			).append(
				$('<span>').text(number).addClass('scale-number').css('left', nbpos+'%')
			)
		}
		function addGrade(pos) {
			$('.bars').prepend(
				$('<span>').addClass('grade').css('left', pos+'%')
			)
		}

		addScale(0, 0, 0)
		for (let i=1; i<=nb; i++) {
			let percent = i*scale/seqLength*100
			addScale(i*scale, percent, percent-1)
			addGrade(percent)
		}
		addScale(seqLength, 100, 98)

        // legend
        var legend = $('<div>').addClass('legend')
		let url = 'https://www.ebi.ac.uk/interpro/protein/' + access
		legend.append('<a href="'+url+'" target="_blank">See more on InterPro <span class="glyphicon glyphicon-new-window"></span></a>')
		$(id).append(legend)

		$('.bar[data-toggle="popover"]').popover()
	}

	function writeAnnotations(data, id) {

		function formatTitle(txt) {
			var res = txt.replace('_', ' ')
			return res.charAt(0).toUpperCase() + res.slice(1)
		}

		const url = 'https://www.ebi.ac.uk/QuickGO/term/'
		const evidence_url = 'http://wiki.geneontology.org/index.php/'
		$(id).html('')

		console.log(data)
		for (const type of ['molecular function', 'biological process', 'cellular component']) {
			let l = data.annotations[type]
			let title = formatTitle(type)
			$(id).append($('<h4>').append(title))

			if (!l || l.length == 0) {
				$(id).append("<div><p>No GO term was found under this category</p></div>")
			} else {
				let list = $('<ul>')

				for (const annot of l) {
					let elem = $('<li>')
					elem.append('<a href="'+url+annot.id+'" target="_blank">'+annot.term+'</a>')

					if ('evidence' in annot) {
						for (const ev of annot.evidence) {
							evlink = evidence_url + ev.description.replaceAll(' ', '_') + '_('+annot.code+')';
							elem.append(' <a href="'+evlink+'" target="_blank" title="'+ev.description+'"><span class="evidence badge badge-primary">'+ev.code+'</span></a>');
						}
					}
					list.append(elem)
				}
				$(id).append(list)
			}
		}
	}

	$('a#show-dom').click(function() {
		var panel = $('#collapseDoms div.panel-body')
		if (panel.attr('data-loaded') !== undefined) return

		panel.attr('data-loading', false);
		$.get(prefix+"/annotations/interpro/"+access, function(data) {
			var doms = data.domains;
			drawDomains(doms, '#collapseDoms div.panel-body');
			panel.attr('data-loaded', true);
		});
	});

	$('a#show-annot').click(function() {
		var panel = $('#collapseGO div.panel-body')
		if (panel.attr('data-loaded') !== undefined) return

		panel.attr('data-loading', false);
		//$.get(prefix+"/annotations/"+version+"/go/"+access, function(data) {
		$.get(prefix+"/annotations/go/"+access, function(data) {
			var annots = data;
			writeAnnotations(annots, '#collapseGO div.panel-body');
			panel.attr('data-loaded', true);
		});
	});

	// taxo profile generation
	(function() {
		var div = $('.taxo-profile');
		if (div.length == 0) {
			return;
		}
		var data = JSON.parse(div.attr('data-profile'));
		data.options.zoom = true;
		create_heatmap(div, data.clades, data.options);

		$('.popup-elem').on('show.bs.popover', function() {
			// close any other open popup
			$('.popup-elem').not($(this)).popover('hide');
		});
	})();

	function sortDictKeys(d) {
		let res = {}
		let keys = Object.keys(d).sort();
		for (const k of keys)
			res[k] = d[k];
		return res;
	}

	function checkInparalogs() {
		let div = $('#collapseInparalogs');

		if (div.data('seen') === true)
			return;
		if (drawInparalogs(div))
			$('#btn-inparalogs').show();
		div.data('seen', true);
	}

	function drawInparalogs(div) {
		let tabledata = $('#orthotable').bootstrapTable('getData');
		let refclades = Object.keys(JSON.parse($('.taxo-profile').attr('data-profile')).clades);
		let matrix = {};

		for (const row of tabledata) {
			let inter = row.fullTaxonomy.filter(x => refclades.includes(x));
			if (inter.length == 0) continue;
			let clade = inter[0];

			for (const prot of row.query) {
				let name = prot.name;
				if (!(name in matrix))
					matrix[name] = [];
				matrix[name][clade] = true;
			}
		}
		for (const genename in matrix) {
			let presence = matrix[genename];
			let row = $('<div class="hm_row">');
			row.append($('<div class="hm_col inparalog-name">').html(genename).attr('title', genename));
			for (const clade of refclades) {
				let col = $('<div class="hm_col">');
				if (clade in presence)
					col.html($('<span class="glyphicon glyphicon-ok">'));
				row.append(col);
			}
			div.append(row);
		}
		return Object.keys(matrix).length > 1;
	}

	function loadAbsentSummary() {
		$.ajax({
			type:"GET",
			url: prefix+'/'+database+'/'+version+'/absent/'+access+(full? '/full': ''),
			success: function(res, st) {
				writeAbsentSummary(res);
				$('#btn-notfoundin').removeAttr('disabled');
			}
		});
	}

	function writeAbsentSummary(dict) {
		var content = "";

		for (const clade in dict) {
			content += "<b>"+clade+"</b><br /><ul>";
			for (const orga of dict[clade])
				content += "<li>"+orga+"</li>"
			content += "</ul>";
		}
		$('#notFoundIn div.modal-body').html(content);
	}

	function save_displayed_fields() {
		let fields = localStorage.getItem('oi-checked-fields') || [];
		for (let c of $('#orthotable').bootstrapTable('getVisibleColumns'))
			fields.push(c.field);
		localStorage.setItem(FIELD_OPT_NAME, fields);
	}

	function restore_displayed_fields() {
		let fields = localStorage.getItem(FIELD_OPT_NAME);
		if (fields) {
			for (let f of fields.split(','))
				$('#orthotable').bootstrapTable('showColumn', f);
		}
	}

	$('#orthotable').on('load-success.bs.table', function(e,data) {
		$('btn-inparalogs').removeAttr('disabled');
		//checkInparalogs();
	});
	$('#orthotable').on('column-switch.bs.table', function(e, field, checked) {
		save_displayed_fields();
	});

	restore_displayed_fields();
	loadAbsentSummary();
});

function PipeError() {
    $('#align-button').removeClass('btn-primary');
    $('#align-button').addClass('btn-danger');
    $('#align-button').html("Service not available");
}

function launchAlignment(table) {
    var access_list = extractAccess(table);
    if (access_list.length <= 1) {
        alert('Please select sequences');
        return;
    }
    $('#align-button').prop('disabled', true);

	var data = {};
	data.access_list = access_list;
	data.query = access;

    $.ajax({
		type:"POST",
		url: prefix+'/'+database+'/'+version+'/download/fasta',
		data: data,
		success: function(html, statut) {
			var fasta = html;
			var session = callPipeAlign(fasta);
		},
		error: PipeError
	});
}

function callPipeAlign(fasta) {

    var formData = new FormData();
    
    formData.append('infile', fasta);

    $.ajax({
		type:"POST",
		url: '/pipealign/session',
		data: formData,
		contentType : false,
		processData : false,
		success: function(html, statut) {
			var session = html['session'];
			var url = '/pipealign?session='+session;
			window.open(url);
			$('#align-button').prop('disabled', false);
		},
		error: PipeError,
		timeout: 5000,
		crossDomain: false
	});
}

function extractId(table) {
    var allId = [];
    var allSelect = $(table).find(".selected");
    if (allSelect.length == 0) {
        return 0;
    }
    var currentSelected = allSelect.each( function(rindex,row){
        $(row).find('.id').each( function(prtindex, proteinId){$
            currentId = $(proteinId).text();
            if (!allId.includes(currentId)) {
				allId.push(currentId);
            }
        });
    });

    return allId;
}

function extractAccess(table) {
	var access_list = [];
	$('tr.selected a.id').each(function(i, l) {
		access_list.push($(l).attr('data-access'));
	});
	return access_list;
}

function exportTable(table, extension) {
    var queries = Array();
    
    var allId = extractId(table);
    if (allId === 0) {
        alert('Please select sequences');
        return;
    }
    method = "post";

    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", prefix+'/'+database+'/protein/'+access+'.'+extension);
    form.setAttribute("target", "_blank");
    var hiddenField = document.createElement("input");
    hiddenField.setAttribute("type", "hidden");
    hiddenField.setAttribute("name", 'proteinId');
    hiddenField.setAttribute("value", allId);
    form.appendChild(hiddenField);
    document.body.appendChild(form);
    form.submit();
}
