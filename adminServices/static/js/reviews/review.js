function dateMaker(date) {
    return String(date.getFullYear()) + '-' + String(date.getMonth() + 1) + '-' + String(date.getDate())
}

var selectCheckbox = new Set();
//this function for colaps rows
function ecRow(event) {
    if (event.target.style.getPropertyValue('white-space') == 'pre-wrap') {
        event.target.style = "white-space: no-wrap;"
    }
    else {
        event.target.style = "white-space: pre-wrap;"
    }
}
//All filter function handel by filterFunction
$(document).ready(() => {
    var flag = 'All';
    if (prev_flag == 'True') {
        flag = 'True'
    }
    if (prev_flag == 'False') {
        flag = 'False'
    }
    $(`#flag option[value='${flag}']`).attr('selected', 'selected');
    $(`#status option[value='${prev_status}']`).attr('selected', 'selected');
    $("#post_date_from").val(`${prev_date_from}`);
    $("#post_date_to").val(`${prev_date_to}`);

    $('.form-check-input').on('click', function () {
        if ($(this).is(':checked')) {
            $(this).css({
                "background-color": "#335F90",
            });
        }
        else {
            $(this).css({
                "background-color": "#fff",
            });
        }
    });

});

// select All checkbox
function selectAll() {
    var checkboxs = $('input[type="checkbox"]');
    for(var i in checkboxs){
        checkboxs[i].checked = true;
        selectCheckbox.add('All');
    }
}
function deselectAll() {
    if (selectCheckbox.has('All')) selectCheckbox.delete('All')

    var checkboxs = $('input[type="checkbox"]');
    for(var i of checkboxs){
        i.checked = NaN;
        selectCheckbox.delete(i.id)
    }
}
//select rows by using checkbox
function selectRow(event) {
    if (event.target.checked) {
        selectCheckbox.add(event.target.id)
    } else {
        selectCheckbox.delete(event.target.id)
    }

}

function updatestatu(discard) {
    var data = Array.from(selectCheckbox);
    if (data.length) {
        if (discard) {
            approve(updatestatus_url, token, selectCheckbox)
        }
        else {
            disapprove(decline_url, token, selectCheckbox)
        }
    }
    else {
        customAlert('No review was selected for action.');
    }
}
let difference =to_date_difference_from_current_date.includes('day')?-parseInt(to_date_difference_from_current_date):0
$(function () {
    $("#post_date_from").datepicker({
        dateFormat: 'dd/mm/yy',
        showOn: "button",
        maxDate: difference,
        buttonImage: "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
        buttonImageOnly: true,
        buttonText: "Select date",
        beforeShowDay: function(date) {
            var selectedDate = $("#post_date_from").datepicker("getDate");
            if (selectedDate && date.getTime() === selectedDate.getTime()) {
              return [true, "highlight-selected-date", "Selected Date"];
            } else {
              return [true, "", ""];
            }
          }
    });
});
$(function () {
    $("#post_date_to").datepicker({
        dateFormat: 'dd/mm/yy',
        showOn: "button",
        minDate:$("#post_date_from").datepicker("getDate"),
        maxDate: 0,
        buttonImage: "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
        buttonImageOnly: true,
        buttonText: "Select date",
        beforeShowDay: function(date) {
            var selectedDate = $("#post_date_to").datepicker("getDate");
            if (selectedDate && date.getTime() === selectedDate.getTime()) {
              return [true, "highlight-selected-date", "Selected Date"];
            } else {
              return [true, "", ""];
            }
          }
    });
});
function showFromDatePicker() {
    $("#post_date_from").datepicker('show')
}
function showToDatePicker() {
    $("#post_date_to").datepicker('show')
}

function showLoader() {
    $('#loader_for_mfg_ev_app').show();
}

function dropdownFunction() {
    document.getElementById("reviewDropdownId").classList.toggle("show");
}
window.onclick = function (event) {
    if (!event.target.matches('.reviewDropbtn')) {
        var dropdowns = document.getElementsByClassName("dropdown-content-items");
        var i;
        for (i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
    }
}