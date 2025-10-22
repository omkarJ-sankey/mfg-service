// this variable used in map.js to check if is updated data or not

let services_data1;
let connector_type_speed_html_new = '';
for (var i=0;i<connector_speed_types_list.length;i++){
    connector_type_speed_html_new+= `<option value="${connector_speed_types_list[i][0]}">${connector_speed_types_list[i][1]}</option>`
}

$(document).ready(function(){
    connector_count_manager.push(1);
    var  countClicked1 =1;
    let  countBackOffice =1;
    // let selected_back_offices = []
    appendChargePointForm(countClicked1)
    appendAddBackOfficeForm(countBackOffice,backoffice_list)
    const chargePointDataDummy = {
        charge_point_id: '',
        charge_point_name: '',
        status: '',
        // back_office:'',
        device_id:'',
        payter_terminal_id:'',
        ampeco_charge_point_id: '',
        ampeco_charge_point_name: '',
        worldline_terminal_id:'',
        connectors : [{
            connector_type: '',
            connector_id:'',
            connector_name:'',
            status: '',
            plug_type_name: '',
            maximum_charge_rate: '',
            tariff_amount: '',
            tariff_currency: '',
            connector_sorting_order: '',
            // back_office:'',
            evse_uid:'',
            ocpi_connector_id:'',
            deleted: false
        }],
        deleted:false,
    }
    const backOfficeDataDummy = {
        back_office:'',
        location_id:'',
        deleted:false
    }
    dataToUpload.chargepoints.push(chargePointDataDummy)
    dataToUpload.backoffice.push(backOfficeDataDummy)

    //Commented code for future reference 
    // appendAddBackOfficeForm(countBackOffice,all_back_offices,dataToUpload.backoffice)

  $("#addChargePointButton").click(function(){
    const chargePointDataToUpload = {
        charge_point_id: '',
        charge_point_name: '',
        status: '',
        // back_office:'',
        device_id:'',
        payter_terminal_id:'',
        ampeco_charge_point_id: '',
        ampeco_charge_point_name: '',
        worldline_terminal_id:'',
        connectors : [{
            connector_type: '',
            connector_id:'',
            connector_name:'',
            status: '',
            plug_type_name: '',
            maximum_charge_rate: '',
            tariff_amount: '',
            tariff_currency: '',
            connector_sorting_order: '',
            // back_office:'',
            evse_uid:'',
            ocpi_connector_id:'',
            deleted: false
        }],
        deleted:false,
    }
      countClicked1 = countClicked1 + 1;
      connector_count_manager.push(1);
      appendChargePointForm(countClicked1)
      dataToUpload.chargepoints.push(chargePointDataToUpload)
  });

//   $("#addBackOfficeButton").click(function(){
//     var backOfficeDataToUpload = {
//         back_office:'',
//         location_id:'',
//         deleted:false
//     }
//     //   countBackOffice = countBackOffice + 1;
//     //   back_office_count_manager.push(1);
//     len = dataToUpload.backoffice.length - deleted_backoffice_from_frontend.length
    
    
//     if ((backoffice_list.length > len) ){
//         countBackOffice++;
//         // appendAddBackOfficeForm(countBackOffice,all_back_offices,dataToUpload.backoffice)
//         dataToUpload.backoffice.push(backOfficeDataToUpload)
//     }
//     else{
//         document.getElementById(`append_back_office_error`).innerHTML = "More back offices are not available";
//     }
      
//   });


  
});

