

$(document).ready(function() {
    var users = [];
    $(".userinfo").each(function (p,e) {
        var ref=$(e).text();
        if(users.indexOf(ref)==-1)
            users.push(ref);
    });
    $.post("/userdb/api/userinfo", {reference:users}).done(function (data) {
        $(".userinfo").each(function (p,e) {
            var u=$(e);
            var ref=u.text();
            console.log(ref);
            if(ref in data) {
                u.text(data[ref].name);
                console.log(data[ref].name);
            }
        });
    });

    $(".monitoring").each(function (p,e) {
        function render(data) {
            var info = $("#m-"+data.service+" .info");
            var ico = $("#ic-"+data.service);
            if(data.tests==0) {
                info.html("<h4>Keine Auswertung vorhanden!</h4>");
            } else if(data.failure==9) {
                info.html("<h4>Kritischer Fehler!</h4>");
                ico.html("<img src='/assets/intern/images/reject.png' title='Kritischer Fehler!'>");
            } else if(data.failure>2) {
                info.html("<h4>Fehler!</h4>");
                ico.html("<img src='/assets/intern/images/reject.png' title='Fehler!'>");
            } else if(data.failure>0) {
                info.html("<h4>Warnung!</h4>");
                ico.html("<img src='/assets/intern/images/help.png' title='Warnung!'>");
            } else {
                info.html("<h4>OK!</h4>");
                ico.html("<img src='/assets/intern/images/commit.png' title='OK!'>");
            }
            info.append("<p>Letzter Test: "+data.timestamp+"</p>");
            //block.html(data.service);
        }
        var block = $(e);
        var ref = block.attr("data");
        var svc = block.attr("svc");
        var dev = block.attr("dev");
        $("#m-"+ref+" button.stats").on("click", function (e) {
            document.location.href=dev;
        });
        $("#m-"+ref+" button.reload").on("click", function (e) {
            e.stopPropagation();
            $.post(svc+"run", {service:ref}).done(function (data) {
                $.post(svc+"status", {service:ref}).done(function (data) {
                    render(data);
                });
            });
        });

        $.post(svc+"status", {service:ref}).done(function (data) {
            render(data);
        });
    });

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



