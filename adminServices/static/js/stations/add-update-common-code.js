$(document).ready(function () {
    checkIfValeting();
    checkPaymentTerminal();
    displayTerminals();


  })
  let options ='<option selected value="">Select</option>';

var dataToUpload = {
    station_id: '',
    station_name: '',
    address_line1: '',
    address_line2: '',
    address_line3: '',
    town: '',
    postal_code: '',
    country: 'England',
    brand: '',
    owner: '',
    email: '',
    phone: '',
    latitude: 0.0,
    longitude: 0.0,
    working_hours: {
        monday_friday: {
            full_hours: false,
            start_time: '',
            end_time: ''
        },
        saturday: {
            full_hours: false,
            start_time: '',
            end_time: ''
        },
        sunday: {
            full_hours: false,
            start_time: '',
            end_time: ''
        },
    },
    status: '',
    station_type_is_mfg: true,
    station_type: 'MFG EV',
    stationTypeSiteData: {
        site_title: '',
        operation_region: '',
        region: '',
        regional_manager: '',
        area: '',
        area_regional_manager: ''
    },
    chargepoints: [],
    retail: [],
    retail_timing: [],
    images: [],
    food_to_go: [],
    food_timing: [],
    amenities: [],
    amenity_timing: [],
    site_id: null,
    valeting: 'No',
    payment_terminal:[],
    rh_site_name:'',
    overstay_fee: 0,
    valeting_site_id:null,
    ampeco_site_id: null,
    ampeco_site_title: null,
    parking_details: null,
    backoffice:[],
}

var countClicked1 = 1;
var countClicked2 = 1;

var connector_count_manager = []
var back_office_count_manager = []
let deleted_chargepoint_from_frontend = []
let deleted_backoffice_from_frontend = []
let deleted_connectors_from_frontend = []


function showCanclePopup() {
    $('#cancle_submit_warning_popup').modal('show');
}


var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function () {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.display === "none") {
            content.style.display = "block";
        } else {
            content.style.display = "none";
        }
    });
}

var coll = document.getElementsByClassName("collapsible1");
var i;

for (i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function () {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.display === "none") {
            content.style.display = "block";
        } else {
            content.style.display = "none";
        }
    });
}


var arrayOfChecklist = []
var checkboxes = document.querySelectorAll('.payment-terminal-check:checked')
function displayTerminals(selectedOption="") {
    arrayOfChecklist = []
    checkboxes = document.querySelectorAll('.payment-terminal-check:checked')
    for (var i = 0; i < checkboxes.length; i++) {
        arrayOfChecklist.push(checkboxes[i].value)
        if (arrayOfChecklist.includes("None") && (selectedOption==="" || selectedOption==="None")) {
            arrayOfChecklist=["None"]
            document.querySelectorAll('.payment-terminal-check:checked').forEach(checkbox => {
                checkbox.checked = false;
            });
            document.getElementById('payment-terminal-None').checked = true;
            $('.rh-site-name-field').attr("style", "display:none");
            break;
        }
        else if (arrayOfChecklist.includes("Worldline")) {
            arrayOfChecklist=arrayOfChecklist.filter(item => item !== "None");
            document.getElementById('payment-terminal-None').checked = false;
            $('.rh-site-name-field').attr("style", "display:flex");
        }
        else if(!arrayOfChecklist.includes("Worldline")) {  
            arrayOfChecklist=arrayOfChecklist.filter(item => item !== "None");
            document.getElementById('payment-terminal-None').checked = false;
            $('.rh-site-name-field').attr("style", "display:none");
        }
    }
    if (arrayOfChecklist.length != 0) {
        if (arrayOfChecklist) {
        const index = arrayOfChecklist.indexOf('Worldline');
        const modifiedArray = [...arrayOfChecklist];
        if (index !== -1) {
            modifiedArray[index] = 'Receipt Hero';
        }
        document.getElementById('terminal-list').innerHTML = modifiedArray.join(', '); 
        }
    }
    else {
        document.getElementById('terminal-list').innerHTML = "Select"
        $('.rh-site-name-field').attr("style", "display:none");
    }
}

function getArrayOfChecklist() {
    arrayOfChecklist = []
    checkboxes = document.querySelectorAll('.payment-terminal-check:checked')
    for (var i = 0; i < checkboxes.length; i++) {
        arrayOfChecklist.push(checkboxes[i].value)
    }
    return arrayOfChecklist
}


// working hours toggle time selection
function timingSelection(n) {
    const hours = document.getElementsByClassName("hours");
    const selections = document.getElementsByClassName("selectt");
    const content = hours[n]

    content.classList.toggle("active");
    let s = n * 2
    let s1 = selections[s]
    let s2 = selections[s + 1]
    s1.toggleAttribute("disabled");
    s2.toggleAttribute("disabled");
    s1.classList.toggle("active");
    s2.classList.toggle("active");
}



function assign_images(id, type) {
    if (type === 'food') {
        if (temp_assign_food.includes(id)) {
            const position = temp_assign_food.indexOf(id)
            temp_assign_food.splice(position, 1)
        }
        else temp_assign_food.push(id)
        document.getElementById('add_images_count1').innerHTML = `0${temp_assign_food.length} selected`
    } else if (type === 'retail') {
        if (temp_assign_retail.includes(id)) {
            const position = temp_assign_retail.indexOf(id)
            temp_assign_retail.splice(position, 1)
        }
        else temp_assign_retail.push(id);
        document.getElementById('add_images_count1').innerHTML = `0${temp_assign_retail.length} selected`;
    } else {
        if (temp_assign_amenities.includes(id)) {
            const position = temp_assign_amenities.indexOf(id)
            temp_assign_amenities.splice(position, 1)
        }
        else temp_assign_amenities.push(id)
        document.getElementById('add_images_count1').innerHTML = `0${temp_assign_amenities.length} selected`
    }
}

