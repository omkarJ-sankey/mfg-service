// variables for timing selection
var mon_fri = 'Mon-Fri';
var sat = 'Sat';
var sun ='Sun';
var prev_mon_fri = null;
var prev_sat = null;
var prev_sun = null;
function updateUploadedDataSetWorkingHours(n, m, val){
    const working_hours_spans = document.getElementsByClassName('working_hours_span')
    const upload_keys = Object.keys(dataToUpload.working_hours);
    const timing_var = upload_keys[n]
    if (m===0){
        const checking_past_value = dataToUpload.working_hours[timing_var].full_hours
        dataToUpload.working_hours[timing_var].full_hours = !checking_past_value
    }else if (m===1){
        dataToUpload.working_hours[timing_var].start_time = val
        dataToUpload.working_hours[timing_var].full_hours = false
    }else{
        
        dataToUpload.working_hours[timing_var].end_time = val
        dataToUpload.working_hours[timing_var].full_hours = false
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

var chargepoints
var station_json
var working_hours_json
({chargepoints,station_json , working_hours_json} = services_data1)
dataToUpload.station_id = station_json[0].station_id
dataToUpload.station_name = station_json[0].station_name
dataToUpload.address_line1 = station_json[0].station_address1
dataToUpload.address_line2 = station_json[0].station_address2
dataToUpload.address_line3 = station_json[0].station_address3
dataToUpload.town = station_json[0].town
dataToUpload.postal_code = station_json[0].post_code
dataToUpload.country = station_json[0].country
dataToUpload.brand = station_json[0].brand
dataToUpload.owner = station_json[0].owner
dataToUpload.email = station_json[0].email
dataToUpload.phone = station_json[0].phone
dataToUpload.status = station_json[0].status
dataToUpload.latitude = station_json[0].latitude
dataToUpload.longitude = station_json[0].longitude
dataToUpload.station_type = station_json[0].station_type
dataToUpload.site_id = station_json[0].site_id
dataToUpload.payment_terminal= station_json[0].payment_terminal || 'None'
dataToUpload.valeting= station_json[0].valeting || 'No'
dataToUpload.rh_site_name= station_json[0].receipt_hero_site_name || ''
dataToUpload.overstay_fee = station_json[0].overstay_fee || 0;
dataToUpload.valeting_site_id = station_json[0].valeting_site_id || '';
dataToUpload.ampeco_site_id = station_json[0].ampeco_site_id || '';
dataToUpload.ampeco_site_title = station_json[0].ampeco_site_title || '';



if( station_json[0].station_type === 'MFG EV' || station_json[0].station_type === 'MFG Forecourt'  || station_json[0].station_type === 'MFG EV plus Forecourt'){
    dataToUpload.station_type_is_mfg =true;
    dataToUpload.stationTypeSiteData.site_title = station_json[0].site_title;
    dataToUpload.stationTypeSiteData.operation_region = station_json[0].operation_region;
    dataToUpload.stationTypeSiteData.region = station_json[0].region;
    dataToUpload.stationTypeSiteData.regional_manager = station_json[0].regional_manager;
    dataToUpload.stationTypeSiteData.area = station_json[0].area;
    dataToUpload.stationTypeSiteData.area_regional_manager = station_json[0].area_regional_manager;

}

var selection_on_start  = document.getElementsByClassName("selectt");
if (working_hours_json[0].monday_friday !== "Closed"){
    if (working_hours_json[0].monday_friday === "24 hours") {
        
        timingSelection(0)
        updateUploadedDataSetWorkingHours(0,0 , '24 hours')
        dataToUpload.working_hours.monday_friday.full_hours = true
    }else{
        updateUploadedDataSetWorkingHours(0, 1, working_hours_json[0].monday_friday.slice(0,5));
        updateUploadedDataSetWorkingHours(0, 2, working_hours_json[0].monday_friday.slice(6,11));
        dataToUpload.working_hours.monday_friday.full_hours = false;
        dataToUpload.working_hours.monday_friday.start_time = working_hours_json[0].monday_friday.slice(0,5);
        dataToUpload.working_hours.monday_friday.end_time = working_hours_json[0].monday_friday.slice(6,11);
        selection_on_start[0].value = working_hours_json[0].monday_friday.slice(0,5);
        selection_on_start[1].value = working_hours_json[0].monday_friday.slice(6,11);
    }
}
if (working_hours_json[0].saturday !== "Closed") {
    if (working_hours_json[0].saturday === "24 hours") {
        
        timingSelection(1)
        updateUploadedDataSetWorkingHours(1,0 , '24 hours')
        dataToUpload.working_hours.saturday.full_hours = true
    }else{
        
        updateUploadedDataSetWorkingHours(1, 1, working_hours_json[0].saturday.slice(0,5))
        updateUploadedDataSetWorkingHours(1, 2, working_hours_json[0].saturday.slice(6,11))
        dataToUpload.working_hours.saturday.full_hours = false
        dataToUpload.working_hours.saturday.start_time = working_hours_json[0].saturday.slice(0,5)
        dataToUpload.working_hours.saturday.end_time = working_hours_json[0].saturday.slice(6,11)
        selection_on_start[2].value = working_hours_json[0].saturday.slice(0,5)
        selection_on_start[3].value = working_hours_json[0].saturday.slice(6,11)
    }
}
if (working_hours_json[0].sunday !== "Closed") {
    if (working_hours_json[0].sunday === "24 hours") {
        timingSelection(2)
        updateUploadedDataSetWorkingHours(2,0 , '24 hours')
        dataToUpload.working_hours.sunday.full_hours = true
    }else{
        
        updateUploadedDataSetWorkingHours(2, 1, working_hours_json[0].sunday.slice(0,5))
        updateUploadedDataSetWorkingHours(2, 2, working_hours_json[0].sunday.slice(6,11))
        dataToUpload.working_hours.sunday.full_hours = false
        dataToUpload.working_hours.sunday.start_time = working_hours_json[0].sunday.slice(0,5)
        dataToUpload.working_hours.sunday.end_time = working_hours_json[0].sunday.slice(6,11)
        selection_on_start[4].value = working_hours_json[0].sunday.slice(0,5)
        selection_on_start[5].value = working_hours_json[0].sunday.slice(6,11)

    }
}

function getConnectorCurrentStatus(status){
    let currentStatus;
    switch(status) {
        case "Available":
            currentStatus = "available_indicator_color";
            break;
        case "Charging":
            currentStatus = "charging_indicator_color";
            break;
        case "Preparing":
            currentStatus = "charging_indicator_color";
            break;
        case "Finishing":
            currentStatus = "charging_indicator_color";
            break;
        case "Out of service":
            currentStatus = "unknown_indicator_color";
            break;
        case "Faulted":
            currentStatus = "unknown_indicator_color";
            break;
        case "Unavailable":
            currentStatus = "unknown_indicator_color";
            break;
        case "Reserved":
            currentStatus = "reserved_indicator_color";
            break;
        case "New":
            currentStatus = "new_indicator_color";
            break;
        default:
            currentStatus = "not_available_indicator_color";
    }
    return currentStatus;
}

let status_list = ['Active','Inactive']
let tariff_currency_list =['GBP(£)','Euro(€)']
let speed_list = ['Ultra Rapid','Rapid']

$(document).ready(function(){
        let data_to_render_first = ''
        // let  countBackOffice =1;
        let ocpi_back_office_html= ''
        for (var i=0;i<available_back_offices.length;i++){
            ocpi_back_office_html+= `<option value="${backoffice_keys[i]}">${backoffice_keys[i]}</option>`
        }
        for(var c=0; c<chargepoints.length; c++){
            cp = chargepoints[c];
            deleted_connectors_from_frontend.push([]);
            connector_count_manager.push(cp[1].length);
            let object_to_push = {}
            object_to_push = {
                cp_on_updation : true,
                cp_id: cp[0].id,
                charge_point_id:cp[0].charger_point_id ,
                charge_point_name: cp[0].charger_point_name,
                status: cp[0].charger_point_status,
                // back_office: cp[0].back_office,
                device_id: cp[0].device_id? cp[0].device_id : '' ,
                payter_terminal_id: cp[0].payter_terminal_id? cp[0].payter_terminal_id : '' ,
                ampeco_charge_point_id: cp[0].ampeco_charge_point_id ? cp[0].ampeco_charge_point_id : '',
                ampeco_charge_point_name: cp[0].ampeco_charge_point_name ? cp[0].ampeco_charge_point_name : '',
                worldline_terminal_id: cp[0].worldline_terminal_id? cp[0].worldline_terminal_id : '' ,
                connectors : [],
                deleted: false,   
            }
            let data_conn_first =''
            for(var con = 0; con< cp[1].length; con ++){
                connect = cp[1]
                let object_to_push1 = {}
                object_to_push1 = {
                    con_on_updation : true,
                    con_id: connect[con].id,
                    connector_type: connect[con].connector_type,
                    connector_id: connect[con].connector_id,
                    connector_name: connect[con].connector_name,
                    status: connect[con].status,
                    plug_type_name: connect[con].plug_type_name,
                    maximum_charge_rate: connect[con].max_charge_rate,
                    tariff_amount: connect[con].tariff_amount,
                    tariff_currency: connect[con].tariff_currency,
                    connector_sorting_order: connect[con].connector_sorting_order,
                    // back_office: connect[con].back_office,
                    evse_uid: connect[con].station_connectors__evse_id__uid,
                    ocpi_connector_id: connect[con].station_connectors__connector_id,
                    deleted: false,
                }
                object_to_push.connectors.push(object_to_push1)
                let connector_current_status=getConnectorCurrentStatus(connect[con].current_status);
                let connector_status_html= ''
                for (var j=0;j<status_list.length;j++){
                    if(status_list[j] === connect[con].status){
                        connector_status_html += `<option selected value="${status_list[j]}">${status_list[j]}</option>`
                    }
                    else{
                        connector_status_html += `<option value="${status_list[j]}">${status_list[j]}</option>`
                    }
                }

                let tariff_currency_html = ''
                for (var i=0;i<tariff_currency_list.length;i++){
                    if(tariff_currency_list[i] === connect[con].tariff_currency){

                        tariff_currency_html += `<option selected value="${tariff_currency_list[i]}">${tariff_currency_list[i]}</option>`
                    }
                    else{

                        tariff_currency_html += `<option value="${tariff_currency_list[i]}">${tariff_currency_list[i]}</option>`
                    }
                }
                let connector_type_speed_html = ''
                for (var i=0;i<connector_speed_types_list.length;i++){
                    if(connector_speed_types_list[i][0] === connect[con].connector_type){

                        connector_type_speed_html+= `<option selected value="${connector_speed_types_list[i][0]}">${connector_speed_types_list[i][1]}</option>`
                    }
                    else{

                        connector_type_speed_html+= `<option value="${connector_speed_types_list[i][0]}">${connector_speed_types_list[i][1]}</option>`
                    }
                }
                let conector_type_html = ''
                for (var i=0;i<connector_type_list.length;i++){
                    if(connector_type_list[i] === connect[con].plug_type_name){

                        conector_type_html+= `<option selected value="${connector_type_list[i]}">${connector_type_list[i]}</option>`
                    }
                    else{

                        conector_type_html+= `<option value="${connector_type_list[i]}">${connector_type_list[i]}</option>`
                    }
                }
                let conector_back_office = ''
                for (var i=0;i<available_back_offices.length;i++){
                    if(available_back_offices[i]?.toUpperCase() === connect[con].back_office?.toUpperCase()){
                        conector_back_office+= `<option selected value="${available_back_offices[i]}">${available_back_offices[i]}</option>`
                    }
                    else{
                        conector_back_office+= `<option value="${available_back_offices[i]}">${available_back_offices[i]}</option>`
                    }
                }

                data_conn_first += `
                <div class="connectors_box" id="connector_delete_id_${c+1}_${con+1}">
                        <div class="connector_heading collapsible1">
                            <div class="connector_heading_container">
                                <div class="connector_current_status_box">
                                    <span>Connector ${con+1}</span>
                                    <span class="connector_status_separator"></span>
                                    <div class="connector_current_status_indicator ${connector_current_status}">
                                        ${connect[con].current_status}
                                    </div>
                                </div>
                                <div class="delete_bar"
                                    onclick="removeConnectorConfirmation('connector_delete_id_${c+1}_${con+1}',
                                    ${con+1},${c+1},${connect[con].id})"
                                 ></div>
                            </div>
                            
                        </div>
                        <div class="content">
                            <div class="charge_point_form">                                                                                                                                                                                              
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector Type</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${c},${con},${0},this.value,${100}, ${true});">
                                            <option value="">Select</option>
                                            ${connector_type_speed_html}
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${c}${con}0"></p>
                                </div>
                                    <div class="charge_point_fields">
                                    
                                    <label    class="labels">Connector ID</label>
                                    <input type="number"  value="${connect[con].connector_id}"  class="inputs" placeholder="Enter connector ID" onchange="updateUploadedDataConnector(${c},${con}, ${1}, this.value,${100} , ${true});"> 
                                    
                                    <p class="error_field" id="chargepointerror${c}${con}1"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector Name</label>
                                    <input type="text" value="${connect[con].connector_name}"   class="inputs" placeholder="Enter connector name" onchange="updateUploadedDataConnector(${c},${con}, ${2}, this.value,${100} , ${true});"> 
                                    
                                    <p class="error_field" id="chargepointerror${c}${con}2"></p>
                                </div>
            
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Status</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${c},${con },${3},this.value,${100}, ${true});">
                                            <option value="">Select</option>
                                            ${connector_status_html}
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${c}${con}3"></p>
                                </div>
            
                            </div>
                            <div class="charge_point_form">                                                                                                                                                                                              
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Plug Type Name</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${c},${con},${4},this.value,${100}, ${true});">
                                            <option value="">Select</option>
                                            ${conector_type_html}
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${c}${con}4"></p>
                                </div>                                                                                                                                                                                              
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Maximum Charge Rate</label>
                                    <input type="number" value="${connect[con].max_charge_rate}"   class="inputs" placeholder="Enter charge rate" onchange="updateUploadedDataConnector(${c},${con},${5},this.value,${0}, ${true});"> 
                                    
                                    <p class="error_field" id="chargepointerror${c}${con}5"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Tariff Amount</label>
                                    <input type="number" min="0" value="${connect[con].tariff_amount}"  class="inputs" placeholder="Enter tariff amount" onchange="updateUploadedDataConnector(${c},${con },${6},this.value,${100}, ${true});"> 
                                    
                                    <p class="error_field" id="chargepointerror${c}${con}6"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Tariff Currency</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${c},${con },${7},this.value,${100}, ${true});">
                                            <option value="">Select</option>
                                            ${tariff_currency_html}
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${c}${con}7"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector Sort Order</label>
                                    <input type="number" min="0" value="${connect[con].connector_sorting_order}"  class="inputs" placeholder="Enter sort order" onchange="updateUploadedDataConnector(${c},${con },${8},this.value,${100}, ${true});"> 
                                    
                                    <p class="error_field" id="chargepointerror${c}${con}8"></p>
                                </div>
                                
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Evse UID</label>
                                    <input type="text"  value = "${connect[con].station_connectors__evse_id__uid  !== null ? connect[con].station_connectors__evse_id__uid : ''}"  class="inputs" placeholder="Enter ocpi evse uid" onchange="updateUploadedDataConnector(${c},${con},${9},this.value,${100}, ${true});"> 
                                    
                                    <p class="error_field" id="chargepointerror${c}${con}9"></p>
                                </div>

                                <div class="charge_point_fields">
                                
                                    <label    class="labels">OCPI Connector ID</label>
                                    <input type="text"  value = "${connect[con].station_connectors__connector_id  !== null ? connect[con].station_connectors__connector_id : ''}"  class="inputs" placeholder="Enter ocpi connector id" onchange="updateUploadedDataConnector(${c},${con},${10},this.value,${100}, ${true});"> 
                                    
                                    <p class="error_field" id="chargepointerror${c}${con}10"></p>
                                </div>
            
            
                            </div>
                        </div>
                    </div>
            `
            }
            let chargepoint_status_html= ''
            for (var i=0;i<status_list.length;i++){
                if(status_list[i] === cp[0].charger_point_status){

                    chargepoint_status_html+= `<option selected value="${status_list[i]}">${status_list[i]}</option>`
                }
                else{

                    chargepoint_status_html+= `<option value="${status_list[i]}">${status_list[i]}</option>`
                }
            }
            let back_office_name_list=['SWARCO','DRIIVZ']
            
            let back_office_html= ''
            for (var i=0;i<back_office_name_list.length;i++){
                if(back_office_name_list[i] === cp[0].back_office){

                    back_office_html+= `<option selected value="${back_office_name_list[i]}">${back_office_name_list[i]}</option>`
                }
                else{

                    back_office_html+= `<option value="${back_office_name_list[i]}">${back_office_name_list[i]}</option>`
                }
            }

            data_to_render_first += `
            <div class="charge_point_details" id="chargepoint_id__${c+1}"
            >

                <div class="charge_point_heading collapsible">
                    <div class="chargepoint_heading_container">
                        <span>Charge Point ${c+1}</span>
                        <div class="delete_bar deleted"
                            onclick="removeChargepointConfirmation('chargepoint_id__${c+1}', ${c+1},${cp[0].id})"></div>
                    </div>
                </div>
                <div class="content">
                    <div class="charge_point_form">                                                                                                                                                                                              
                        <div class="charge_point_fields">
                        
                            <label    class="labels">Charge Point ID</label>
                            <input type="text"   value="${cp[0].charger_point_id}" class="inputs" placeholder="Enter charge point id" onchange="updateUploadedDataChargePoint(${c+1},${0},this.value, ${true});"> 
                            
                            <p class="error_field" id="chargepointerror${c}0"></p>
                        </div>                                                                                                                                                                                              
                        <div class="charge_point_fields">
                        
                            <label    class="labels">Charge Point Name</label>
                            <input type="text"  value="${cp[0].charger_point_name}"  class="inputs" placeholder="Enter charge point name" onchange="updateUploadedDataChargePoint(${c+1},${1},this.value, ${true});"> 
                            
                            <p class="error_field" id="chargepointerror${c}1"></p>
                        </div>

                        <div class="charge_point_fields">
                        
                            <label    class="labels">Status</label>
                            <div class="station_select-box charge_point_field">
                                <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataChargePoint(${c+1},${2},this.value, ${true});">
                                    <option value="">Select</option>
                                    ${chargepoint_status_html}
                                </select>
                            </div>
                            <p class="error_field" id="chargepointerror${c}2"></p>
                        </div>
                        
                                                                                                                                                                                                                
                        <div class="charge_point_fields">
                        
                            <label    class="labels">Device id</label>
                            <input type="number"   value="${cp[0].device_id}" class="inputs" placeholder="Enter device id" onchange="updateUploadedDataChargePoint(${c+1},${3},this.value,${true});"> 
                            
                            <p class="error_field" id="chargepointerror${c}3"></p>
                        </div>                                                                                                                                                                                    
                        <div class="charge_point_fields">
                        
                            <label    class="labels">Payter terminal id</label>
                            <input type="text"   value="${cp[0].payter_terminal_id?cp[0].payter_terminal_id:''}" class="inputs" placeholder="Enter terminal id" onchange="updateUploadedDataChargePoint(${c+1},${4},this.value,${true});"> 
                            
                            <p class="error_field" id="chargepointerror${c}4"></p>
                        </div>

                        <div class="charge_point_fields">
                            <label    class="labels">Worldline Terminal ID</label>
                            <input type="text"   value="${cp[0].worldline_terminal_id?cp[0].worldline_terminal_id:''}" class="inputs" placeholder="Enter terminal id" onchange="updateUploadedDataChargePoint(${c+1},${7},this.value,${true});"> 
                            <p class="error_field" id="chargepointerror${c}7"></p>
                        </div>

                        <div class="charge_point_fields">
                            <label class="labels">Ampeco Charge Point ID</label>
                            <input type="text" value="${cp[0].ampeco_charge_point_id ? cp[0].ampeco_charge_point_id : ''}" class="inputs" placeholder="Enter Ampeco Charge Point ID" onchange="updateUploadedDataChargePoint(${c+1},${5},this.value,${true});">
                            <p class="error_field" id="chargepointerror${c}5"></p>
                        </div>

                        <div class="charge_point_fields">
                            <label class="labels">Ampeco Charge Point Name</label>
                            <input type="text" value="${cp[0].ampeco_charge_point_name ? cp[0].ampeco_charge_point_name : ''}" class="inputs" placeholder="Enter Ampeco Charge Point Name" onchange="updateUploadedDataChargePoint(${c+1},${6},this.value,${true});">
                            <p class="error_field" id="chargepointerror${c}6"></p>
                        </div>
                    </div>

                    <!-- connector fields -->
                    <div id="ConnectorContainer${c +1 }">
                        ${data_conn_first}
                        
                    </div>
                        
                    <div class="charge_point_button_container1">
                        
                        <button class="add_charge_point" onclick="appendConnectorForm(${c +1});">
                            <img src=${plus_sign_icn_url} class="add_image"></button>

                    </div>
                </div>


                </div>
            
            `
            dataToUpload.chargepoints.push(object_to_push)
        }
        $("#chargingPointContainer").append(data_to_render_first)

  let countClicked1 = chargepoints.length
  $("#addChargePointButton").click(function(){
    var chargePointDataToUpload = {
        charge_point_id: '',
        charge_point_name: '',
        status: '',
        // back_office:'',
        device_id :'',
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
            deleted: false,
        }],
        cp_id: null,
        deleted: false,
    }
    countClicked1 = countClicked1 + 1;
      connector_count_manager.push(1)
      appendChargePointForm(countClicked1)
      dataToUpload.chargepoints.push(chargePointDataToUpload)
    //   updateChargePointBackOfficeDropdowns();
  });

  
        
    let ocpi_back_office_list = backoffice_list ? Object.keys(backoffice_list) : [];

    function renderBackOfficeHTML(index, backOfficeValue = '', locationIdValue = '') {
        let back_office_data_html = '';
        for (let i = 0; i < total_back_offices.length; i++) {
            if (total_back_offices[i]?.toUpperCase() === backOfficeValue?.toUpperCase()) {
                back_office_data_html += `<option selected value="${total_back_offices[i]}">${total_back_offices[i]}</option>`;
            } else {
                back_office_data_html += `<option value="${total_back_offices[i]}">${total_back_offices[i]}</option>`;
            }
        }

        return `
                <div class="charge_point_details station_back_office_details" id="backoffice_id__${index + 1}">
                    <div class="back_office_heading collapsible">
                        <div class="backoffice_heading_container">
                            <span>Back Office</span>
                        </div>
                    </div>
                    <div class="content">
                        <div class="back_office_form">
                            <div class="back_office_fields">
                                <label class="labels">Back Office Name</label>
                                <select name="backOffice" id="backoffice_name_input" class="back_office_select_class"
                                    onchange="updateUploadedDataBackOffice(${index}, 0, this.value);">
                                    <option value="">Select</option>
                                    ${back_office_data_html}
                                </select>
                                <p class="error_field" id="backOfficeError${index}0"></p>
                            </div>
                            <div class="back_office_fields">
                                <label class="labels">Location ID</label>
                                <input type="text" id="backoffice_location_id_input" class="inputs" placeholder="Enter Location Id"
                                    value="${locationIdValue}" onchange="updateUploadedDataBackOffice(${index}, 1, this.value);">
                                <p class="error_field" id="backOfficeError${index}1"></p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
    }

    if (ocpi_back_office_list.length === 0) {
        $("#backOfficeContainer").append(renderBackOfficeHTML(0));
        dataToUpload.backoffice.push({
            back_office: "",
            location_id: "",
            deleted: false
        });
    } else {
        ocpi_back_office_list.forEach((key, index) => {
            const locationId = backoffice_list[key];
            $("#backOfficeContainer").append(renderBackOfficeHTML(index, key, locationId));

            dataToUpload.backoffice.push({
                back_office: key,
                location_id: locationId,
                deleted: false
            });
        });
    }

//   $("#backOfficeContainer").html(office_to_render_first)


    let back_office_count = ocpi_back_office_list.length


//   $("#addBackOfficeButton").click(function(){
//     var backOfficeDataToUpload = {
//         back_office:'',
//         location_id:'',
//         deleted:false
//     }
//       back_office_count = back_office_count + 1;
//     //   connector_count_manager.push(1)
//     
//       let len = 0
    
//       len = dataToUpload.backoffice.length - deleted_backoffice_from_frontend.length

//     if ((total_back_offices.length > len) ){
//         countBackOffice++;
//         appendBackOfficeForm(countBackOffice, dataToUpload.backoffice)
//         dataToUpload.backoffice.push(backOfficeDataToUpload)
//         // updateChargePointBackOfficeDropdowns();    
//     }
//     else{
//         document.getElementById(`append_back_office_error`).innerHTML = "More back offices are not available";
//     }

//   });

  
});

let connector_type_speed_html_new = ''
for (var i=0;i<connector_speed_types_list.length;i++){

    connector_type_speed_html_new+= `<option value="${connector_speed_types_list[i][0]}">${connector_speed_types_list[i][1]}</option>`
    
}



function validateBackOffice(index) {
    let valid = true;
    const name = dataToUpload.backoffice[index]?.back_office || false;
    const location_id = dataToUpload.backoffice[index]?.location_id || false;
    if (name === false && name ==='') {
        $(`#backOfficeError${index}0`).html("Back Office Name is required");
        // dataToUpload.backoffice[index].name = prev_bo
        valid = false;
    } else {
        $(`#backOfficeError${index}0`).html("");
    }
    if (location_id=== false && location_id ==='') {
        // dataToUpload.backoffice[index].location_id = prev_loc
        $(`#backOfficeError${index}1`).html("Location ID is required");
        valid = false;
    } else {
        $(`#backOfficeError${index}1`).html("");
    }
    // if(valid){
    //     dataToUpload.backoffice[index].name = 
    // }

    return valid;
}


let backOfficeCount = 0;

// Update Back Office Data
function updateUploadedDataBackOffice(index, field, value) {
    
    // prev_bo = dataToUpload.backoffice[index]?.name || false;
    // prev_loc = dataToUpload.backoffice[index]?.location_id || false;
    is_valid = validateBackOffice(index);
    if(is_valid){
    if (!dataToUpload.backoffice[index]) {
        dataToUpload.backoffice[index] = { back_office: '', location_id: '' };
    }
    if (field === 0) {
        dataToUpload.backoffice[index].back_office = value;
    } else if (field === 1) {
        dataToUpload.backoffice[index].location_id = value;
    }

    }
    getSelectedBackOffices();
}

// Remove Back Office
// function removeBackOffice(id, number) {
//     document.getElementById(id).style.display = 'none';
//     $('#delete_backoffice_confirmation_model').modal('hide');
//     document.getElementById(`append_back_office_error`).innerHTML = '';
//     deleted_backoffice_from_frontend.push(number - 1);
//     // dataToUpload.backoffice[number - 1] = null;
//     // deleted_backoffice_from_frontend.push(number - 1);
// }

// let backOfficeCount = 0;
// $('#addBackOfficeButton').on('click', function () {
//     backOfficeCount += 1;
//     
//     appendBackOfficeForm(backOfficeCount, backoffice_list);

//     dataToUpload.backoffice.push({ name: '', location_id: '' });
//     updateChargePointBackOfficeDropdowns();
// });



// function removeBackOfficeConfirmation(id, number) {
//     document.getElementById('backoffice_delete_modal_content').innerHTML = `
//         <div class="heading">
//             <h5>Remove Back Office</h5>
//             <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
//         </div>
//         <div class="modal-body delete_chargepoint_confirmation_modal_body_styl" >
//             <h6 > Are you sure you want to remove back office ${number}?</h6>
//             <div class="google_maps_submit_buttons">
//                 <div class="google_maps_container_buttons">
//                     <button class="cancle_button" data-bs-dismiss="modal">No</button>
//                     <button onclick="removeBackOffice('${id}',${number});"  class="done_button" >Yes</button>
//                 </div>
//             </div>
//         </div>
//     `
//     $('#delete_backoffice_confirmation_model').modal('show');
// }


function appendConnectorForm(n){
    // var back_offices_count = back_offices_data.length()
        var connectorDataToUpload = {
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
            evse_uid:'',
            ocpi_connector_id:'',
            deleted: false,
            con_id:null
        }
        connector_count_manager[n-1] = connector_count_manager[n-1] + 1
        
      dataToUpload.chargepoints[n-1].connectors.push(connectorDataToUpload)
      $(`#ConnectorContainer${n}`).append(`
      
      <div class="connectors_box" id="connector_delete_id_${n}_${connector_count_manager[n-1]}">
                        <div class="connector_heading collapsible1">
                            <div class="connector_heading_container">
                                <span>Connector ${connector_count_manager[n-1]}</span>
                                <div class="delete_bar"
                                    onclick="removeConnectorConfirmation('connector_delete_id_${n}_${connector_count_manager[n-1]}',
                                    ${connector_count_manager[n-1]},${n},${null})"
                                 ></div>
                            </div>
                        </div>
                        <div class="content">
                            <div class="charge_point_form">                                                                                                                                                                                              
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector Type</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] - 1 },${0},this.value,${100}, ${false});">
                                            <option value="">Select</option>
                                            ${connector_type_speed_html_new}
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}0"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector ID</label>
                                    <input type="number"    class="inputs" placeholder="Enter connector ID" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] - 1 }, ${1}, this.value,${100} , ${false});"> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}1"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector Name</label>
                                    <input type="text"    class="inputs" placeholder="Enter connector name" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] - 1 }, ${2}, this.value,${100}, ${false} );"> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}2"></p>
                                </div>
            
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Status</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] -1 },${3},this.value,${100}, ${false});">
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
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] - 1 },${4},this.value,${100}, ${false});">
                                            <option value="">Select</option>
                                            ${connector_type_html}
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}4"></p>
                                </div>                                                                                                                                                                                              
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Maximum Charge Rate</label>
                                    <input type="number"    class="inputs" placeholder="Enter charge rate" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] - 1},${5},this.value,${0}, ${false});"> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}5"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Tariff Amount</label>
                                    <input type="number"    class="inputs" placeholder="Enter tariff amount" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] -1 },${6},this.value,${100}, ${false});"> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}6"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Tariff Currency</label>
                                    <div class="station_select-box charge_point_field">
                                        <select   class="dropdown_input small_dropdown_input" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] -1 },${7},this.value,${100}, ${false});">
                                            <option value="">Select</option>
                                            <option value="GBP(£)">GBP (£)</option>
                                            <option value="Euro(€)">Euro (€)</option>
                                        </select>
                                    </div>
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}7"></p>
                                </div>
                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Connector Sort Order</label>
                                    <input type="number"    class="inputs" placeholder="Enter sort order" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] -1 },${8},this.value,${100}, ${false});"> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}8"></p>
                                </div>   


                                <div class="charge_point_fields">
                                
                                    <label    class="labels">Evse UID</label>
                                    <input type="text"    class="inputs" placeholder="Enter ocpi evse uid" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] -1},${9},this.value, ${false});"> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}9"></p>
                                </div>

                                <div class="charge_point_fields">
                                
                                    <label    class="labels">OCPI Connector ID</label>
                                    <input type="text"    class="inputs" placeholder="Enter ocpi connector id" onchange="updateUploadedDataConnector(${n-1},${connector_count_manager[n-1] -1},${10},this.value, ${false});"> 
                                    
                                    <p class="error_field" id="chargepointerror${n-1}${connector_count_manager[n-1]-1}10"></p>
                                </div>
            
                            </div>
                        </div>
                    </div>
      
      `);
}


var uploaded_images = [];
var uploaded_images_copy = [];
var remove_images = [];
var assign_food = [];
var assign_retail = [];
var assign_amenities = [];
let images_from_backend = [];
var temp_assign_food = [];
var temp_assign_retail = [];
var temp_assign_amenities = [];
let temp_uploaded_images = [];
for(i=0; i< services_data1.station_images.length;i++){
    images_from_backend.push(services_data1.station_images[i].image)
}
uploaded_images = images_from_backend;
uploaded_images_copy = images_from_backend;
var food
var retail
var amenities
var foods
var retail_station
var station_images
var amenities_station
({food, retail, amenities,foods, retail_station , station_images , amenities_station,chargepoints} = services_data)

var food_content = ''
var retail_content = ''
var amenities_content = ''
var img_cont = ''




for(var im=0; im <station_images.length ; im++){
    img_cont += `<img src=${station_images[im].image} >`
}

$(`#images_container`).append(img_cont);


for (var f=0; f< foods.length ; f++){
    assign_food.push(foods[f].id)
}
dataToUpload.food_to_go = assign_food

append_food_images_side_bar(assign_food)

for (var r=0; r< retail_station.length ; r++){
    assign_retail.push(retail_station[r].id)
}
dataToUpload.retail = assign_retail

append_retail_images_side_bar(assign_retail)

for (var a=0; a< amenities_station.length ; a++){
    assign_amenities.push(amenities_station[a].id)
}

dataToUpload.amenities = assign_amenities


append_amenity_images_side_bar(assign_amenities)

temp_assign_retail = [...assign_retail];

temp_assign_food = [...assign_food];

temp_assign_amenities = [...assign_amenities];
function addRemovedImages() {
    remove_images.forEach(x =>{
        uploaded_images.push(x);
    });
    remove_images = [];
    updateImages();
}

function removeAssignedImage(event) {
    if(temp_uploaded_images.includes(event.getAttribute("ref"))){
        remove_images.push(event.getAttribute("ref"));
    }
    temp_uploaded_images.splice(event.getAttribute("data"),1);
    updateImages();
}

function updateImages(){
    if(temp_uploaded_images.length == 0){
        $("#add_images_container").html(`<div class="text_container"><div class="text_for_images"><p>Click 'Add Images' to add images here</p></div></div>`);
    }else{
        const tempArray = temp_uploaded_images;
        temp_uploaded_images = [];
        tempArray.forEach(url => {
            if (temp_uploaded_images.length === 0){
                $("#add_images_container").html(`<div class="img-download">
                    <img src=${url} class="promotion_img_tag_style" alt="image">
                    <b class="promotion_discard_button-style" data="${temp_uploaded_images.length}" ref="${url}" id="discard_edit"  onclick="removeAssignedImage(this)" class="discard">x</b>
                    </div>`);
            }
            else
            { 
                $("#add_images_container").append(`<div class="img-download">
                    <img src=${url} class="promotion_img_tag_style" alt="image">
                    <b class="promotion_discard_button-style" data="${temp_uploaded_images.length}" ref="${url}" id="discard_edit"  onclick="removeAssignedImage(this)" class="discard">x</b>
                    </div>`);
            }
            temp_uploaded_images.push(url)
            
        });
    }
    if (temp_uploaded_images.length < 10) $("#add_images_count").html(`0${temp_uploaded_images.length} added`)
            else $("#add_images_count").html(`${temp_uploaded_images.length} added`)
}


checkingMFGSite();
function updateUploadedDataSet(n, val){
    const upload_keys = Object.keys(dataToUpload);
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
    } else if (n === 35){
        let maxVal = 200;
        maxVal = parseFloat(maxVal);
        if(val.length>maxVal && maxVal!=0){
            document.getElementById(`error_field${n}`).innerHTML = "You can't enter more than " + maxVal + " chars.";
        }else{
            document.getElementById(`error_field${n}`).innerHTML=''
        }
    }
     else if (val.length ===0){
        if(n != 3 && n != 4) {
            document.getElementById(`error_field${n}`).innerHTML = "This field is required"
        }
    } 
    else if (n===0 && val.length > 15){     
        document.getElementById(`error_field${n}`).innerHTML = "You can't enter more than 15 chars"
    }else if ( val.length > 100){
        document.getElementById(`error_field${n}`).innerHTML = "You can't enter more than 100 chars"
    }
    dataToUpload[upload_keys[n]]= val
}

