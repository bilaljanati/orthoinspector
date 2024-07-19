function color_boxes(father) {
	let fcol = chroma.scale(['#70ff4d','#ff4d4d']).mode('hsv');
	$(father).find(".hm_rect").each(function(i, el) {
		let ratio = $(el).attr('data-ratio') || false;
		if (ratio !== false)
			el.style['background-color'] = fcol(1-ratio);
	});
}

function apply_rename_rules(s) {
	const to_replace = ['^Candidatus', '^SAR'];
	const substitute = ['', 'SAR'];

	for (let i=0; i<to_replace.length; i++) {
		s = s.replace(RegExp(to_replace[i]), substitute[i]);
	}
	return s;
}

function abbreviate(string, maxlen) {
	string = apply_rename_rules(string);
	if (string.length <= maxlen) {
		return string;
	}
	return string.slice(0, maxlen-1)+'.';
}

function create_heatmap(clades, options={}) {
	var label_row = $('<div class="hm_row">');
	var box_row = $('<div class="hm_row">');
	var display_domains = ('display_domains' in options && options.display_domains);

	// inparalog placeholder
	label_row.append($('<div class="hm_col">'));
	box_row.append($('<div class="hm_col">'));

	if (display_domains) {
		var domain_row = $('<div class="hm_row domain_row">');
		domain_row.append($('<div class="hm_rect">'));
	}

	var prev_domain = null;
	for (const clade of clades) {
		let name = clade.name;
		let domain = clade.domain;
		let draw_border = new_domain = false;
		if (domain != prev_domain) {
			new_domain = true;
			if (prev_domain !== null)
				draw_border = true;
			prev_domain = domain;
		}

		let label = $('<div class="hm_label">')
		label.attr('title', name).text(abbreviate(name, 6));
		label_row.append(label);

		let box = $('<div class="hm_rect">')
		box.attr('title', clade.present+"/"+clade.total).attr('data-ratio', clade.present/clade.total);
		if (display_domains) {
			let domblock = $('<div class="hm_rect">');

			if (draw_border)
				box.addClass('black-border');
			if (new_domain)
				domblock.html(clade.domain);
			domain_row.append(domblock);
		}
		box_row.append(box);

		if ('zoom' in options && options.zoom && 'additional' in clade) {
			let boxtitle = box.attr('title');
			box.removeAttr('title');
			box.addClass('popup-elem');

			let zoomdiv = $('<div class="banner">');
			create_heatmap(zoomdiv, clade.additional, options);
			let pop_options = {'title': name+' distribution',
							template: '<div class="popover popover-distribution" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>',
							'content': zoomdiv,
							'html': true,
							'trigger': 'click',
							'placement': 'bottom'}
			box.popover(pop_options);
			box.attr('title', boxtitle);
		}
	}
	var div = $("<div>");
	/*
	if (display_domains)
		div.append(domain_row);
	*/
	div.append(label_row, box_row);
	color_boxes(box_row);
	return div;
}
