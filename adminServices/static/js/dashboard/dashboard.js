let from_date_object = {
    dateFormat: 'dd/mm/yy',
    showOn: "button",
    buttonImage: "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-2.png",
    buttonImageOnly: true,
    buttonText: "Select date",
    maxDate: 0,
    beforeShowDay: function(date) {
        var selectedDate = $("#from_date").datepicker("getDate");
  
        if (date.getTime() === selectedDate.getTime()) {
          return [true, "highlight-selected-date", "Selected Date"];
        } else {
          return [true, "", ""];
        }
      }
}

$(function () {
    $("#from_date").datepicker(from_date_object);
});

let to_date_object = {
    dateFormat: 'dd/mm/yy',
    showOn: "button",
    buttonImage: "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-2.png",
    buttonImageOnly: true,
    buttonText: "Select date",
    maxDate:$("#from_date").datepicker("getDate")?new Date($("#from_date").datepicker("getDate").setDate($("#from_date").datepicker("getDate").getDate()+dashboard_data_days_limit)):0,
    beforeShowDay: function(date) {
        var selectedDate = $("#to_date").datepicker("getDate");
  
        if (date.getTime() === selectedDate.getTime()) {
          return [true, "highlight-selected-date", "Selected Date"];
        } else {
          return [true, "", ""];
        }
      }
}
to_date_object['maxDate'] = -maximum_to_date;
to_date_object['minDate'] = -time_difference;


$(function () {
    $("#to_date").datepicker(to_date_object);
});

function showFromDatePicker() {
    $("#from_date").datepicker('show')
}
function showToDatePicker() {
    $("#to_date").datepicker('show')
}


function filterFunction(type, val) {
    if (type === 'clear') {
        window.location.href = window_radirect_location;
    } else {
        if (val.includes('&')) {
            val = val.replace("&", "$");
        }
        $('#loader_for_mfg_ev_app').show();
        let new_url = ''
        const params = new URLSearchParams(url_u);
        params.forEach(function (value, key) {
            if (key !== type) {
                new_url += `&${key}=${value}`;
            }
        });
        if (type) window.location.href = `${window_radirect_location}?${type}=${val}${new_url}`;
    }
}
$('#chart_nav .navbar-nav a').on('click', function () {
    $('#chart_nav .navbar-nav').find('li.active').removeClass('active');
    $(this).parent('li').addClass('active');
});
$('#chart_nav .navbar-nav a').on('click', function () {
    $('#chart_container_id').find('div.active').removeClass('active');
    $('#c' + $(this).parent('li').attr('id')).addClass('active');
});


