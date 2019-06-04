

$(document).ready(function() {

    /* search ---------------------------------------*/
    $("a.search_start").on("click", function(e) {
       document.searchForm.start.value = $(this).attr("data-value");
       document.searchForm.submit();
    });
});


function search_sort(fld, asc) {
   document.searchForm.sort.value = fld;
   document.searchForm.ascending.value = asc;
   document.searchForm.submit();
}

function overlay(url) {
    $('#overlay-content').load(url);
    $('#overlay').modal({show:true});
}

var isSelected = false;
function search_toggleSelect() {
  if (isSelected == false) {
    for (i = 0; i < document.searchList.length; i++) {
      if(document.searchList.elements[i].name != "ids")
          continue;
      document.searchList.elements[i].checked = true ;
      }
      isSelected = true;
      $("button.select").text("Select none");
      return isSelected;
  }
  else {
    for (i = 0; i < document.searchList.length; i++) {
      if(document.searchList.elements[i].name != "ids")
          continue;
      document.searchList.elements[i].checked = false ;
      }
      isSelected = false;
      $("button.select").text("Select all");
      return isSelected;
  }
}