function toggleTimingStyle(id_type) {
    const content = document.getElementById(`content${id_type}`);
    if (assign_food.includes(id_type)) {
        if (content.style.display === "block") {
            content.style.display = "none";
        } else {
            content.style.display = "block";
        }
    } else {
        document.getElementById(`food_error${id_type}`).innerHTML = "please select checkbox";
    }
}



function appendChargePointForm(clicked) {

    let back_office_data_html= ''
            for (var i=0;i<available_back_offices.length;i++){
                back_office_data_html+= `<option value="${available_back_offices[i]}">${available_back_offices[i]}</option>`
            }
    deleted_connectors_from_frontend.push([])
    $("#chargingPointContainer").append(` 
    
        <div class="charge_point_details" id="chargepoint_id__${clicked}"
            >

            <div class="charge_point_heading collapsible">
                <div class="chargepoint_heading_container">
                    <span>Charge Point ${clicked}</span>
                    <div class="delete_bar deleted"
                        onclick="removeChargepointConfirmation('chargepoint_id__${clicked}', ${clicked})"></div>
                </div>
            </div>
            <div class="content">
                <div class="charge_point_form">                                                                                                                                                                                              
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Charge Point ID</label>
                        <input type="text"    class="inputs" placeholder="Enter charge point id" onchange="updateUploadedDataChargePoint(${clicked},${0},this.value);"> 
                        
                        <p class="error_field" id="chargepointerror${clicked - 1}0"></p>
                    </div>                                                                                                                                                                                              
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Charge Point Name</label>
                        <input type="text"    class="inputs" placeholder="Enter charge point name" onchange="updateUploadedDataChargePoint(${clicked},${1},this.value);"> 
                        
                        <p class="error_field" id="chargepointerror${clicked - 1}1"></p>
                    </div>

                    <div class="charge_point_fields">
                    
                        <label    class="labels">Status</label>
                        <div class="station_select-box charge_point_field">
                            <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataChargePoint(${clicked},${2},this.value);">
                                <option value="">Select</option>
                                <option value="Active">Active</option>
                                <option value="Inactive">Inactive</option>
                            </select>
                        </div>
                        <p class="error_field" id="chargepointerror${clicked - 1}2"></p>
                    </div>

    
                                                                                                                                                                                                          
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Device id</label>
                        <input type="number"    class="inputs" placeholder="Enter device id" onchange="updateUploadedDataChargePoint(${clicked},${3},this.value);"> 
                        
                        <p class="error_field" id="chargepointerror${clicked - 1}3"></p>
                    </div>                                                                                                                                                                                        
                    <div class="charge_point_fields">
                    
                        <label    class="labels">Payter terminal id</label>
                        <input type="text"    class="inputs" placeholder="Enter terminal id" onchange="updateUploadedDataChargePoint(${clicked},${4},this.value);"> 
                        
                        <p class="error_field" id="chargepointerror${clicked - 1}4"></p>
                    </div>

                    <div class="charge_point_fields">
                        <label    class="labels">Worldline Terminal ID</label>
                        <input type="text"    class="inputs" placeholder="Enter terminal id" onchange="updateUploadedDataChargePoint(${clicked},${7},this.value);">
                        <p class="error_field" id="chargepointerror${clicked - 1}7"></p>
                    </div>

                    <div class="charge_point_fields">
                        <label class="labels">Ampeco Charge Point ID</label>
                        <input type="text" class="inputs" placeholder="Enter Ampeco Charge Point ID" onchange="updateUploadedDataChargePoint(${clicked},${5},this.value);">
                        <p class="error_field" id="chargepointerror${clicked - 1}5"></p>
                    </div>
                    
                    <div class="charge_point_fields">
                        <label class="labels">Ampeco Charge Point Name</label>
                        <input type="text" class="inputs" placeholder="Enter Ampeco Charge Point Name" onchange="updateUploadedDataChargePoint(${clicked},${6},this.value);">
                        <p class="error_field" id="chargepointerror${clicked - 1}6"></p>
                    </div>

                </div>

                <!-- connector fields -->
                <div id="ConnectorContainer${clicked}">
                    
                    <div class="connectors_box" id="connector_delete_id_${clicked}_1">
                        <div class="connector_heading collapsible1">
                            <div class="connector_heading_container">
                                <span>Connector 1</span>
                                <div class="delete_bar"
                                    onclick="removeConnectorConfirmation('connector_delete_id_${clicked}_1',
                                    1,${clicked})"
                                 ></div>
                            </div>
                            
                        </div>
                        <div class="content">
                            <div class="charge_point_form">                                                                                                                                                                                              
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector Type</label>
                                    <div class="station_select-box charge_point_field" >
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${clicked - 1} , ${0}, ${0}, this.value,${100} );">
                                            <option value="">Select</option>
                                            ${connector_type_speed_html_new}
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${clicked - 1}${0}0"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector ID</label>
                                    <input type="number"    class="inputs" placeholder="Enter connector ID" onchange="updateUploadedDataConnector(${clicked - 1} , ${0}, ${1}, this.value,${100} );"> 
                                    
                                    <p class="error_field" id="chargepointerror${clicked - 1}${0}1"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector Name</label>
                                    <input type="text"    class="inputs" placeholder="Enter connector name" onchange="updateUploadedDataConnector(${clicked - 1} , ${0}, ${2}, this.value,${100} );"> 
                                    
                                    <p class="error_field" id="chargepointerror${clicked - 1}${0}2"></p>
                                </div>
            
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Status</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${clicked - 1},${0},${3},this.value,${100});">
                                            <option value="">Select</option>
                                            <option value="Active">Active</option>
                                            <option value="Inactive">Inactive</option>
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${clicked - 1}${0}3"></p>
                                </div>
            
                            </div>
                            <div class="charge_point_form">                                                                                                                                                                                              
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Plug Type Name</label>
                                    <div class="station_select-box charge_point_field" >
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${clicked - 1} , ${0}, ${4}, this.value,${100} );">
                                            <option value="">Select</option>
                                            ${connector_type_html}
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${clicked - 1}${0}4"></p>
                                </div>                                                                                                                                                                                              
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Maximum Charge Rate</label>
                                    <input type="number"    class="inputs" placeholder="Enter charge rate" onchange="updateUploadedDataConnector(${clicked - 1} , ${0}, ${5}, this.value,${0} );"> 
                                    
                                    <p class="error_field" id="chargepointerror${clicked - 1}${0}5"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Tariff Amount</label>
                                    <input type="number" min ="0"   class="inputs" placeholder="Enter tariff amount" onchange="updateUploadedDataConnector(${clicked - 1} , ${0}, ${6}, this.value,${100} );"> 
                                    
                                    <p class="error_field" id="chargepointerror${clicked - 1}${0}6"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Tariff Currency</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${clicked - 1} , ${0}, ${7}, this.value,${100} );">
                                            <option value="">Select</option>
                                            <option value="GBP(£)">GBP (£)</option>
                                            <option value="Euro(€)">Euro (€)</option>
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${clicked - 1}${0}7"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector Sort Order</label>
                                    <input type="number" min ="0"   class="inputs" placeholder="Enter sort order" onchange="updateUploadedDataConnector(${clicked - 1} , ${0}, ${8}, this.value,${100} );"> 
                                    
                                    <p class="error_field" id="chargepointerror${clicked - 1}${0}8"></p>
                                </div>

                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Evse UID</label>
                                    <input type="text"    class="inputs" placeholder="Enter ocpi evse uid" onchange="updateUploadedDataConnector(${clicked - 1} , ${0}, ${9}, this.value,${100});"> 
                                    
                                    <p class="error_field" id="chargepointerror${clicked - 1}${0}9"></p>
                                </div>

                                <div class="charge_point_fields">
                                
                                    <label    class="labels">OCPI Connector ID</label>
                                    <input type="text"    class="inputs" placeholder="Enter ocpi connector id" onchange="updateUploadedDataConnector(${clicked - 1} , ${0}, ${10}, this.value,${100} );"> 
                                    
                                    <p class="error_field" id="chargepointerror${clicked - 1}${0}10"></p>
                                </div>
            
                            </div>
                        </div>
                    </div>
                </div>
                    
                <div class="charge_point_button_container1">
                    
                    <button class="add_charge_point" onclick="appendConnectorForm(${clicked});">
                        <img src=${plus_sign_icn_url} class="add_image"></button>

                </div>
            </div>
            </div>
    `);
}