function appendAddBackOfficeForm(clicked, all_back_offices, selected_back_office_obj) {
    
    let optionsHTML = `<option value="">Select</option>`;
    all_back_offices.forEach(backoffice => {
        optionsHTML += `<option value="${backoffice}">${backoffice}</option>`;
    });

    $("#backOfficeContainer").append(`
        <div class="charge_point_details station_back_office_details" id="backoffice_id__${clicked}">
            <div class="back_office_heading collapsible">
                <div class="chargepoint_heading_container">
                    <span>Back Office</span>
                </div>
            </div>
            <div class="content">
                <div class="back_office_form">
                    <div class="back_office_fields">
                        <label class="labels">Back Office Name</label>
                        <select name="backOffice" class="back_office_select_class" id="back_office_input_${clicked}"
                            onchange="updateUploadedDataBackOffice(${clicked - 1}, 0, this.value);">
                            ${optionsHTML}
                        </select>
                        <p class="error_field" id="backOfficeError${clicked - 1}0"></p>
                    </div>
                    <div class="back_office_fields">
                        <label class="labels">Location ID</label>
                        <input type="text"  id="location_input_${clicked}" class="inputs" placeholder="Enter Location Id"
                            onchange="updateUploadedDataBackOffice(${clicked - 1}, 1, this.value);">
                        <p class="error_field" id="backOfficeError${clicked - 1}1"></p>
                    </div>
                </div>
            </div>
        </div>
    `);
}

// function removeBackOffice(id, number) {
//     id.style.display = 'none';
//     $('#delete_backoffice_confirmation_model').modal('hide');
//     document.getElementById(`append_back_office_error`).innerHTML = '';
//     document.getElementById('backoffice_delete_modal_content').innerHTML = '';
    
//     deleted_backoffice_from_frontend.push(number - 1);
// }


function appendConnectorForm(n){
        const connectorDataToUpload = {
            connector_type: '',
            connector_id:'',
            connector_name:'',
            status: '',
            plug_type_name: '',
            maximum_charge_rate: '',
            tariff_amount: '',
            tariff_currency: '',
            connector_sorting_order: '',
            // back_office: '',
            evse_uid: '',       
            ocpi_connector_id: '', 
            deleted:false,
        }
        connector_count_manager[n-1] = connector_count_manager[n-1] + 1;
        dataToUpload.chargepoints[n-1].connectors.push(connectorDataToUpload)    

        let back_office_data_html= ''
            for (var i=0;i<available_back_offices.length;i++){
                back_office_data_html+= `<option value="${available_back_offices[i]}">${available_back_offices[i]}</option>`
            }

      $(`#ConnectorContainer${n}`).append(`
      
      <div class="connectors_box" id="connector_delete_id_${n}_${connector_count_manager[n-1]}">
                        <div class="connector_heading collapsible1">
                            <div class="connector_heading_container">
                                <span>Connector ${connector_count_manager[n-1]}</span>
                                <div class="delete_bar"
                                    onclick="removeConnectorConfirmation('connector_delete_id_${n}_${connector_count_manager[n-1]}',
                                    ${connector_count_manager[n-1]},${n})"
                                 ></div>
                            </div>
                        </div>
                        <div class="content">
                            <div class="charge_point_form">                                                                                                                                                                                              
                                <div class="charge_point_fields">
                                    <label    class="labels">Connector Type</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] - 1 },${0},this.value,${100});">
                                            <option value="">Select</option>
                                            ${connector_type_speed_html_new}
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}0"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector ID</label>
                                    <input type="number"    class="inputs" placeholder="Enter connector ID" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] - 1 }, ${1}, this.value,${100} );"> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}1"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector Name</label>
                                    <input type="text"    class="inputs" placeholder="Enter connector name" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] - 1 }, ${2}, this.value,${100} );"> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}2"></p>
                                </div>
            
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Status</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] -1 },${3},this.value,${100});">
                                            <option value="">Select</option>
                                            <option value="Active">Active</option>
                                            <option value="Inactive">Inactive</option>
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}3"></p>
                                </div>
            
                            </div>
                            <div class="charge_point_form">                                                                                                                                                                                              
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Plug Type Name</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] - 1 },${4},this.value,${100});">
                                            <option value="">Select</option>
                                            ${connector_type_html}
                                        </select>
                                    </div> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}4"></p>
                                </div>                                                                                                                                                                                              
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Maximum Charge Rate</label>
                                    <input type="number"    class="inputs" placeholder="Enter charge rate" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] - 1},${5},this.value,${0});"> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}5"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Tariff Amount</label>
                                    <input type="number"  min="0"  class="inputs" placeholder="Enter tariff amount" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] -1 },${6},this.value,${100});"> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}6"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Tariff Currency</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] -1 },${7},this.value,${100});">
                                            <option value="">Select</option>
                                            <option value="GBP(£)">GBP (£)</option>
                                            <option value="Euro(€)">Euro (€)</option>
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}7"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector Sort Order</label>
                                    <input type="number"  min="0"  class="inputs" placeholder="Enter sort order" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] -1 },${8},this.value,${100});"> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}8"></p>
                                </div>


                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Evse UID</label>
                                    <input type="text"    class="inputs" placeholder="Enter ocpi evse uid" onchange="updateUploadedDataConnector(${n - 1} , ${connector_count_manager[n-1]-1}, ${9}, this.value,${100});"> 
                                    
                                    <p class="error_field" id="chargepointerror${n - 1}${connector_count_manager[n-1]-1}9"></p>
                                </div>

                                <div class="charge_point_fields">
                                
                                    <label    class="labels">OCPI Connector ID</label>
                                    <input type="text"    class="inputs" placeholder="Enter ocpi connector id" onchange="updateUploadedDataConnector(${n - 1} , ${connector_count_manager[n-1]-1}, ${10}, this.value,${100} );"> 
                                    
                                    <p class="error_field" id="chargepointerror${n - 1}${connector_count_manager[n-1]-1}10"></p>
                                </div>

                            </div>
                        </div>
                    </div>
      
      `);
}


