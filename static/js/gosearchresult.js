"use strict";


$(document).ready(function() {
	var result_handler = new SearchResultPage({
						'name': 'go',
						'taskid': taskid,
						'div': $('#result'),
						'result_url_prefix': prefix+'/gosearch/result/',
						'protein_url_prefix': prefix+'/'+database+'/'+release+'/protein/',
						'fasta_url': prefix+'/'+database+'/'+release+'/download/fasta',
						'toolbar': $('#toolbar'),
						'result_count': $('#numres')
					});
});