function getSelectedBackOffices() {
    let selected = [];
    
    $('.back_office_select_class').each(function() {
        let val = $(this).val();
        if (val) selected.push(val);
    });
    return selected;
}


function updateChargePointBackOfficeDropdowns() {
    let selectedBackOffices = getSelectedBackOffices();
    $('.charge_point_backoffice_select').each(function() {
        let currentVal = $(this).val();
        let options ='<option value="">Select</option>';
        let val
        options = '<option selected value="">Select</option>'; 
        [...new Set(selectedBackOffices)].forEach(function(bo) {
            val = bo
            options += `<option value="${bo}" >${bo}</option>`;
            if (bo === currentVal){
                val = bo;
            }
        });
        $(this).html(options);
        // $(this).val(val);
    
    });
}

$(document).on('change', '.back_office_select_class', function() {
    updateChargePointBackOfficeDropdowns();
});


function checkingMFGSite() {
    const x = document.getElementById("MFGEVSiteCheck").value;

    const content = document.getElementById('toggleOnSection');
    const chargepoint_content = document.getElementById('charge_point_container');
    const back_office_content = document.getElementById('back_office_container');
    const driivz_site_id = document.getElementById("driivz_site_id");

    if (x === 'MFG Forecourt' || x === 'MFG EV' || x === 'MFG EV plus Forecourt') {
        content.style.display = "";
        dataToUpload.station_type_is_mfg = true
        if (x === 'MFG Forecourt') {
            chargepoint_content.style.display = "none";
            back_office_content.style.display = "none";
            driivz_site_id.style.display = 'none';
        }
        else {
            chargepoint_content.style.display = "";
            back_office_content.style.display = "";
            driivz_site_id.style.display = 'block';
        }
    }
    else {
        chargepoint_content.style.display = "";
        back_office_content.style.display = "";
        content.style.display = "none";
        driivz_site_id.style.display = "none";
        dataToUpload.station_type_is_mfg = false
    }
    if (x === 'MFG Forecourt') {
        document.getElementById("chargePointDetails").style.display = 'none';
    } else {
        document.getElementById("chargePointDetails").style.display = 'block';
    }
}





