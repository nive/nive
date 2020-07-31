

$(document).ready(function () {

    $("#boxSearch a.search_start").on("click", function (e) {
        document.searchForm.start.value = $(this).attr("data-value");
        document.searchForm.submit();
    });

    $("#boxSearch #delete").on("click", function (e) {
        e.preventDefault();
        $("#boxSearch").attr("action", "deletec").submit();
    });
    $("#boxSearch #cut").on("click", function (e) {
        e.preventDefault();
        $("#boxSearch").attr("action", "@cut").submit();
    });
    $("#boxSearch #copy").on("click", function (e) {
        e.preventDefault();
        $("#boxSearch").attr("action", "@copy").submit();
    });
    $("#boxSearch #paste").on("click", function (e) {
        e.preventDefault();
        $("#boxSearch").attr("action", "@paste").submit();
    });

    $("#boxSearch .sort").on("click", function (e) {
        e.preventDefault();
        var fld = $(this);
        if (fld.attr("data-value") == $("#boxSearch input[name=sort]").val()) {
            var ac = $("#boxSearch input[name=ascending]").val();
            ac = ac == "1" ? "0" : "1";
            $("#boxSearch input[name=ascending]").val(ac);
        } else {
            $("#boxSearch input[name=sort]").val($(this).attr("data-value"));
            $("#boxSearch input[name=ascending]").val("1");
            $("#boxSearch input[name=start]").val("");
        }
        $("#boxSearch").submit();
    });

    var isSelected = false;
    $("#boxSearch #selectButton").on("click", function (e) {
        e.preventDefault();
        if (isSelected == false) {
            isSelected = true;
            $("input[name=ids]").prop("checked", true);
            $("#selectButton").text("Auswahl aufheben");
        } else {
            isSelected = false;
            $("input[name=ids]").prop("checked", false);
            $("#selectButton").text("Alle auswählen");
        }
    });

    $('.lazy').Lazy();
});


function overlay(url) {
    $('#overlay-content').load(url);
    $('#overlay').modal({show: true});
}