var uploaded_images = [];
var remove_images = [];
var assign_food = [];
var assign_retail = [];
var assign_amenities = [];
var final_upload_images = [];
var temp_assign_food = [];
var temp_assign_retail = [];
var temp_assign_amenities = [];
let temp_uploaded_images = [];
let food
let retail
let amenities
({food, retail, amenities} = services_data)
let food_content = ''
let retail_content = ''
let amenities_content = ''



function removeAssignedImage(event) {
    temp_uploaded_images.splice(event.getAttribute("data"),1);
    remove_images.push(event.getAttribute("ref"));
    if(temp_uploaded_images.length == 0){
        $("#add_images_container").html(`<div class="text_container"><div class="text_for_images"><p>Click 'Add Images' to add images here</p></div></div>`);
    }else{
        const tempArray = temp_uploaded_images;
        temp_uploaded_images = [];
        tempArray.forEach(url => {
            if (temp_uploaded_images.length === 0){
                $("#add_images_container").html(`<div class="img-download">
                    <img src=${url} class="promotion_img_tag_style" alt="image">
                    <b class="promotion_discard_button-style" data="${temp_uploaded_images.length}" ref="${url}" id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
                    </div>`);
            }
            else
            { 
                $("#add_images_container").append(`<div class="img-download">
                    <img src=${url} class="promotion_img_tag_style" alt="image">
                    <b class="promotion_discard_button-style" data="${temp_uploaded_images.length}" ref="${url}" id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
                    </div>`);
            }
            temp_uploaded_images.push(url)
            
        });
    }
    if (temp_uploaded_images.length < 10) $("#add_images_count").html(`0${temp_uploaded_images.length} added`)
            else $("#add_images_count").html(`${temp_uploaded_images.length} added`) 
}

function addRemovedImages(){
    remove_images.forEach(x =>{
        uploaded_images.push(x);
    });
    remove_images = [];
}