$(document).on('change', '#i_file', function (event) {
    if (event.target.files) {
        const reader = new FileReader();
        reader.onload = (event) => {
            let url = event.target.result;
            if (temp_uploaded_images.length === 0) $("#add_images_container").html(`<div class="img-download">
                    <img src=${url} class="promotion_img_tag_style" alt="image">
                    <b class="promotion_discard_button-style" data="${temp_uploaded_images.length}" ref=${url} id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
                    </div>`);
            else $("#add_images_container").append(`<div class="img-download">
                    <img src=${url} class="promotion_img_tag_style" alt="image">
                    <b class="promotion_discard_button-style" data="${temp_uploaded_images.length}" ref=${url} id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
                    </div>`);

            temp_uploaded_images.push(url);
            if (temp_uploaded_images.length < 10) $("#add_images_count").html(`0${temp_uploaded_images.length} added`)
            else $("#add_images_count").html(`${temp_uploaded_images.length} added`)
        }
        reader.readAsDataURL(event.target.files[0]);
    }
});


var assign_amenities_time_availability = [];
var assign_retail_time_availability = [];
var assign_food_time_availability = [];

function searchShopIds(id, Array) {
    for (var i = 0; i < Array.length; i++) {
        if (Array[i].id === id) {
            return i;
        }
    }
}
function append_food_images_side_bar(arr) {
    let food_content = "";
    for (i = 0; i < food.length; i++) {
        var food_set_availability_object = {
            id: food[i].id,
            start: '',
            end: '',
            days: [],

        }
        assign_food_time_availability.push(food_set_availability_object)
        let img_url = food[i].image_path;
        if (i === 0) $(`#images_container2`).html('');
        if (arr.includes(food[i].id)) {
            $(`#images_container2`).append(`<div class="services_image"><img src=${food[i].image_path} ></div>`);
        }

        food_content += `
        <div class="sub_services_data">
            <div class="services_img_container"><img src=${img_url}></div>
        
            <div class="sub_service_data">
                <p>${food[i].service_name}</p>
            </div>
            <input type="checkbox" class="services_ckeckbox" ${arr.includes(food[i].id) ? 'checked' : ''} value=${food[i].id} onclick="assign_images(${food[i].id}, 'food');">
    
        </div>
        <div class="horizontal-lines1"></div>
        
        `;
    }
    return food_content

}

function append_retail_images_side_bar(arr) {
    let retail_content = "";
    for (let i = 0; i < retail.length; i++) {

        var retail_set_availability_object = {
            start: '',
            end: '',
            days: [],

        }
        assign_retail_time_availability.push(retail_set_availability_object)
        let img_url = retail[i].image_path;

        if (i === 0) $(`#images_container0`).html('');
        if (arr.includes(retail[i].id)) {
            $(`#images_container0`).append(`<div class="services_image"><img src=${retail[i].image_path} ></div>`);
        }
        retail_content += `<div class="sub_services_data">
                    <div class="services_img_container"><img src=${img_url}></div>
                    <div class="sub_service_data">
                        <p>${retail[i].service_name}</p>
                    </div>
                    <input type="checkbox" class="services_ckeckbox" ${arr.includes(retail[i].id) ? 'checked' : ''} value=${retail[i].id} onclick="assign_images(${retail[i].id}, 'retail');">
                </div>
        <div class="horizontal-lines1"></div>`;
    }

    return retail_content

}

function append_amenity_images_side_bar(arr) {
    let amenities_content = "";
    for (let i = 0; i < amenities.length; i++) {
        var amenity_set_availability_object = {
            start: '',
            end: '',
            days: [],
        }
        assign_amenities_time_availability.push(amenity_set_availability_object)
        let img_url = amenities[i].image_path;
        if (i === 0) $(`#images_container3`).html('');
        if (arr.includes(amenities[i].id)) {
            $(`#images_container3`).append(`<div class="services_image"><img src=${amenities[i].image_path} ></div>`);
        }

        amenities_content += `<div class="sub_services_data">
        
        <div class="services_img_container"><img src=${img_url}></div>
        <div class="sub_service_data">
            <p>${amenities[i].service_name}</p>
            
        </div>
        
        <input type="checkbox" class="services_ckeckbox" ${arr.includes(amenities[i].id) ? 'checked' : ''} value=${amenities[i].id} onclick="assign_images(${amenities[i].id}, 'amenity');">
       </div><div class="horizontal-lines1"></div>`;
    }
    return amenities_content
}




function removeChargepointConfirmation(id, number) {

    document.getElementById('chargepoint_delete_modal_content').innerHTML = `
        <div class="heading">
            <h5>Remove chargepoint</h5>
            <button type="button" class="btn-close" onclick="assign_map_values(true);" data-bs-dismiss="modal" aria-label="Close"></button>

        </div>
        <div class="modal-body delete_chargepoint_confirmation_modal_body_styl" >
            <h6 > Are you sure you want to remove charge point ${number}</h6>
            <div class="google_maps_submit_buttons">
                <div class="google_maps_container_buttons">
                    <button class="cancle_button" data-bs-dismiss="modal">No</button>
                    <button onclick="removeChargepoint(${id},${number});"  class="done_button" >Yes</button>
                </div>
            </div>
        </div>
    `
    $('#delete_chargepoint_confirmation_model').modal('show');
}