function updateUploadedDataSetSite(n, val){
    const upload_keys = Object.keys(dataToUpload.stationTypeSiteData);
    dataToUpload.stationTypeSiteData[upload_keys[n]]= val;
    if (val.length === 0){  
        document.getElementById(`error_field_site${n}`).innerHTML = "This field is required"
    } 
    else if (val.length > 100){
        document.getElementById(`error_field_site${n}`).innerHTML = "You can't enter more than 100 chars"
    }
}

function updateUploadedDataChargePoint(n, m, val, updated_cp) {
    // Map field index to explicit key
    const fieldMap = [
        'charge_point_id',
        'charge_point_name',
        'status',
        // 'back_office',
        'device_id',
        'payter_terminal_id',
        'ampeco_charge_point_id',
        'ampeco_charge_point_name',
        'worldline_terminal_id'
    ];
    const key = fieldMap[m];
    let chargepoint_data = dataToUpload.chargepoints[n - 1];
    chargepoint_data[key] = val;
    let worldLineStationCheck = (
        (
            dataToUpload["payment_terminal"] === 'Worldline' &&
            m !== 5
        ) || dataToUpload["payment_terminal"] !== 'Worldline'
    );
    const errorElem = document.getElementById(`chargepointerror${n-1}${m}`);
    if (m === 6) {
        // No validation for Ampeco Charge Point Name
        if (errorElem) errorElem.innerHTML = "";
        return;
    }
    if (val.length === 0 && worldLineStationCheck) {
        if (errorElem) errorElem.innerHTML = "This field is required";
    } else if (m === 3 && !parseInt(val)) {
        if (errorElem) errorElem.innerHTML = "Only numbers are allowed.";
    } else if (val.length > 15 && m === 0) {
        if (errorElem) errorElem.innerHTML = "You can't enter more than 15 chars";
    } else if (val.length > 25 && worldLineStationCheck) {
        if (errorElem) errorElem.innerHTML = "You can't enter more than 25 chars";
    } else if (m === 5 && val.length === 0) {
        if (errorElem) errorElem.innerHTML = "This field is required";
    } else if (m === 5 && val.length > 30) {
        if (errorElem) errorElem.innerHTML = "You can't enter more than 30 chars";
    } else {
        if (errorElem) errorElem.innerHTML = "";
    }
}
function updateUploadedDataConnector(c,n,m,val,maxVal,updated_cn){
    const upload_keys = Object.keys(dataToUpload.chargepoints[c].connectors[n]);
    let connector_updated_data = dataToUpload.chargepoints[c].connectors[n]
    
    let numeric_fields = [5,6,8]

    if (updated_cn) {
        if (numeric_fields.includes(m)){
            connector_updated_data[upload_keys[m+2]] = parseFloat(val)
        }else connector_updated_data[upload_keys[m+2]] = val
    }else{
        if (numeric_fields.includes(m)){
            connector_updated_data[upload_keys[m]] = parseFloat(val)
        }else connector_updated_data[upload_keys[m]] = val
    }
    if (val.length ===0){      
        document.getElementById(`chargepointerror${c}${n}${m}`).innerHTML = "This field is required"
    }else if (numeric_fields.includes(m)){
        const num = parseFloat(val);
        maxVal = parseFloat(maxVal);
        if (num<=0.0){
            document.getElementById(`chargepointerror${c}${n}${m}`).innerHTML = "Value is not valid.";
        }else if(num>maxVal && maxVal!=0){
            document.getElementById(`chargepointerror${c}${n}${m}`).innerHTML = "Can't be more than " + maxVal + ".";
        }else{
            document.getElementById(`chargepointerror${c}${n}${m}`).innerHTML=''
        }
    }else if (val.length > 15 && m===1){       
        document.getElementById(`chargepointerror${c}${n}${m}`).innerHTML = "You can't enter more than 15 chars"
    }else  if (val.length > 25){
        document.getElementById(`chargepointerror${c}${n}${m}`).innerHTML = "You can't enter more than 25 chars"
    }

}
  function toggleModal(n){
    const contents = [ "Assign Retail", "Assign Images","Assign Food To Go","Assign Amenities"]
    var modal = document.getElementById("side_modal_id");
    modal.classList.toggle("active");
    let content_to_be_embed_in_side_modal;
    if (n === 1) {
        
        temp_uploaded_images = [...uploaded_images];
        var content_image_container  = ''
        if (uploaded_images.length > 0){
            for( i=0 ; i< uploaded_images.length; i++){
                content_image_container += `<div class="img-download">
                    <img src=${uploaded_images[i]} class="promotion_img_tag_style" alt="image">
                    <b class="promotion_discard_button-style" data="${i}" id="discard_edit"  ref="${uploaded_images[i]}" onclick="removeAssignedImage(this)" class="discard">x</b>
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
                <button class="assign_image" onclick="appendImages();">Assign</button>
            </div>`
    }
    else{
        var inner_content = ''
        var selected_count = 0
        if (n === 0) {
            
            retail_content  =append_retail_images_side_bar(temp_assign_retail)
            inner_content = retail_content;
            selected_count = temp_assign_retail.length
        }
        else if ( n===2){
            food_content = append_food_images_side_bar(temp_assign_food)
            inner_content = food_content;
            selected_count = temp_assign_food.length;
        }
        else if(n===3){
            amenities_content = append_amenity_images_side_bar(temp_assign_amenities)
            inner_content = amenities_content;
            selected_count =temp_assign_amenities.length;
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
        let content_for_image_container  = ''
        for( i=0 ; i< uploaded_images.length; i++){
            content_for_image_container += `<img src=${uploaded_images[i]} >`
        }      
        dataToUpload.images = uploaded_images
        $("#images_container").html(content_for_image_container);
        toggleModal();
  }
