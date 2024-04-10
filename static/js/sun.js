"use strict";

$(function() {

	function load_species() {
		const url = prefix+'/'+database+'/tree/sun';

		$.get(url, function(res) {
			draw_sun(res);
		});
	}

	function draw_sun(species) {
		var ids = [];
		var labels = [];
		var parents = [];
		var values = [];

		for (let s of species) {
			ids.push(s['id']);
			labels.push(s['name']);
			parents.push(s['parent']);
			values.push(s['value']);
		}

		const ref_colors = ['#e54545', '#f2a285', '#f2eb85', '#32a632', '#2a4d46', '#4192d9', '#4132a6', '#573159', '#66384a', '#4c1717', '#8c5e4d', '#a6835b', '#a6a15b', '#234027', '#39bfb6', '#2e6799', '#231b59', '#73226d', '#331c25', '#330f0f', '#ff944d', '#d9a641', '#c5e645', '#7ee69a', '#549994', '#132b40', '#655ba6', '#e67edf', '#ff4d7c', '#e57e7e', '#b26836', '#8c6c2a', '#798c2a', '#4dff94', '#49e7f2', '#498df2', '#9a7ee6', '#804674', '#ff8cab', '#a65b5b', '#734322', '#e5c37e', '#89b336', '#1b5934', '#1f6166', '#3f5473', '#8d49f2', '#e645b0', '#995467', '#593131', '#ffba8c', '#594c31', '#62733f', '#46805d', '#4ddbff', '#3d63cc', '#432273', '#a6327f', '#a63241', '#ff7c4d', '#a6795b', '#332b1c', '#344d17', '#2e9967', '#328fa6', '#2a448c', '#2f2340', '#661f45', '#73222d', '#bf5d39', '#73543f', '#fff34d', '#c9ff8c', '#4dffc3', '#17424d', '#6278b3', '#8d5ba6', '#ff8cc9', '#8c442a', '#402f23', '#b2aa36', '#387322', '#62b398', '#4dc4ff', '#455ae6', '#8f32a6', '#b3628d', '#592b1b', '#ffac4d', '#736d22', '#5ff249', '#8cffe8', '#2e7599', '#131940', '#db45e6', '#b23668', '#401f13', '#b27836', '#403d13', '#65a65b', '#3f7368', '#1f4e66', '#383866', '#310f33', '#593c1b', '#4c172c'];

		var colors = ref_colors;
		while (colors.length < species.length) {
			colors.push(...ref_colors);
		}

		var data = [{
		  type: "sunburst",
		  ids: ids,
		  labels: labels,
		  parents: parents,
		  values: values,
		  outsidetextfont: {size: 20},
		  leaf: {opacity: 0.4},
		  marker: {
			  line: {width: 3},
			  colors: colors
		  },
		  hovertemplate: "%{label}<br />%{value} species<extra></extra>",
		  branchvalues: "total",
		  maxdepth: 4
		}];
		var layout = {
		  margin: {l: 0, r: 0, b: 0, t: 0},
		  width: 500,
		  height: 500,
		  paper_bgcolor: 'rgba(0,0,0,0)',
		  plot_bgcolor: 'rgba(0,0,0,0)',
		};
		Plotly.newPlot('species-plot', data, layout);
	}

	load_species();
});