//Commenting code for future reference

// function removeBackOfficeConfirmation(id, number) {

//     document.getElementById('backoffice_delete_modal_content').innerHTML = `
//         <div class="heading">
//             <h5>Remove Back Office</h5>
//             <button type="button" class="btn-close" onclick="assign_map_values(true);" data-bs-dismiss="modal" aria-label="Close"></button>

//         </div>
//         <div class="modal-body delete_chargepoint_confirmation_modal_body_styl" >
//             <h6 > Are you sure you want to remove back office ${number}</h6>
//             <div class="google_maps_submit_buttons">
//                 <div class="google_maps_container_buttons">
//                     <button class="cancle_button" data-bs-dismiss="modal">No</button>
//                     <button onclick="removeBackOffice(${id},${number});"  class="done_button" >Yes</button>
//                 </div>
//             </div>
//         </div>
//     `
//     $('#delete_backoffice_confirmation_model').modal('show');
// }





function removeChargepoint(id, number) {
    id.style.display = 'none';
    $('#delete_chargepoint_confirmation_model').modal('hide');
    document.getElementById('chargepoint_delete_modal_content').innerHTML = '';
    deleted_chargepoint_from_frontend.push(number - 1);
}
// function removeBackOffice(id, number) {
//     id.style.display = 'none';
//     $('#delete_backoffice_confirmation_model').modal('hide');
//     document.getElementById(`append_back_office_error`).innerHTML = '';
//     document.getElementById('backoffice_delete_modal_content').innerHTML = '';
//     deleted_backoffice_from_frontend.push(number - 1);
// }
function removeConnectorBox(conn_id, number, cp_number) {
    conn_id.style.display = 'none';
    $('#delete_chargepoint_confirmation_model').modal('hide');
    deleted_connectors_from_frontend[cp_number - 1].push(number - 1);
}
function removeConnectorConfirmation(conn_id, number, cp_number) {
    document.getElementById('chargepoint_delete_modal_content').innerHTML = `
        <div class="heading">
            <h5>Remove connector</h5>
                <button type="button" class="btn-close"  data-bs-dismiss="modal" aria-label="Close"></button>

        </div>
        <div class="modal-body delete_conn_confirmation_modal_body_styl" >
            <h6 > Are you sure you want to remove connector  ${number} from charge point ${cp_number}.</h6>
            
            <div class="google_maps_submit_buttons">
                <div class="google_maps_container_buttons">
                    <button class="cancle_button" data-bs-dismiss="modal">No</button>
                    <button onclick="removeConnectorBox(${conn_id},${number},${cp_number});" class="done_button" >Yes</button>
                </div>
            </div>
        </div>
        `
    $('#delete_chargepoint_confirmation_model').modal('show');
}




var coll = document.getElementsByClassName("set_availability");
var i;


for (i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function () {
        this.classList.toggle("active");
        var content = contents3[i];
        if (content.style.display === "block") {
            content.style.display = "none";
        } else {
            content.style.display = "block";
        }
    });
}

$('a').click(function (event) {
    event.preventDefault();
});

var expanded = [];

function showCheckboxes(n) {
    
        const checkboxes = document.getElementById(`checkbosx${n}`);
        
        if (expanded.includes(n)) {
            checkboxes.style.display = "none";
            var position = expanded.indexOf(n)
            expanded.pop(position)
        } else {
            expanded.forEach(element => {
                var checkbx = document.getElementById(`checkbosx${element}`);
                if (checkbx && (checkbx.style.display !== "none" || checkboxes.style.display === "block")) checkbx.style.display = "none";
            });
            expanded = []
            expanded.push(n)
            checkboxes.style.display = "block";
        }
    }
// }


function appendBackOfficeForm(clicked, backoffice_list) {
        
    var selected_backoffices = []
    for(var i=0;i<backoffice_list.length;i++){

        if(backoffice_list[i].back_office !== '' ){
            selected_backoffices.push(backoffice_list[i].back_office)
        }

    }
    selected_backoffices = selected_backoffices.map(backoffice => backoffice?.toUpperCase());

    available_back_offices_data = available_back_offices.filter(item => !selected_backoffices.includes(item));
    
    let optionsHTML = `<option value="">Select</option>`;
    available_back_offices_data.forEach(backoffice => {
        optionsHTML += `<option value="${backoffice}">${backoffice}</option>`;
    });


    // $("#backOfficeContainer").append(`
    //     <div class="charge_point_details station_back_office_details" id="backoffice_id__${clicked}">
    //         <div class="back_office_heading collapsible">
    //             <div class="chargepoint_heading_container">
    //                 <span>Back Office ${clicked}</span>
    //                 <div class="delete_bar deleted"
    //                     onclick="removeBackOfficeConfirmation('backoffice_id__${clicked}', ${clicked})"></div>
    //             </div>
    //         </div>
    //         <div class="content">
    //             <div class="back_office_form">
    //                 <div class="back_office_fields">
    //                     <label class="labels">Back Office Name</label>
    //                     <select name="backOffice" class="back_office_select_class" id="back_office_input_${clicked}"
    //                         onchange="updateUploadedDataBackOffice(${clicked - 1}, 0, this.value);">
    //                         ${optionsHTML}
    //                     </select>
    //                     <p class="error_field" id="backOfficeError${clicked - 1}0"></p>
    //                 </div>
    //                 <div class="back_office_fields">
    //                     <label class="labels">Location ID</label>
    //                     <input type="text"  id="location_input_${clicked}" class="inputs" placeholder="Enter Location Id"
    //                         onchange="updateUploadedDataBackOffice(${clicked - 1}, 1, this.value);">
    //                     <p class="error_field" id="backOfficeError${clicked - 1}1"></p>
    //                 </div>
    //             </div>
    //         </div>
    //     </div>
    // `);
}




