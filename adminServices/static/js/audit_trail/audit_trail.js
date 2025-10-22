let difference =to_date_difference_from_current_date.includes('day')?-parseInt(to_date_difference_from_current_date):0
$(function() {
    $( "#from_date").datepicker({ dateFormat: 'dd/mm/yy',
        showOn: "button",
        buttonImage: "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
        buttonImageOnly: true,
        buttonText: "Select date",
        maxDate:difference,
        beforeShowDay: function(date) {
            var selectedDate = $("#from_date").datepicker("getDate");
            if (selectedDate && date.getTime() === selectedDate.getTime()) {
              return [true, "highlight-selected-date", "Selected Date"];
            } else {
              return [true, "", ""];
            }
          }
    });
});
$(function() {
    $( "#to_date").datepicker({ dateFormat: 'dd/mm/yy',
        showOn: "button",
        buttonImage: "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
        buttonImageOnly: true,
        buttonText: "Select date",
        minDate: $("#from_date").datepicker("getDate"),
        maxDate:0,
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

function orderByFunction(type){
    let update_order = 'Descending';
    let new_url = '';
    const keys_for_ordering = ['order_by_id', 'order_by_date'];
    const params = new URLSearchParams(url_u);
    params.forEach(function(value, key) {
            if (key !== type) {
                if (!keys_for_ordering.includes(key)) new_url += `&${key}=${value}`;
            }
            else {
                if (value === `Ascending`) update_order = 'Descending'
                else update_order = 'Ascending'
            }
    });
    document.getElementById(type).classList.toggle('order-by');
    window.location.href = `${window_radirect_location}?${type}=${update_order}${new_url}`;
}