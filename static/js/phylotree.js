"use strict";


$(document).ready(function() {

	var names = {};
	var selection;

	function expand_while_one_child(node) {
		if (node.children && node.children.length == 1) {
			expand_while_one_child(node.children[0]);
			return;
		}
		if (node.children && node.children.length > 0) {
			node.children[0].setActive();
		} else {
			node.setActive();
		}
	}

	function get_name(taxid) {
		return names[taxid];
	}

	function put_taxons(ulselector, list) {
		var ul = $(ulselector);
		ul.html('');
		for (const taxid of list) {
			ul.append('<li>'+get_name(taxid)+'</li>');
		}
	}

	function display_selection(selection) {
		put_taxons('#present', selection['present']);
		put_taxons('#absent', selection['absent']);

		var empty = (selection['present'].length+selection['absent'].length > 0);
		$('#selection').toggle(empty);
		$('#submit').prop('disabled', !empty);
	}

	function update_selection() {
		selection = get_tree_selection();
		display_selection(selection);
	}

	function get_tree_selection() {
		var tree = $("#tree").fancytree("getTree");
		var absents = [];
		var presents = new Set();

		for (const ancestor of tree.getPresentNodes()) {
			for (const n of ancestor.findAll(n => !n.children)) {
				if (!n.children) {
					let taxid = n.data['taxid']
					presents.add(taxid);
					names[taxid] = n.title;
				}
			}
		}
		presents = [...presents];

		for (const n of tree.getAbsentNodes()) {
			if (!n.children) {
				let taxid = n.data['taxid']
				absents.push(taxid);
				names[taxid] = n.title;
			}
		}
		return {
			'present': presents,
			'absent': absents
		}
	}

	function load_tree() {
		$("#tree").fancytree({
			extensions: ["glyph", "filter"],
			checkbox: true,
			selectMode: 3,
			glyph: {
				preset: "bootstrap3",
				map: {}
			},
			icon: false,
			filter: {
				autoApply: false,
				autoExpand: true,
				counter: true,
				fuzzy: false,
				hideExpandedCounter: true,
				hideExpanders: true,
				highlight: true,
				leavesOnly: false,
				nodata: true,
				mode: "hide"
			},
			source: {
				url: prefix+"/"+database+"/tree/profile",
			},
			activate: function(event, data) {
				$("#statusLine").text(event.type + ": " + data.node);
			},
			expand: function(e, data) {
				expand_while_one_child(data.node);
			},
			select: function(event, data) {
				update_selection();
			}
		});
		$.ui.fancytree.debugLevel = 0;
	}

	load_tree();
	$('#submit').click(function() {
		const data = selection;
		// TODO: submit
	});
});
