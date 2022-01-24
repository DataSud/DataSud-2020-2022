var var_display;

function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;
    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
};

$(document).ready(function() {
    var_display = getUrlParameter('view_mode');
	if (var_display) {
	    $('.media-grid').removeClass('affich-grille affich-liste');
   		if (var_display === 'grid') {
        	$('.media-grid').addClass('affich-grille');
	    } else if (var_display === 'list') {
    	    $('.media-grid').addClass('affich-liste');
	    }
    	$('#affich-mode button').removeClass('active');
		$('#affich-mode button[data-affich='+var_display+']').addClass('active');
	}
});

$('.primary').on('click', '#affich-mode button', function () {
    var selected_value = $(this).attr('data-affich');
    var newUrl;
	// Update URL
	if (var_display) {
		newUrl = location.href.replace("view_mode="+var_display, "view_mode="+selected_value);
	} else {
		if (window.location.search) {
			newUrl = window.location.href + '&view_mode=' + selected_value;	
		} else {
			newUrl = window.location.href + '?view_mode=' + selected_value;	
		}
	}
	// Reload page with new URL	
	window.location.href = newUrl;
});