$(document).on('click', function (event) {
    if (!$(event.target).closest('.checkbox_select_box').length) {
        const checkbox_elements = document.getElementsByClassName('checkboxes');
        for (var i of checkbox_elements) {
            i.style.display = "none";
        }
    }
});

//valeting core logic starts here
const dummy_terminal_object = {
    db_id: null,
    payter_serial_number: "",
    amenities: [],
    status: '',
    deleted: false,
}
let terminal_container_content = "";
let createValetingTerminal = (valeting_terminal, valeting_terminal_index) => {
    var create_valeting_amenities = "";
    var create_terminal_container_content = "";
    amenities.forEach((amenity) => {
        if (dataToUpload.amenities.includes(amenity.id)) {
            create_valeting_amenities += `<label>
                <input type="checkbox" value="${amenity.id}" ${valeting_terminal.amenities.includes(amenity.id) && `checked`}
                    class="amenities_list" name="type" onchange="updateValetingTerminals(this.value,${valeting_terminal_index},${1})"
                    />${amenity.service_name}
            </label>`
        }
    })
    create_terminal_container_content += `<div class="valeting_terminal_details" id="valeting_terminal_id_${valeting_terminal_index}">
                <div class="valeting_terminal_heading header-style">
                    <div class="valeting_terminal_heading_container">
                        <span>Terminal ${valeting_terminal_index + 1}</span>
                        <div class="delete_bar deleted"
                            onclick="removeValetingTerminalConfirmation(${valeting_terminal_index})">
                        </div>
                    </div>
                </div>
                <div class="content">
                    <div class="valeting_terminal_form">                                                                                                                                                                                              
                        <div class="valeting_terminal_fields">
                            <label class="labels">Payter Serial Number</label>
                            <input type="text" value="${valeting_terminal.payter_serial_number}" class="inputs" placeholder="Enter Payter Serial Number" onchange="updateValetingTerminals(this.value,${valeting_terminal_index},${0});"> 
                            <p class="error_field1" id="valeting_error${valeting_terminal_index}0"></p>
                        </div> 
                        <div class="input_container_inrow valeting_terminal_fields" id="region-data-container">
                            <label class="labels">Valeting Amenities</label>
                            <div class="station_select-box checkbox_select_box">
                                <div class="multiselect">
                                    <div class="selectBox" onclick="showCheckboxes(${valeting_terminal_index + 1})">
                                        <select class="select-field" name=""
                                            id="regions_region">
                                            <option id="regions-list${valeting_terminal_index}"></option>
                                        </select>
                                        <div class="overSelect"></div>
                                    </div>
                                    <div class="checkboxes" id="checkbosx${valeting_terminal_index + 1}">
                                        <div id="checkbosx6_loader"></div>
                                        <label>
                                            ${create_valeting_amenities}
                                        </label>
                                    </div>
                                </div>
                            </div>
                            <p class='error_field1' id="valeting_error${valeting_terminal_index}1"></p>
                        </div>
                        <div class="valeting_terminal_fields"> 
                            <label class="labels">Status</label>
                            <div class="station_select-box charge_point_field">
                                <select   class="dropdown_input small_dropdown_input" onchange="updateValetingTerminals(this.value,${valeting_terminal_index},${2});">
                                    <option ${valeting_terminal.status === "" && `selected`} value="">Select</option>
                                    <option ${valeting_terminal.status === "Active" && `selected`} value="Active">Active</option>
                                    <option ${valeting_terminal.status === "Inactive" && `selected`} value="Inactive">Inactive</option>
                                </select>
                            </div>
                            <p class="error_field1" id="valeting_error${valeting_terminal_index}2"></p>
                        </div>
                    </div>
                </div>
            </div>`
    return create_terminal_container_content
}
const selectedValetingAmenitiesHelper = () => {
    valeting_terminals.forEach((valeting_terminal, valeting_terminal_index) => {
        if (!valeting_terminal.deleted) {
            showSelectedValetingAmenities(valeting_terminal.amenities, valeting_terminal_index);
        }
    })
}
let show_valeting_terminals = () => {
    if (valeting_terminals.length === 0) {
        valeting_terminals.push({ ...dummy_terminal_object })
    }
    valeting_terminals.forEach((valeting_terminal, valeting_terminal_index) => {
        if (!valeting_terminal.deleted) {
            terminal_container_content += createValetingTerminal(valeting_terminal, valeting_terminal_index);
        }
        $('#valeting-terminals-container').html(terminal_container_content)
    })
    selectedValetingAmenitiesHelper();
}

