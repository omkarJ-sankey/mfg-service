function showDownloadError(){
    $('#no_download_box').modal('show');
    setTimeout(function(){ $('#no_download_box').modal('hide'); }, 3000);
}

$(function() {
    let from_date_object = { 
        dateFormat: 'dd/mm/yy',
        showOn: "button",
        buttonImage: "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
        buttonImageOnly: true,
        buttonText: "Select date",
        beforeShowDay: function(date) {
            var selectedDate = $("#from_date").datepicker("getDate");
    
            if (selectedDate && date.getTime() === selectedDate.getTime()) {
            return [true, "highlight-selected-date", "Selected Date"];
            } else {
            return [true, "", ""];
            }
        }
    }
    $("#from_date").datepicker(from_date_object);
});

$(function() {
    $("#to_date").datepicker({ dateFormat: 'dd/mm/yy',
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
function orderByFunction(type){
    let update_order = 'Descending';
    let keys_for_ordering = ['order_by_product_bar_code','order_by_start_date','order_by_end_date'];
    let params = new URLSearchParams(url_u);
    let new_url = '';

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

function checkSearchBoxValue(){
    filterFunction('search',document.getElementById('search_station_param').value)
}
function appendDeleteContent(url, name){
    content =`
        <p class="delete-modal-text">Are you sure you want to remove <strong>${name}</strong></p>
        <div class="google_maps_submit_buttons">
            <div class="google_maps_container_buttons">
                
                <button class="cancle_button" data-bs-dismiss="modal">No</button>
                &nbsp;
                <a href="${url}"><button class="done_button">Yes</button></a>
            </div>
        </div>
    `
    document.getElementById('delete-modal-content').innerHTML= content
}


function disableActionModal() {
setTimeout(function(){  $('#action_status_popup').modal('hide'); }, 2000);
}
// function to make call for active and inactive of promotions

const statusContentManager = (id, n, action) => (action === 'Inactive')? `
    <div class="inactive_status"></div>Inactive
    <div class="dropdown display-none-style-promotion-status"  id="dropdownMenuButton${id}" >
        <ul class="dropdown-menu show dropdown-menu-style">
            <li class="text_align_style">
                <p class="dropdown-item" onclick="makeAction('${n}', 'Inactive', ${id});">Make Active</p>
            </li>
        </ul>
    </div>
    <div class="dots"  onclick="changeStatus('${id}')" ><span></span><span></span><span></span></div>
`: `
    <div class="active_status"></div>Active
    <div class="dropdown display-none-style-promotion-status"  id="dropdownMenuButton${id}" >
        <ul class="dropdown-menu show dropdown-menu-style">
            <li class="text_align_style">
                <p class="dropdown-item" onclick="makeAction('${n}', 'Active', ${id});">Make Inactive</p>
            </li>
        </ul>
    </div>
    <div class="dots"  onclick="changeStatus('${id}')" ><span></span><span></span><span></span></div>
`;

function makeAction(n, action, id){
    let action_boxes  = document.getElementsByClassName('active_status_box')
    let action_to_pass_to_backend = ''
    let status_content = '';
    let failed_content = '';

    action_boxes[n-1].innerHTML = 'Loading...'
    
    if (action === 'Active'){
        action_to_pass_to_backend ='Inactive'
        status_content = statusContentManager(id ,n, action_to_pass_to_backend);
        failed_content = statusContentManager(id ,n, 'Active');
    }else{
        action_to_pass_to_backend ='Active'
        status_content = statusContentManager(id ,n, action_to_pass_to_backend);
        failed_content = statusContentManager(id ,n, 'Inactive');
    }


    $.ajax({
            url: change_status_view_url,     
            data: {'getdata': JSON.stringify({'loyalty_id': id, 'status': action_to_pass_to_backend})}, 
            headers: { "X-CSRFToken": token },
            dataType: 'json',
            type: 'POST',                                                                                                                                                                                                

            success: function (res, status) {
                $('#action_status_popup').modal('show');
                action_boxes[n-1].innerHTML = (res.status) ? status_content: failed_content;
                document.getElementById('updated_status').innerHTML = res.message
            },
            error: function (res) {   
                
                $('#action_status_popup').modal('show');
                document.getElementById('updated_status').innerHTML = 'Something went wrong!!'                                                                                                                  
            }

    });
    disableActionModal()
}

var prevDropDownId = -1;
function changeStatus(id){
    var dropDownId = "#"+"dropdownMenuButton"+id;
    if($("#dropdownMenuButton"+id).css('display') == 'none'){
        if(prevDropDownId != dropDownId && prevDropDownId > -1){
            document.getElementById("dropdownMenuButton"+prevDropDownId).style.display = "none";
        }
        prevDropDownId = id;
        document.getElementById("dropdownMenuButton"+id).style.display = "block";
    }else{
        prevDropDownId = -1;
        document.getElementById("dropdownMenuButton"+id).style.display = "none";
    }
}