function updateUploadedDataSet(n, val){
    const upload_keys = Object.keys(dataToUpload);
    if (n === 34) {
        dataToUpload.ampeco_site_title = val.trim() === "" ? null : val.trim();
        return;
    }
    if (n === 33) {
        dataToUpload.ampeco_site_id = val;
        return;
    }
    if (n === 31){
        let maxVal = 100;
        let num = parseFloat(val);
        maxVal = parseFloat(maxVal);
        if (num<0.0){
            document.getElementById(`error_field${n}`).innerHTML = "Value is not valid.";
        }else if(num>maxVal && maxVal!=0){
            document.getElementById(`error_field${n}`).innerHTML = "Can't be more than " + maxVal + ".";
        }else{
            document.getElementById(`error_field${n}`).innerHTML=''
        }
    }
    else if (n === 35){
        let maxVal = 200;
        maxVal = parseFloat(maxVal);
        if(val.length>maxVal && maxVal!=0){
            document.getElementById(`error_field${n}`).innerHTML = "You can't enter more than " + maxVal + " chars.";
        }else{
            document.getElementById(`error_field${n}`).innerHTML=''
        }
    }
     else if (val.length ===0){
        if(n != 3 && n != 4){
            document.getElementById(`error_field${n}`).innerHTML = "This field is required"        
        }
    } 
    else if (n===0 && val.length > 15){ 
        document.getElementById(`error_field${n}`).innerHTML = "You can't enter more than 15 chars"
    }
    else  if (val.length > 100){
        document.getElementById(`error_field${n}`).innerHTML = "You can't enter more than 100 chars"
    }
    dataToUpload[upload_keys[n]]= val
}

function updateUploadedDataSetSite(n, val){
    const upload_keys = Object.keys(dataToUpload.stationTypeSiteData);
    dataToUpload.stationTypeSiteData[upload_keys[n]]= val
    if (val.length ===0){
        if(n != 3 && n != 4) {
            document.getElementById(`error_field_site${n}`).innerHTML = "This field is required"

        }
    } 
    else  if (val.length > 100){
        document.getElementById(`error_field_site${n}`).innerHTML = "You can't enter more than 100 chars"
    }
}

// variables for timing selection
var mon_fri = 'Mon-Fri'
var sat = 'Sat'
var sun ='Sun'
var prev_mon_fri = null
var prev_sat = null
var prev_sun = null
function updateUploadedDataSetWorkingHours(n, m, val){
    const working_hours_spans = document.getElementsByClassName('working_hours_span')
    const upload_keys = Object.keys(dataToUpload.working_hours);
    const timing_var = upload_keys[n]
    
    if (m===0){    
        const checking_past_value = dataToUpload.working_hours[timing_var].full_hours
        dataToUpload.working_hours[timing_var].full_hours = !checking_past_value
    }else if (m===1){
        
        dataToUpload.working_hours[timing_var].start_time = val
    }else{
        
        dataToUpload.working_hours[timing_var].end_time = val
    }
    working_hours_spans[n].innerHTML = ""
    var text = ''
    if(n===0)
    {   
        
        if (m===0){
            
            
            if (m===prev_mon_fri) {
                prev_mon_fri=null
            }
            else {
                text = `${mon_fri} : 24 hours, `;
                prev_mon_fri=0
            }
        }else{
            
            text = `${mon_fri} : ${dataToUpload.working_hours[timing_var].start_time}-${dataToUpload.working_hours[timing_var].end_time}, `

        }
        working_hours_spans[n].innerHTML = text
    }
    else if (n===1){
        if (m===0){
            if (m===prev_sat){
                prev_sat=null
            }
            else {
                text = `${sat} : 24 hours, `;
                prev_sat=0
            }
        }else{
            
            text= `${sat} : ${dataToUpload.working_hours[timing_var].start_time}-${dataToUpload.working_hours[timing_var].end_time} ,`

        }
        if (working_hours_spans[0].innerHTML ==='Select working hours')working_hours_spans[0].innerHTML =''
        working_hours_spans[n].innerHTML = text
    }
    else {
        if (m===0){
            if (m===prev_sun) {
                prev_sun=null
            }
            else {
                text = `${sun} : 24 hours, `;
                prev_sun=0
            }
        }else{
            
            text = `${sun} : ${dataToUpload.working_hours[timing_var].start_time}-${dataToUpload.working_hours[timing_var].end_time} `

        }
        
        if (working_hours_spans[0].innerHTML ==='Select working hours')working_hours_spans[0].innerHTML =''
        working_hours_spans[n].innerHTML = text
    }
}
function updateUploadedDataChargePoint(n,m,val){
    const upload_keys = Object.keys(dataToUpload.chargepoints[n-1]);
    let chargepoint_data = dataToUpload.chargepoints[n-1];
    chargepoint_data[upload_keys[m]] = val;
    let worldLineStationCheck = (
        (
            dataToUpload["payment_terminal"] === 'Worldline' &&
            m !== 5
        ) || dataToUpload["payment_terminal"] !== 'Worldline'
    );
    // if (m !==3){
    if (val.length ===0 && worldLineStationCheck){
        document.getElementById(`chargepointerror${n-1}${m}`).innerHTML = "This field is required"
    }
    else if (m===3 && !parseInt(val)){
            document.getElementById(`chargepointerror${n-1}${m}`).innerHTML = "Only numbers are allowed."
    }
    else if (val.length > 15 && m===0){ 
        document.getElementById(`chargepointerror${n-1}${m}`).innerHTML = "You can't enter more than 15 chars"
    }else  if (val.length > 25 && worldLineStationCheck){
        document.getElementById(`chargepointerror${n-1}${m}`).innerHTML = "You can't enter more than 25 chars"
    }
// }
    else document.getElementById(`chargepointerror${n-1}${m}`).innerHTML =""
}