const checkIfValeting = () => {
    if ($('#ValetingCheck').val() != "Yes") {
        $('#valeting_terminals_container').attr("style", "display:none");
        $('#valetingDetails').attr("style", "display:none");
        $('#valeting_machines_container').attr("style", "display:none");
        $('#valetingMachinesDetails').attr("style", "display:none");
        
    }
    else {
        $('#valetingDetails').attr("style", "display:block");
        $('#valeting_terminals_container').attr("style", "display:block");
        $('#valetingMachinesDetails').attr("style", "display:block");
        $('#valeting_machines_container').attr("style", "display:block");
        valeting_terminals.length === 0 || terminal_container_content === '' ?
            (show_valeting_terminals()) :
            $('#valeting-terminals-container').html(terminal_container_content)
        valeting_machines.length === 0 || machine_container_content === '' ?
            (show_valeting_machines()) :
            $('#valeting-machines-container').html(machine_container_content)
    }
}

const checkPaymentTerminal = () => {
    if ($('#payment-terminal-check').val() == "Worldline") {
        $('.rh-site-name-field').attr("style", "display:flex");
    } else {
        $('.rh-site-name-field').attr("style", "display:none");
    }
}

$('#add_valeting_terminal_button').on("click", () => {
    valeting_terminals.push({ ...dummy_terminal_object })
    terminal_container_content = '';
    show_valeting_terminals();
    // terminal_container_content += createValetingTerminal(dummy_terminal_object,valeting_terminals.length-1);
    // $('#valeting-terminals-container').html(terminal_container_content)
})

const removeValetingTerminalConfirmation = (id) => {
    document.getElementById('valeting_terminal_modal_content').innerHTML = `
        <div class="heading">
            <h5>Remove Valeting Terminal</h5>
            <button type="button" class="btn-close" onclick="assign_map_values(true);" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body delete_valeting_terminal_confirmation_modal_body_styl" >
            <h6 > Are you sure you want to remove <span>Terminal ${id + 1}</span> </h6>
            <div class="google_maps_submit_buttons">
                <div class="google_maps_container_buttons">
                    <button class="cancle_button" data-bs-dismiss="modal">No</button>
                    <button onclick="removeValetingTerminal(${id});"  class="done_button" >Yes</button>
                </div>
            </div>
        </div>
    `
    $('#delete_valeting_terminal_confirmation_model').modal('show');
}

const removeValetingTerminal = (id) => {
    $('#delete_valeting_terminal_confirmation_model').modal('hide');
    valeting_terminals[id].deleted = true;
    terminal_container_content = ""
    show_valeting_terminals();
}

const showSelectedValetingAmenities = (selectedAmenities, valeting_terminal_index) => {
    var selectedAmenitiesString = ""
    if (!selectedAmenities.length) {
        document.getElementById(`regions-list${valeting_terminal_index}`).innerHTML = 'Select'
    }
    else {
        amenities.forEach((amenity) => {
            if (selectedAmenities.includes(amenity.id)) {
                selectedAmenitiesString += `${amenity.service_name},`
            }
        })
        document.getElementById(`regions-list${valeting_terminal_index}`).innerHTML = selectedAmenitiesString.substring(0, selectedAmenitiesString.length - 1)
    }
}

const updateValetingTerminals = (value, valeting_terminal_index, field_identifier) => {
    if (field_identifier === 1) {
        terminal_amenities = [...valeting_terminals[valeting_terminal_index].amenities]
        terminal_amenities.includes(Number(value)) ? terminal_amenities.splice(terminal_amenities.indexOf(Number(value)), 1) : terminal_amenities.push(Number(value));
        valeting_terminals[valeting_terminal_index].amenities = terminal_amenities;
        valeting_terminals[valeting_terminal_index].amenities.length === 0 ?
            $(`#valeting_error${valeting_terminal_index}1`).html("Please select atleast one amenity") :
            $(`#valeting_error${valeting_terminal_index}1`).html("")
        showSelectedValetingAmenities(terminal_amenities, valeting_terminal_index);
    }
    else if (field_identifier === 0) {
        if (value === '') {
            $(`#valeting_error${valeting_terminal_index}0`).html("This field is required");
        }
        else if (value.length > 20) {
            $(`#valeting_error${valeting_terminal_index}0`).html("Can't be more than 20 characters");
        }
        else {
            $(`#valeting_error${valeting_terminal_index}0`).html("");
        }
        valeting_terminals[valeting_terminal_index].payter_serial_number = value;
    }
    else {
        value === '' ?
            $(`#valeting_error${valeting_terminal_index}2`).html("This field is required") :
            $(`#valeting_error${valeting_terminal_index}2`).html("");
        valeting_terminals[valeting_terminal_index].status = value;
    }
}

const removeAmenityFromValetingAmenities = () => {
    valeting_terminals_copy = [...valeting_terminals]
    valeting_terminals.forEach((terminal) => {
        terminal.amenities = terminal.amenities.filter((amenity) => {
            return dataToUpload.amenities.includes(amenity)
        })
    })
    selectedValetingAmenitiesHelper()
}

// Valeting Machines core logic starts here
const dummy_machine_object = {
    db_id: null,
    machine_id: "",
    machine_name: "",
    machine_number: "",
    is_active: true,
    deleted: false
}

