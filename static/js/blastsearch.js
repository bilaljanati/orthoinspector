$(function() {
    const DONE    = 0;
    const RUNNING = 1;
    const FAILED  = 2;
    const UNKNOWN = 3;
	const start_interval = 2000;
	const interval_multiplier = 1.75;
	const max_interval = 15000;

    function do_error(msg) {
        alert(msg);
        active_mode(false, false);
    }

	function active_mode(active, success=true) {
		$('#loading').toggle(active);
		$('#submit').prop('disabled', active);
		$('#result').toggle(!active && success);
		$('#loader').toggle(active);
	}

	function run_blast() {
        var query = $('#blast-input').val();
        var cutoff = $('#expect').val();
		active_mode(true);

        $.ajax({
            url: prefix+'/blast/submit',
            type: 'POST',
			data: {'query': query, 'cutoff': cutoff},
            success: function(res) {
                if (res.status !== "OK") {
                    do_error("Service unavailable, please retry later !");
					return;
				}
				check_result(res.id, start_interval);
            },
			error: function(xhr, status, error) {
				do_error("Service unavailable, please retry later.");
			}
        });
	}

	function check_result(id, interval) {
		$.ajax({
			url: prefix+'/blast/result/'+id,
			method: 'GET',
			success: function(res) {
				if (res.status === DONE) {
					display_result(res.result);
					active_mode(false);
				} else if (res.status === FAILED || res.status === UNKNOWN) {
                    do_error("An error occured.");
					active_mode(false, false);
				} else {
					interval = Math.min(max_interval, Math.round(interval*1.75));
					setTimeout(function() {
						check_result(id, interval);
					}, interval);
					return;
				}
			},
			error: function(xhr, status, error) {
				do_error("An error occured.");
			}
		});
	}

	function format_hit_line(l) {
		const regex = /^([^ ]+) (.*)  ([0-9][^ ]*) +([0-9][^ ]*)$/;
		const match = l.trim(' ').match(regex);

		if (!match) {
			return false;
		}
		return {
			'name': match[1],
			'description': match[2],
			'score': match[3],
			'evalue': match[4],
		};
	}

	function extract_alignment_name(al) {
		const regex = /^([^ ]+)/;
		const match = al.match(regex);

		return match ? match[1] : '';
	}

	function parse_blast(blast) {
		const lines = blast.trim().split('\n');
		let i = 0;
		var hits = [];
		var alignments = {};

		// scroll to hits
		while (i<lines.length && !lines[i++].startsWith('Sequences producing')) {}
		if (i == lines.length) {
			return {'hits': [], 'alignments': []};
		}
		i += 1;
		// parse hits
		while (lines[i] !== '') {
			hits.push(format_hit_line(lines[i]));
			i++;
		}
		// parse alignments
		var alilines = [];
		while (!lines[i].startsWith('Lambda')) {
			alilines.push(lines[i++]);
		}
		var alignments = alilines.join('\n').trim().split('>');
		delete alilines;
		if (alignments[0].trim() === "") {
			alignments.shift();
		}
		alignments = alignments.map(a => '>'+a);

		return {'hits': hits, 'alignments': alignments};
	}

	function extract_prot_access(name) {
		var access = "";

		const match = name.match(/^[^|]+\|([^|]+)\|[^|]+$/);
		if (match) {
			access = match[1];
		} else {
			access = name.toUpperCase();
		}
		return access;
	}

	function get_latest_release() {
		let releases = Object.keys(dbs);
		return Math.max(...releases.map(r => parseInt(r)))
	}

	function get_protein_url(name) {
		let latest_release = get_latest_release();
		return prefix+'/Transverse/'+latest_release+'/protein/'+extract_prot_access(name);
	}

	function display_result(blast) {
		var data = parse_blast(blast);
		var d = $('#result');
		d.html('');

		if (data['hits'].length == 0) {
			d.html("No hits found !");
			return;
		}

		d.html('Sequences producing significant alignments:                          (Bits)  Value\n\n');

		var i = 1;
		for (const h of data['hits']) {
			let hclass = (i%2)==0 ? 'blast-odd' : 'blast-even';
			let name = h['name'];

			d.append('<span class="blast-hit '+hclass+'">'
				+'<a href="'+get_protein_url(name)+'" target="_blank">'+name+'</a> '
				+h['description']+'  '
				+'<a>'+h['score']+'</a>'+' '.repeat(8-h['score'].length)
				+'<a>'+h['evalue']+'</a>'+' '.repeat(9-h['evalue'].length)
				+'<a href="#hit'+i+'">Go to alignment</a>'
				+'</span>\n');
			i++;
		}
		d.append('\n\n');
		var i = 1;
		for (const a of data['alignments']) {
			let name = extract_alignment_name(a);
			d.append('<a id="hit'+(i++)+'"></a>'+a);
		}
		d.show();
	}

	function check_input() {
		var refloat = /^[+-]?\d+(\.\d+)?([eE][+-]?\d+)?$/;
		var input = $('#blast-input').val().trim();
		var ready = input.length >= 10;
		ready &= refloat.test($('#expect').val());
		return ready;
	}

	function init() {
		if ($('#blast-input').val().length == 0) {
			return;
		}
		if (!check_input()) {
			return;
		}
		run_blast();
	}

	$('#blast-input,#expect').on('input', function() {
		$('#submit').prop('disabled', !check_input());
	});
	$('#submit').click(run_blast);

	init();
});
