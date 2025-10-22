function showDownloadError(){
    $('#no_download_box').modal('show');
    setTimeout(function(){ $('#no_download_box').modal('hide'); }, 3000);
}

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
function orderByFunction(type){
    let update_order = 'Descending';
    let new_url = '';
    const keys_for_ordering = ['order_by_retail_barcode','order_by_m_code','order_by_start_date','order_by_end_date'];
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

function checkSearchBoxValue(){
    filterFunction('search',document.getElementById('search_station_param').value)
}
function appendDeleteContent(url, sid, name){
    const content =`
        <p class="delete-modal-text">Are you sure you want to remove <strong>${sid}</strong>, <strong>${name}</strong>?</p>
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

const slider = document.querySelector('#sliding_table');
let isDown = false;
let startX;
let scrollLeft;

slider.addEventListener('dblclick', (e) => {
    isDown = true;
    if (startX) startX = null;
    else {
        startX = e.pageX - slider.offsetLeft;
        scrollLeft = slider.scrollLeft;
    }
});
slider.addEventListener('mousemove', (e) => {
    if(!isDown) return;
    e.preventDefault();
    if (startX){
        
        const x = e.pageX - slider.offsetLeft;
        const walk = (x - startX) * 4  ; //scroll-fast
        slider.scrollLeft = scrollLeft - walk;
    }
});
let current_row = ''
function ecRow(row){
    const all_list = document.getElementsByClassName(`more_detailed_box`);
    const all_title_list = document.getElementsByClassName("title_of_content");
    const all_indicators = document.getElementsByClassName(`indicator`);
    
    let all_left_rows = document.getElementsByClassName('leftrows');
    for(var r of all_left_rows){
        r.style.height = 'auto'
    }
    if (row !== current_row){
        for (var d=0; d< all_list.length; d++){
            all_list[d].classList.remove('show_more');
            all_indicators[d].classList.remove('show_detailed');
            all_title_list[d].classList.remove('show_less');
        }
    }
    const list_of_content = document.getElementsByClassName(`more_detailed_box${row}`);
    const list_of_title = document.getElementsByClassName(`title_of_content${row}`);
    
    const list_of_indicators = document.getElementsByClassName(`indicator${row}`);


    for (var i=0; i< list_of_content.length;i++){
        list_of_content[i].classList.toggle('show_more');
        list_of_indicators[i].classList.toggle('show_detailed');
        list_of_title[i].classList.toggle('show_less');
    }
    const height = document.querySelector(`#right${row}`).offsetHeight;
    document.getElementById(`left${row}`).style.height = height+'px'
    current_row = row
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
    const action_boxes  = document.getElementsByClassName('active_status_box')
    let action_to_pass_to_backend = ''

    let status_content = '';
    action_boxes[n-1].innerHTML = 'Loading...'
    
    if (action === 'Active'){
        action_to_pass_to_backend ='Inactive'
        status_content = statusContentManager(id ,n, action_to_pass_to_backend);
    }else{
        action_to_pass_to_backend ='Active'
        status_content = statusContentManager(id ,n, action_to_pass_to_backend);
    }

    $.ajax({
            url: change_status_view_url,     
            data: {'getdata': JSON.stringify({'promotion_id': id, 'status': action_to_pass_to_backend})}, 
            headers: { "X-CSRFToken": token },
            dataType: 'json',
            type: 'POST',                                                                                                                                                                                                

            success: function (res, status) {
                $('#action_status_popup').modal('show');
                action_boxes[n-1].innerHTML = status_content;
                document.getElementById('updated_status').innerHTML = 'Succesfully updated status of promotion!!'
            },
            error: function (res) {   
                
                $('#action_status_popup').modal('show');
                document.getElementById('updated_status').innerHTML = 'Something went wrong!!'                                                                                                                  
            }

    });
    disableActionModal()
}


function processCSV(){
document.getElementById('upload_message').style.display='none';
let file=$("#selectSheet").get(0).files[0];
if (file){
    $('#loader_for_mfg_ev_app').show()
    let data = new FormData()
    data.append('file',file)
    $.ajax({
            url:uploadSheet_promotions_url,     
            data:file, 
            headers: { "X-CSRFToken": token },
            // dataType: 'form-data',
            type: 'POST',                                                                                                                                                                                                
            processData: false,
            success: function (res, status) {
                document.getElementById('progress_bar_box').style.display='block';
                data = res.response.data
                let error_list = []
                let have_field_errors = false
                if (res.response.status){
                    document.getElementById('bulk_upload_res_error').innerHTML =''
                    document.getElementById('bulk_upload_res_error').classList.remove('active_errors')
                    if (res.response.data.fields){
                        
                        document.getElementById('upload_message').style.display='flex';
                        have_field_errors =true
                        let error = ''
                        for(var i=0;i<res.response.data.data.length;i++){
                            error+= `<p class="error_fields">${i+1}.${res.response.data.data[i]}</p>`
                        }
                        var content =`
                                <div>
                                    <h6 class="filed_error_heading">Following Fields are missing in "Promotions" tab</h6>
                                    <div class="fields_errors">
                                        ${error}
                                    <div>
                                </div>`
                        document.getElementById('empty_column_errors').classList.add('active_errors')  
                        $("#empty_column_errors").append(content)
                        $("#empty_column_errors").append('<div class="horizontal-lines"></div>')
                        document.getElementById('bulk_upload_res_sucess').classList.remove('active_success')
                        document.getElementById('bulk_upload_res_sucess').innerHTML =''
                    }
                    else {
                        
                        error_list= [...error_list,...data.data];
                    }
                    if(res.response.c_data.fields){
                        
                        document.getElementById('upload_message').style.display='flex';
                        have_field_errors =true
                        document.getElementById('empty_column_errors').classList.add('active_errors')
                        let error = ''
                        for(i=0;i<res.response.c_data.data.length;i++){
                            error+= `<p class="error_fields">${i+1}.${res.response.c_data.data[i]}</p>`
                        }
                        
                        content =`
                                <div>
                                    <h6 class="filed_error_heading">Following Fields are missing in "Promotion assign" tab</h6>
                                    <div class="fields_errors">
                                        ${error}
                                    <div>
                                </div>` 
                        $("#empty_column_errors").append(content)
                    }else{
                        
                        error_list= [...error_list,...res.response.c_data.data];
                    }
                    
                    if (error_list.length >0 || have_field_errors === true) {
                        
                        document.getElementById('upload_message').style.display='flex';
                        document.getElementById('bulk_upload_res_error').classList.add('active_errors')
                        document.getElementById('bulk_upload_res_error').innerHTML =''
                        $('#bulk_upload_res_error').append(`<h6 class="bulk_upload_error">Bulk upload is interrupted by the below issues. Please update the sheet and try again.</h6>`)
                        addData(error_list,'Retail Barcode');

                    }
                    else{
                        document.getElementById('empty_column_errors').innerHTML =''
                        document.getElementById('empty_column_errors').classList.remove('active_errors')
                        
                        document.getElementById('bulk_upload_res_sucess').classList.add('active_success')
                        document.getElementById('bulk_upload_res_sucess').innerHTML =''
                        $('#bulk_upload_res_sucess').append(`<h6 class="bulk_upload_success">Successfully uploaded data</h6>`)
                    }
                }
                else{
                    document.getElementById('upload_message').style.display='flex';
                    document.getElementById('bulk_upload_res_error').classList.add('active_errors')
                    document.getElementById('bulk_upload_res_error').innerHTML =''
                    $('#bulk_upload_res_error').append(`<h6 class="bulk_upload_error">${res.response.error}</h6>`)
                }
                $('#loader_for_mfg_ev_app').hide();
            },
            error: function (error) {
                document.getElementById('upload_message').style.display='flex';
                $('#loader_for_mfg_ev_app').hide();
                if (error.status === 504) customAlert('Timeout - Please minimize data, and try again.');
                else if (error.status === 502) customAlert(`${error.statusText} , please try again.`); 
                else  customAlert(`Bulk upload intruppted due to - ${error.responseText}, please try again.`);                                                                                                                           
            }
    });
    progressChecker();
}

$('#upload').prop("disabled", true);
$('#selectSheet').val('');

}
var prevDropDownId = -1;
function changeStatus(id){
var dropDownId = "#"+"dropdownMenuButton"+id;

    if($("#dropdownMenuButton"+id).css('display') == 'none'){
        if(prevDropDownId != dropDownId && prevDropDownId > -1){
            if (document.getElementById("dropdownMenuButton"+prevDropDownId))
                document.getElementById("dropdownMenuButton"+prevDropDownId).style.display = "none";
        }
        prevDropDownId = id;
        document.getElementById("dropdownMenuButton"+id).style.display = "block";
    }else{
        prevDropDownId = -1;
        document.getElementById("dropdownMenuButton"+id).style.display = "none";
    }
}