let machine_container_content = "";
let createValetingMachine = (valeting_machine, valeting_machine_index) => {
    var create_machine_container_content = "";
    
    create_machine_container_content += `<div class="valeting_machine_details" id="valeting_machine_id_${valeting_machine_index}">
        <div class="valeting_machine_heading header-style">
            <div class="valeting_machine_heading_container">
                <span>Machine ${valeting_machine_index + 1}</span>
                <div class="delete_bar deleted"
                    onclick="removeValetingMachineConfirmation(${valeting_machine_index})">
                </div>
            </div>
        </div>
        <div class="content">
            <div class="valeting_machine_form">                                                                                                                                                                                              
                <div class="valeting_machine_fields">
                    <label class="labels">Machine ID</label>
                    <input type="number" value="${valeting_machine.machine_id}" class="inputs" placeholder="Enter Machine ID" 
                        onchange="updateValetingMachines(this.value,${valeting_machine_index},${0});"> 
                    <p class="error_field1" id="valeting_machine_error${valeting_machine_index}0"></p>
                </div>
                <div class="valeting_machine_fields">
                    <label class="labels">Machine Name</label>
                    <input type="text" value="${valeting_machine.machine_name}" class="inputs" placeholder="Enter Machine Name" 
                        onchange="updateValetingMachines(this.value,${valeting_machine_index},${1});">
                    <p class="error_field1" id="valeting_machine_error${valeting_machine_index}1"></p>
                </div>
                <div class="valeting_machine_fields">
                    <label class="labels">Machine Number</label>
                    <input type="text" value="${valeting_machine.machine_number || ''}" class="inputs" placeholder="Enter Machine Number" 
                        onchange="updateValetingMachines(this.value,${valeting_machine_index},${2});">
                    <p class="error_field1" id="valeting_machine_error${valeting_machine_index}2"></p>
                </div>
                <div class="valeting_machine_fields"> 
                    <label class="labels">Status</label>
                    <div class="station_select-box charge_point_field">
                        <select class="dropdown_input small_dropdown_input" 
                            onchange="updateValetingMachines(this.value,${valeting_machine_index},${3});">
                            <option ${valeting_machine.status === "Active" ? 'selected' : ''} value="Active">Active</option>
                            <option ${valeting_machine.status === "Inactive" ? 'selected' : ''} value="Inactive">Inactive</option>
                        </select>
                    </div>
                    <p class="error_field1" id="valeting_machine_error${valeting_machine_index}3"></p>
                </div>
            </div>
        </div>
    </div>`;
    
    return create_machine_container_content;
}

let show_valeting_machines = () => {
    if (valeting_machines.length === 0) {
        valeting_machines.push({ ...dummy_machine_object });
    }
    
    machine_container_content = "";
    valeting_machines.forEach((valeting_machine, valeting_machine_index) => {
        if (!valeting_machine.deleted) {
            machine_container_content += createValetingMachine(valeting_machine, valeting_machine_index);
        }
    });
    
    $('#valeting-machines-container').html(machine_container_content);
}

// Check if valeting is enabled (similar to terminals but for machines)
const checkIfValetingMachines = () => {
    if ($('#ValetingCheck').val() != "Yes") {
        $('#valeting_machines_container').hide();
    } else {
        $('#valeting_machines_container').show();
        valeting_machines.length === 0 || machine_container_content === '' ?
            show_valeting_machines() :
            $('#valeting-machines-container').html(machine_container_content);
    }
}

// Add new machine button handler
$('#add_valeting_machine_button').on("click", () => {
    valeting_machines.push({ ...dummy_machine_object });
    machine_container_content = '';
    show_valeting_machines();
});

// Remove machine confirmation modal
const removeValetingMachineConfirmation = (id) => {
    document.getElementById('valeting_machine_modal_content').innerHTML = `
        <div class="heading">
            <h5>Remove Valeting Machine</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body delete_valeting_machine_confirmation_modal_body_styl">
            <h6>Are you sure you want to remove <span>Machine ${id + 1}</span></h6>
            <div class="google_maps_submit_buttons">
                <div class="google_maps_container_buttons">
                    <button class="cancle_button" data-bs-dismiss="modal">No</button>
                    <button onclick="removeValetingMachine(${id});" class="done_button">Yes</button>
                </div>
            </div>
        </div>
    `;
    $('#delete_valeting_machine_confirmation_model').modal('show');
}

// Actual removal function
const removeValetingMachine = (id) => {
    $('#delete_valeting_machine_confirmation_model').modal('hide');
    valeting_machines[id].deleted = true;
    if(valeting_machines[id].machine_id === "") {
        valeting_machines.splice(id, 1);
    }
    machine_container_content = "";
    show_valeting_machines();
}

// Update machine data handler
const updateValetingMachines = (value, valeting_machine_index, field_identifier) => {
    switch(field_identifier) {
        case 0: // Machine ID
            if (!value) {
                $(`#valeting_machine_error${valeting_machine_index}0`).html("Machine ID is required");
            } else {
                $(`#valeting_machine_error${valeting_machine_index}0`).html("");
            }
            valeting_machines[valeting_machine_index].machine_id = parseInt(value);
            break;
            
        case 1: // Machine Name
            if (!value) {
                $(`#valeting_machine_error${valeting_machine_index}1`).html("Machine Name is required");
            } else {
                $(`#valeting_machine_error${valeting_machine_index}1`).html("");
            }
            valeting_machines[valeting_machine_index].machine_name = value;
            break;
            
        case 2: // Machine Number (optional)
            valeting_machines[valeting_machine_index].machine_number = value;
            break;
            
        case 3: // Status
            valeting_machines[valeting_machine_index].status = value;
            valeting_machines[valeting_machine_index].is_active = (value === "Active");
            break;
    }
}

// Initialize on page load
$(document).ready(function() {
    if ($('#ValetingCheck').val() === "Yes") {
        show_valeting_machines();
    }
});