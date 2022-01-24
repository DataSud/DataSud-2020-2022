// Convert bytes to octets
function toOctetString(value) {
	var len = String(value).length;
	if (len > 6) {
		return (Math.round((value / 1024 / 1024)*10)/10).toLocaleString('fr-FR') + ' Mo';
	} else if (value > 3) {
		return (Math.round(value / 1024)).toLocaleString('fr-FR') + ' Ko';
	} else if (value > 0) {
		return Math.round(value) + ' octets';
	} else {
        return '';
    }
}

// Init Bootstrap Tooltips
$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})

// Update resource size in resource list (ckan: dataset)
$('#dataset-resources .resource-list .resource-item [name="size"]').each(function(){
  var size_bytes = $(this).attr('data-size');
  $(this).children('span[name="size-value"]').html(toOctetString(size_bytes));
});

// Update resource size in additional info (ckanext-scheming)
var resource_size = $('table tr[name="size"] td').html();
$('table tr[name="size"] td').html(toOctetString(resource_size));

// Modal resource download
$(document).on("click", ".open-download-modal", function () {
  var datasetName = $(this).data('datasetname');
  var datasetTitle = $(this).data('datasettitle');
  var datasetCreationDate = $(this).data('datasetcreationdate');
  var datasetPublicationDate = $(this).data('datasetpublicationdate');
  var datasetModificationDate = $(this).data('datasetmodificationdate');
  var datasetLicense = $(this).data('datasetlicense');
  var resourceTitle = $(this).data('resourcetitle');
  var resourceURL = $(this).data('resourceurl');
  var resourceFormat = $(this).data('resourceformat');
  var resourceCRS = $(this).data('resourcecrs');

  // Download button URL
  $("#download-modal-res-list .download-button-resource").attr("href", resourceURL);

  // Replace variables
  var regexDatasetURL = new RegExp('<a href="{{URL_DATASET}}">', "g");
  var modalCustomContent = $("#download-modal-res-list .modal-custom-content").html()
    .replace(/{{TITLE_DATASET}}/g,`<span class="modal-dataset-title"></span>`)
    .replace(regexDatasetURL,`<a class="modal-dataset-url"></span>`)
    .replace(/{{DATE_CREATION}}/g,`<span class="modal-dataset-crea-date"></span>`)
    .replace(/{{DATE_PUBLICATION}}/g,`<span class="modal-dataset-publi-date"></span>`)
    .replace(/{{DATE_EDITION}}/g,`<span class="modal-dataset-modif-date"></span>`)
    .replace(/{{LICENSE_DATASET}}/g,`<span class="modal-dataset-license"></span>`)
    .replace(/{{TITLE_RESOURCE}}/g,`<span class="modal-res-title"></span>`)
    .replace(/{{FORMAT_RESOURCE}}/g,`<span class="modal-res-format"></span>`)
    .replace(/{{CRS_RESOURCE}}/g,`<span class="modal-res-crs"></span>`);

  $("#download-modal-res-list .modal-custom-content").html(modalCustomContent);

  $("#download-modal-res-list .modal-custom-content .modal-dataset-title").html(datasetTitle);
  $("#download-modal-res-list .modal-custom-content .modal-dataset-url").attr("href", `/dataset/${datasetName}`);
  $("#download-modal-res-list .modal-custom-content .modal-dataset-crea-date").html(datasetCreationDate);
  $("#download-modal-res-list .modal-custom-content .modal-dataset-publi-date").html(datasetPublicationDate);
  $("#download-modal-res-list .modal-custom-content .modal-dataset-modif-date").html(datasetModificationDate);
  $("#download-modal-res-list .modal-custom-content .modal-dataset-license").html(datasetLicense);
  $("#download-modal-res-list .modal-custom-content .modal-res-title").html(resourceTitle);
  $("#download-modal-res-list .modal-custom-content .modal-res-format").html(resourceFormat);
  $("#download-modal-res-list .modal-custom-content .modal-res-crs").html(resourceCRS);
});