function updateUploadedDataBackOffice(n,m,val){
    // let backoffice_data = dataToUpload.backoffice[n];
    let backoffice_data = dataToUpload.backoffice[n];
    const upload_keys = Object.keys(backoffice_data);
    backoffice_data[upload_keys[m]] = val;     

    const inputEl = document.getElementById(`back_office_input_${n}`);
    if (inputEl) {
        const valueToRemove = inputEl.value;

        const index = backoffice_list.indexOf(valueToRemove);
        if (index > -1) {
            backoffice_list.splice(index, 1); 
        } else {
            console.log(`${valueToRemove} not found in bo`);
        }
    }
    // backoffice_list.pop(backOfficeDataToUpload)

    // optionsHTML = `<option value="">Select</option>`;
    // backoffice_list.forEach(backoffice => {
    //     optionsHTML += `<option value="${backoffice}">${backoffice}</option>`;
    // });
    // document.getElementById(`backOfficeError${n}${m}`).innerHTML
    
    if (val.length === 0 ){
        document.getElementById(`backOfficeError${n}${m}`).innerHTML = "This field is required"
    }
    else document.getElementById(`backOfficeError${n}${m}`).innerHTML =""
}

function updateUploadedDataConnector(c,n,m,val,maxVal){
    let numeric_fields = [5,6,8]
    let upload_keys = Object.keys(dataToUpload.chargepoints[c].connectors[n]);
    
    let connector_updated_data = dataToUpload.chargepoints[c].connectors[n]
    if (val.length ===0){
        document.getElementById(`chargepointerror${c}${n}${m}`).innerHTML = "This field is required"
    }else if (numeric_fields.includes(m)){
        let num = parseFloat(val);
        maxVal = parseFloat(maxVal);
        if (num<=0.0){
            document.getElementById(`chargepointerror${c}${n}${m}`).innerHTML = "Value is not valid.";
        }else if(num>maxVal && maxVal!=0){
            document.getElementById(`chargepointerror${c}${n}${m}`).innerHTML = "Can't be more than " + maxVal + ".";
        }else{
            document.getElementById(`chargepointerror${c}${n}${m}`).innerHTML=''
        }
    } 
    else if (val.length > 15 && m===1){      
        document.getElementById(`chargepointerror${c}${n}${m}`).innerHTML = "You can't enter more than 15 chars"
    }else  if (val.length > 25){
        document.getElementById(`chargepointerror${c}${n}${m}`).innerHTML = "You can't enter more than 25 chars"
    }
    
    if (numeric_fields.includes(m)){
        connector_updated_data[upload_keys[m]] = parseFloat(val)
    }
    else{ 
        connector_updated_data[upload_keys[m]] = val
    }
}


