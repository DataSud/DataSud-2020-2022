(function( $ ) {

  //sortList function
  $.fn.sortList = function(sort, sortType) {
    cnt = $(this).children('li:visible').get().length;
    var mylist = $(this);
    var listitems = $('li', mylist).get();

    if(sort == 'desc') {
      //descending sort
      if(sortType  == 'alphaSort') {
        mylist.removeClass('alph_asc');
        mylist.removeClass('cnt_asc');
        mylist.removeClass('cnt_desc');
        mylist.addClass('alph_desc');
      } else {
            mylist.removeClass('alph_asc');
            mylist.removeClass('cnt_asc');
            mylist.removeClass('alph_desc');
            mylist.addClass('cnt_desc');
      }
    } else {
      //ascending sort
      if(sortType  == 'alphaSort') {
        mylist.removeClass('alph_desc');
        mylist.removeClass('cnt_asc');
        mylist.removeClass('cnt_desc');
        mylist.addClass('alph_asc');
      } else {
        mylist.removeClass('cnt_desc');
        mylist.removeClass('alph_desc');
        mylist.removeClass('alph_asc');
        mylist.addClass('cnt_asc');
      }
    }

    if(listitems.length > 1) {
      listitems.sort(function(a, b) {
        if(sortType == 'alphaSort') {
          var compA = $.trim($(a).text().toUpperCase());
          var compB = $.trim($(b).text().toUpperCase());
        } else {
          var compA_arr = $(a).text().split("(");
          var compB_arr = $(b).text().split("(");
          var compA = parseInt($.trim(compA_arr[compA_arr.length-1].split(')')[0]));
          var compB = parseInt($.trim(compB_arr[compB_arr.length-1].split(')')[0]));
        }

        if(sort == 'asc'){
          return (compA < compB) ? -1 : 1;
        } else {
          return (compA > compB) ? -1 : 1;
        }
      });
    }

    //add sorted list to ul
    $.each(listitems, function(i, itm) {
        mylist.append(itm);
    });
  }

  $.extend({
    getUrlVars: function(){
      var vars = [], hash;
      var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
      for(var i = 0; i < hashes.length; i++) {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
      }
      return vars;
    },

    getUrlVar: function(name){
      return $.getUrlVars()[name];
    }
  });

  /* for all Show more/show less links modify link to take you to that facet */
/*  $('a#facet_read_more').each( function() {
    var name = $(this).attr('name').split("sm_")[1];
    var url = $(this).attr('href');

    if(url.indexOf('#sec-' + name) == -1){
      url = url.replace('#', '') + '#sec-' + name;
    }

    $(this).click(function(){
      location.href = url;
    });
  });
*/
  /**
   * for Alphabatical sort set param 'sortType' to alphaSort
   * for Count sort set param 'sortType' to cntSort
   * for sort order set param 'sort' to asc or desc
  **/
  var defaults = {
    'organization' : {'sortType': 'cntSort', 'sort' : 'desc'},
    'groups' : {'sortType': 'cntSort', 'sort' : 'desc'},
    'datatype' : {'sortType': 'cntSort', 'sort' : 'desc'},
    'support' : {'sortType': 'cntSort', 'sort' : 'desc'},
    'res_format' : {'sortType': 'cntSort', 'sort' : 'desc'},
    'license_id' : {'sortType': 'cntSort', 'sort' : 'desc'},
    'tags' : {'sortType': 'cntSort', 'sort' : 'desc'},
    'frequency' : {'sortType': 'cntSort', 'sort' : 'desc'},
  };

  var allVars = $.getUrlVars();
  var paramArr=[];
  var defaultArr = defaults;

  if(allVars[0] != window.location.href) {
    for(var i = 0; i < allVars.length; i++) {
      var sort = $.getUrlVar(allVars[i]).split('#')[0];

      if(sort == 'asc' || sort == 'desc') {
        var id, sortType;
        var parts = allVars[i].split('_');

        if(parts[parts.length-1] == 'sortAlpha'){
          sortType = 'alphaSort';
        } else {
          sortType = 'cntSort';
        }

        if(parts.length > 3) {
          parts.splice(0,1);
          parts.splice(parts.length-1, 1);
          id = parts.join('_');
        } else {
            id = parts[1];
        }

        paramArr.push(id);
        $('ul#' + id).sortList(sort, sortType);
      }
    }

    var diff = {};
    $.each(defaults, function(i,e) {
      if ($.inArray(i, paramArr) == -1) {
        diff['' + i + ''] = e;
      }
    });

    defaultArr = diff;
  }

  $.each(defaultArr, function(i,e) {
    if($('ul#'+ i).length > 0){
      $('ul#' + i).sortList(e['sort'], e['sortType']);
    }
  });

  $(".sortFacetAlpha").click(function() {
    var id = $(this).parent().parent().find('ul.unstyled.nav.nav-simple.nav-facet').attr('id');
    var mylist = $('ul#' + id);

    if(mylist.hasClass('alph_asc')){
      var sort = 'desc';
    } else {
      var sort = 'asc';
    }
    mylist.sortList(sort, 'alphaSort');
  });

  $(".sortFacetCount").click(function() {
    var id = $(this).parent().parent().find('ul.unstyled.nav.nav-simple.nav-facet').attr('id');
    var mylist = $('ul#' + id);

    if(mylist.hasClass('cnt_asc')){
      var sort = 'desc';
    } else {
      var sort = 'asc';
    }

    mylist.sortList(sort, 'cntSort');
  });

})( jQuery );
