// this file contains the js code for hold payments list page
function showDownloadError(){
    $('#no_download_box').modal('show');
    setTimeout(function(){ $('#no_download_box').modal('hide'); }, 3000);
}
let difference =to_date_difference_from_current_date.includes('day')?-parseInt(to_date_difference_from_current_date):0
let from_date_object = { 
    dateFormat: 'dd/mm/yy',
    showOn: "button",
    buttonImage: "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
    buttonImageOnly: true,
    buttonText: "Select date",
    maxDate: difference,
    beforeShowDay: function(date) {
        var selectedDate = $("#from_date").datepicker("getDate");
  
        if (selectedDate && date.getTime() === selectedDate.getTime()) {
          return [true, "highlight-selected-date", "Selected Date"];
        } else {
          return [true, "", ""];
        }
      }
}

$(function() {
    $("#from_date").datepicker(from_date_object);
});



$(function() {
    $("#to_date").datepicker({ 
        dateFormat: 'dd/mm/yy',
        showOn: "button",
        buttonImage: "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
        buttonImageOnly: true,
        buttonText: "Select date",
        minDate:$("#from_date").datepicker("getDate"),
        maxDate:$("#from_date").datepicker("getDate")?new Date($("#from_date").datepicker("getDate").setDate($("#from_date").datepicker("getDate").getDate()+dashboard_data_days_limit)):0,
        beforeShowDay: function(date) {
            var selectedDate = $("#to_date").datepicker("getDate");
    
            if (selectedDate && date.getTime() === selectedDate.getTime()) {
                return [true, "highlight-selected-date", "Selected Date"];
            } else {
                return [true, "", ""];
            }
        }
    });
});

function showFromDatePicker(){
    $("#from_date").datepicker('show')
}
function showToDatePicker(){
    $("#to_date").datepicker('show')
}