function toggleModal(n){
    const contents = [ "Assign Retail", "Assign Images","Assign Food To Go","Assign Amenities"]
    var modal = document.getElementById("side_modal_id");
    modal.classList.toggle("active");
    let content_to_be_embed_in_side_modal 
    
    let images_divs = document.getElementsByClassName('images_div');
    if (n){
        
        if (images_divs[n].style.display === 'none'){
            images_divs[n].style.display = 'block'
        }  
    }      

    if (n === 1) {
        
        temp_uploaded_images = [...uploaded_images];
        var content_image_container  = ''
        if (uploaded_images.length > 0){
            for( i=0 ; i< uploaded_images.length; i++){
                content_image_container += `<div class="img-download">
                    <img src=${uploaded_images[i]} class="promotion_img_tag_style" alt="image">
                    <b class="promotion_discard_button-style" data="${i}" ref="${uploaded_images[i]}" id="discard_edit" ref="${uploaded_images[i]}" onclick="removeAssignedImage(this)" class="discard">x</b>
                    </div>`
                
            }
        }
        else{
            content_image_container = `<div class="text_container"><div class="text_for_images"><p>Click 'Add Images' to add images here</p></div></div>`
        } 
        content_to_be_embed_in_side_modal = ` <div class="content_of_modal"> 
                <div class="side_modal_heading">
                    <p>${contents[n]}</p>
                    <button class="close_button" onclick="toggleModal();"><img src=${cross_one_icn_url}></button>
        
                </div>
                <div class="side_modal_heading1">
                    <p id="add_images_count">0${uploaded_images.length} added</p>
                    
                    <input type="file" id="i_file" name="filename" hidden accept=".jpeg,.jpg,.png"/>
                    <label for="i_file" class="add_images_label">Add images</label>
                </div>
                <div class="horizontal-lines"></div>
                <div id="add_images_container">
                    ${
                        content_image_container
                    }
                </div>
            </div>
            <div class="add_images_button_cotainer">
                <button class="cancel_image_button" onclick="toggleModal();">Cancel</button>
                <button class="assign_image" onclick="appendImages(${n});">Assign</button>
            </div>`
    }
    else{
        var inner_content = ''
        var selected_count = 0
        if (n === 0) {
            retail_content =append_retail_images_side_bar(temp_assign_retail);
            inner_content = retail_content;
            selected_count = temp_assign_retail.length
        }
        else if ( n===2){
            food_content = append_food_images_side_bar(temp_assign_food);
            inner_content = food_content;
            selected_count = temp_assign_food.length;
        }
        else if(n===3){
            amenities_content = append_amenity_images_side_bar(temp_assign_amenities)
            inner_content = amenities_content;
            selected_count = temp_assign_amenities.length;
        } 
        content_to_be_embed_in_side_modal = ` <div class="content_of_modal"> 
                <div class="side_modal_heading">
                    <p>${contents[n]}</p>
                    <button class="close_button" onclick="toggleModal();"><img src=${cross_one_icn_url}></button>
        
        
                </div>
                <div class="side_modal_heading1">
                    <p id='add_images_count1'>0${selected_count} selected</p>
                </div>
                <div class="horizontal-lines"></div>
                <div id="add_services_container">
                    ${inner_content}
                </div>
            </div>
            <div class="add_images_button_cotainer">
                <button class="cancel_image_button" onclick="toggleModal();">Cancel</button>
                <button class="assign_image" onclick="appendServices(${n});">Assign</button>
            </div>`
    }
    
    $("#dynamic_content_container").html(content_to_be_embed_in_side_modal);

  }

  function appendImages(){
      
    uploaded_images = temp_uploaded_images;
      remove_images = [];
      final_upload_images = [];
      let content_for_image_container  = ''
      for( i=0 ; i< uploaded_images.length; i++){
          final_upload_images.push(uploaded_images[i]);
          content_for_image_container += `<img id="assignedImg" src=${uploaded_images[i]} >`
      }
      dataToUpload.images = uploaded_images
      $("#images_container").html(content_for_image_container);
      toggleModal(1);
  }
