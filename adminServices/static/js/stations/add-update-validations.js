function searchServiceId(id, Array) {
    for (var i = 0; i < Array.length; i++) {
        if (Array[i].id === id) {
            return i;
        }
    }
}

function appendServices(type) {
    let content_for_image_container = ''
    if (type === 0) {
        var assign_retail = temp_assign_retail;
        for (var i = 0; i < assign_retail.length; i++) {
            service_position_in_array = searchServiceId(assign_retail[i], retail);
            content_for_image_container += `<div class="services_image"><img src=${retail[service_position_in_array].image_path} ></div>`
        }
        dataToUpload.retail = assign_retail
        dataToUpload.retail_timing = assign_retail_time_availability
    } else if (type === 2) {
        var assign_food = temp_assign_food
        for (i = 0; i < assign_food.length; i++) {
            var service_position_in_array = searchServiceId(assign_food[i], food);
            content_for_image_container += `<div class="services_image"><img src=${food[service_position_in_array].image_path} ></div>`
        }
        dataToUpload.food_to_go = assign_food
        dataToUpload.food_timing = assign_food_time_availability

    } else {
        var assign_amenities = temp_assign_amenities
        for (i = 0; i < assign_amenities.length; i++) {
            service_position_in_array = searchServiceId(assign_amenities[i], amenities);
            content_for_image_container += `<div class="services_image"><img src=${amenities[service_position_in_array].image_path} ></div>`
        }
        dataToUpload.amenities = assign_amenities
        dataToUpload.amenity_timing = assign_amenities_time_availability
        terminal_container_content = ""
        if ($('#ValetingCheck').val() === "Yes") {
            show_valeting_terminals();
        }
        removeAmenityFromValetingAmenities();
    }


    $(`#images_container${type}`).html(content_for_image_container);
    toggleModal();
}
function submitStationData(){
    dataToUpload["payment_terminal"] = getArrayOfChecklist();
    let error_less = true
    let validationErrors = [];
    if ($('#ValetingCheck').val() === "Yes") {
        dataToUpload.valeting_terminals = valeting_terminals;
        dataToUpload.valeting_machines = valeting_machines;
    }
    const upload__keys = Object.keys(dataToUpload);
    
    upload__keys.forEach((element, index) => {
        if (index === 31){
            let maxVal = 100;
            let num = parseFloat(dataToUpload[element]);
            maxVal = parseFloat(maxVal);
            if (num<0.0){
                document.getElementById(`error_field${index}`).innerHTML = "Value is not valid.";
                validationErrors.push({ field: element, index, message: "Value is not valid." });
                if (error_less) error_less = false;
            }else if(num>maxVal && maxVal!=0){
                document.getElementById(`error_field${index}`).innerHTML = "Can't be more than " + maxVal + ".";
                validationErrors.push({ field: element, index, message: `Can't be more than ${maxVal}.` });
                if (error_less) error_less = false;
            }else{
                document.getElementById(`error_field${index}`).innerHTML=''
            }
        }
        
        if (typeof (dataToUpload[element]) === "number") {
            if (element === 'latitude') {
                if (dataToUpload[element] == 0.0) {
                    document.getElementById(`error_field${index}`).innerHTML = "Please select the location";
                    validationErrors.push({ field: element, index, message: "Please select the location" });
                    if (error_less) error_less = false;
                } else document.getElementById(`error_field${index}`).innerHTML = "";
            }
            if (element === 'longitude') {
                if (dataToUpload[element] == 0.0) {
                    document.getElementById(`error_field${index}`).innerHTML = "Please select the location";
                    validationErrors.push({ field: element, index, message: "Please select the location" });
                    if (error_less) error_less = false;
                }
                else document.getElementById(`error_field${index}`).innerHTML = "";
            }
        }
        if (element === 'site_id') {
            const station_type = document.getElementById("MFGEVSiteCheck").value
            if (!dataToUpload[element] && (station_type === 'MFG EV' || station_type === 'MFG EV plus Forecourt')) {
                document.getElementById(`error_field${index}`).innerHTML = "Null value not allowed";
                validationErrors.push({ field: element, index, message: "Null value not allowed" });
                if (error_less) error_less = false;
            }
        }

        if (element === 'payment_terminal') {
            if (index == 29 && dataToUpload["payment_terminal"].length === 0) {
                document.getElementById(`error_field${index}`).innerHTML = "This field is required";
                validationErrors.push({ field: element, index, message: "This field is required" });
                if (error_less) error_less = false;
            }
            else {
                document.getElementById(`error_field${index}`).innerHTML = ""
            }
        }
        if (typeof (dataToUpload[element]) === "string") {
            var select_list_items = [7, 8, 9, 15, 28, 29]
            const station_type = document.getElementById("MFGEVSiteCheck").value
            if ((index < 17 || index == 28 || index == 29 || (index==30 && dataToUpload["payment_terminal"].includes('Worldline')) || (index == 27 && (station_type === 'MFG EV' || station_type === 'MFG EV plus Forecourt'))) && dataToUpload[element].length === 0) {
                if (index != 3 && index != 4) {
                    document.getElementById(`error_field${index}`).innerHTML = "This field is required";
                    validationErrors.push({ field: element, index, message: "This field is required" });
                    if (error_less) error_less = false;
                }
            }
            else if (index === 0 && dataToUpload[element].length > 15 && !select_list_items.includes(index)) {
                document.getElementById(`error_field${index}`).innerHTML = "You cant enter more than 15 chars";
                validationErrors.push({ field: element, index, message: "You cant enter more than 15 chars" });
                if (error_less) error_less = false;
            } else if ((index < 17 || (index==30 && dataToUpload["payment_terminal"].includes('Worldline'))) && dataToUpload[element].length > 100 && !select_list_items.includes(index)) {
                document.getElementById(`error_field${index}`).innerHTML = "You cant enter more than 100 chars";
                validationErrors.push({ field: element, index, message: "You cant enter more than 100 chars" });
                if (error_less) error_less = false;
            } else {

                if (index < 17) document.getElementById(`error_field${index}`).innerHTML = ""
                if (index == 27 && isNaN(dataToUpload[element]) === true) {
                    document.getElementById(`error_field${index}`).innerHTML = "Only Number Allowed";
                    validationErrors.push({ field: element, index, message: "Only Number Allowed" });
                    if (error_less) error_less = false;
                }
                if (element === 'email') {
                    const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
                    let result = re.test(String(dataToUpload[element]).toLowerCase());
                    if (result) document.getElementById(`error_field${index}`).innerHTML = ""
                    else {
                        document.getElementById(`error_field${index}`).innerHTML = "Please enter email in valid format";
                        validationErrors.push({ field: element, index, message: "Please enter email in valid format" });
                        if (error_less) error_less = false;
                    }
                }
                if (element === 'phone') {
                    const reg = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/im
                    let result_phone = reg.test(String(dataToUpload[element]).toLowerCase());
                    if (result_phone) document.getElementById(`error_field${index}`).innerHTML = ""
                    else {
                        document.getElementById(`error_field${index}`).innerHTML = "Please enter phone no in valid format";
                        validationErrors.push({ field: element, index, message: "Please enter phone no in valid format" });
                        if (error_less) error_less = false;
                    }
                }
            }
        }
        if (typeof (dataToUpload[element]) === "object" && element === "working_hours") {
            const working_hours_keys = Object.keys(dataToUpload[element]);
            let error_status_for_working_hours = false
            working_hours_keys.forEach((el, index) => {
                if (dataToUpload.working_hours[el].full_hours === false && dataToUpload.working_hours[el].end_time.length === 0 && dataToUpload.working_hours[el].start_time.length === 0 && `${el}` == "monday_friday") {

                    error_status_for_working_hours = true
                    document.getElementById(`${el}_error`).innerHTML = "Time selection is required";
                    validationErrors.push({ field: 'working_hours', index: el, message: "Time selection is required" });
                    if (error_less) error_less = false
                } else if (dataToUpload.working_hours[el].full_hours === false && dataToUpload.working_hours[el].end_time.length > 0 && dataToUpload.working_hours[el].start_time.length > 0) {


                    document.getElementById(`${el}_error`).innerHTML = "";
                }
                if (dataToUpload.working_hours[el].full_hours === true) {


                    document.getElementById(`${el}_error`).innerHTML = "";
                }
            })
            if (error_status_for_working_hours) {
                document.getElementById(`error_field_working_hours`).innerHTML = "Time selection is required";
                validationErrors.push({ field: 'working_hours', index: 'error_field_working_hours', message: "Time selection is required" });
                if (error_less) error_less = false;

            }
            else document.getElementById(`error_field_working_hours`).innerHTML = "";

        }
        if (typeof (dataToUpload[element]) === "object" && element === "stationTypeSiteData") {
            select_list_items = []
            if (dataToUpload.station_type_is_mfg) {
                const upload__site_keys = Object.keys(dataToUpload[element]);

                upload__site_keys.forEach((el1, index) => {
                    if (el1 === 'area') {

                        if (dataToUpload.stationTypeSiteData[el1].length === 0) {
                            document.getElementById(`error_field_site${index}`).innerHTML = "This field is required";
                            validationErrors.push({ field: 'stationTypeSiteData', index: el1, message: "This field is required" });
                            if (error_less) error_less = false;
                        } else if (dataToUpload.stationTypeSiteData[el1].length < 1 && !select_list_items.includes(index)) {
                            document.getElementById(`error_field_site${index}`).innerHTML = "Must be atleast 1 chars long";
                            validationErrors.push({ field: 'stationTypeSiteData', index: el1, message: "Must be atleast 1 chars long" });
                            if (error_less) error_less = false
                        } else if (dataToUpload.stationTypeSiteData[el1].length > 10) {
                            document.getElementById(`error_field_site${index}`).innerHTML = "You cant enter more than 10 chars";
                            validationErrors.push({ field: 'stationTypeSiteData', index: el1, message: "You cant enter more than 10 chars" });
                            if (error_less) error_less = false
                        } else document.getElementById(`error_field_site${index}`).innerHTML = "";
                    }
                    else {
                        if (dataToUpload.stationTypeSiteData[el1].length === 0) {
                            document.getElementById(`error_field_site${index}`).innerHTML = "This field is required";
                            validationErrors.push({ field: 'stationTypeSiteData', index: el1, message: "This field is required" });
                            if (error_less) error_less = false;
                        }
                        else if (dataToUpload.stationTypeSiteData[el1].length > 100) {
                            document.getElementById(`error_field_site${index}`).innerHTML = "You cant enter more than 100 chars";
                            validationErrors.push({ field: 'stationTypeSiteData', index: el1, message: "You cant enter more than 100 chars" });
                            if (error_less) error_less = false
                        } else document.getElementById(`error_field_site${index}`).innerHTML = "";
                    }

                })
            }
        }


        if (typeof (dataToUpload[element]) === "object" && element === "backoffice"){
            const station_type = document.getElementById("MFGEVSiteCheck").value
            dataToUpload.backoffice.forEach((elm, i) => {
                if (!deleted_backoffice_from_frontend.includes(i)) {
                    const backoffice__keys = Object.keys(elm)
                    
                    let cp = dataToUpload.backoffice[i]
                    backoffice__keys.forEach((elm1, j) => {
                        if (elm1 !== 'deleted') {
                            if (typeof(cp[elm1]) === "string" && cp[elm1] !== null) {                            
                                
                                    if (
                                        cp[elm1].length === 0 && (station_type === 'MFG EV' || station_type === 'MFG EV plus Forecourt')
                                    ) {
                                        document.getElementById(`backOfficeError${i}${j}`).innerHTML = "This field is required";
                                        validationErrors.push({ field: 'backoffice', index: `${i}-${elm1}`, message: "This field is required" });
                                        if (error_less) error_less = false;
                                    }
                                    // else if (elm1 === "charge_point_id" && cp[elm1].length > 15){
                                    //     document.getElementById(`chargepointerror${i}${j - 2}`).innerHTML = "You can't enter more than 15 chars";
                                    //     if (error_less) error_less = false;
                                    // } 
                                    else if (
                                        cp[elm1].length > 25 && (station_type === 'MFG EV' || station_type === 'MFG EV plus Forecourt')
                                    ) {
                                        document.getElementById(`backOfficeError${i}${j}`).innerHTML = "You can't enter more than 25 chars";
                                        if (error_less) error_less = false;
                                    } else if (j === 4 && !parseInt(cp[elm1])) {
                                        document.getElementById(`backOfficeError${i}${j}`).innerHTML = "Only numbers are allowed."
                                        if (error_less) error_less = false;
                                    }
                                    // else if (elm1 === "charge_point_id" && cp[elm1].length > 15){
                                    //     document.getElementById(`chargepointerror${i}${j - 2}`).innerHTML = "You can't enter more than 15 chars";
                                    //     if (error_less) error_less = false;
                                    // } else if (
                                    //     cp[elm1].length > 25 && worldLineStationCheckInSubmit
                                    // ) {
                                    //     document.getElementById(`chargepointerror${i}${j}`).innerHTML = "You can't enter more than 25 chars";
                                    //     if (error_less) error_less = false;
                                    // } else if (j === 4 && !parseInt(cp[elm1])) {
                                    //     document.getElementById(`chargepointerror${i}${j}`).innerHTML = "Only numbers are allowed."
                                    //     if (error_less) error_less = false;
                                    // }
                                    else document.getElementById(`backOfficeError${i}${j}`).innerHTML = ""
                                // }
                            }
                        }
                    })
                }
                else {
                    dataToUpload.backoffice[i]['deleted'] = true
                }
            })
        }

        if (typeof (dataToUpload[element]) === "object" && element === "chargepoints") {
            if (dataToUpload.station_type !== 'MFG Forecourt') {
                dataToUpload.chargepoints.forEach((elm, i) => {
                    if (!deleted_chargepoint_from_frontend.includes(i)) {
                        const chargePoint__keys = Object.keys(elm)
                        let cp = dataToUpload.chargepoints[i]
                        chargePoint__keys.forEach((elm1, j) => {
                            if (elm1 === 'ampeco_charge_point_name'||elm1 === 'back_office') return; // skip all validation for these fields
                            if (elm1 !== 'deleted') {
                                if (typeof (cp[elm1]) === "string" && cp[elm1] !== null) {
                                    let worldLineStationCheckInSubmit=(
                                        (
                                            !dataToUpload["payment_terminal"].includes('Payter') &&
                                            elm1 !== "payter_terminal_id"
                                        ) || dataToUpload["payment_terminal"].includes('Payter')
                                    )
                                    if (chargePoint__keys.includes("cp_on_updation")) {
                                        if (j > 1) {
                                            if (elm1 === "worldline_terminal_id" && !dataToUpload["payment_terminal"].includes('Worldline')) {
                                                document.getElementById(`chargepointerror${i}${j - 4}`).innerHTML = ""
                                                return;
                                            }
                                            if (
                                                cp[elm1].length === 0 && worldLineStationCheckInSubmit
                                            ) {
                                                var errorElem = document.getElementById(`chargepointerror${i}${j - 2}`);
                                                if (errorElem) errorElem.innerHTML = "This field is required";
                                                validationErrors.push({ field: 'chargepoints', index: `${i}-${elm1}`, message: "This field is required", extra: {i, j, elm1} });
                                                if (error_less) error_less = false;
                                            } else if (elm1 === "charge_point_id" && cp[elm1].length > 15) {
                                                var errorElem = document.getElementById(`chargepointerror${i}${j - 2}`);
                                                if (errorElem) errorElem.innerHTML = "You can't enter more than 15 chars";
                                                validationErrors.push({ field: 'chargepoints', index: `${i}-${elm1}`, message: "You can't enter more than 15 chars", extra: {i, j, elm1} });
                                                if (error_less) error_less = false;
                                            } else if (cp[elm1].length > 25 && worldLineStationCheckInSubmit) {
                                                var errorElem = document.getElementById(`chargepointerror${i}${j - 2}`);
                                                if (errorElem) errorElem.innerHTML = "You can't enter more than 25 chars";
                                                validationErrors.push({ field: 'chargepoints', index: `${i}-${elm1}`, message: "You can't enter more than 25 chars", extra: {i, j, elm1} });
                                                if (error_less) error_less = false;
                                            }else if (j === 5 && !parseInt(cp[elm1])) {
                                                var errorElem = document.getElementById(`chargepointerror${i}${j - 2}`);
                                                if (errorElem) errorElem.innerHTML = "Only numbers are allowed."
                                                validationErrors.push({ field: 'chargepoints', index: `${i}-${elm1}`, message: "Only numbers are allowed.", extra: {i, j, elm1} });
                                                if (error_less) error_less = false;
                                            }
                                            else if(j!==4){
                                                var errorElem = document.getElementById(`chargepointerror${i}${j - 2}`);
                                                if (errorElem) errorElem.innerHTML = ""
                                            }
                                        }
                                    }
                                    else {
                                        if (elm1 === "worldline_terminal_id" && !dataToUpload["payment_terminal"].includes('Worldline')) {
                                            document.getElementById(`chargepointerror${i}${j}`).innerHTML = ""
                                            return;
                                        }
                                        if (
                                            cp[elm1].length === 0 && worldLineStationCheckInSubmit && j!==3
                                        ) {
                                            document.getElementById(`chargepointerror${i}${j}`).innerHTML = "This field is required";
                                            validationErrors.push({ field: 'chargepoints', index: `${i}-${elm1}`, message: "This field is required", extra: {i, j, elm1} });
                                            if (error_less) error_less = false;
                                        } else if (elm1 === "charge_point_id" && cp[elm1].length > 15) {
                                            var errorElem = document.getElementById(`chargepointerror${i}${j - 2}`);
                                            if (errorElem) errorElem.innerHTML = "You can't enter more than 15 chars";
                                            validationErrors.push({ field: 'chargepoints', index: `${i}-${elm1}`, message: "You can't enter more than 15 chars", extra: {i, j, elm1} });
                                            if (error_less) error_less = false;
                                        } else if (
                                            cp[elm1].length > 25 && worldLineStationCheckInSubmit
                                        ) {
                                            var errorElem = document.getElementById(`chargepointerror${i}${j}`);
                                            if (errorElem) errorElem.innerHTML = "You can't enter more than 25 chars";
                                            validationErrors.push({ field: 'chargepoints', index: `${i}-${elm1}`, message: "You can't enter more than 25 chars", extra: {i, j, elm1} });
                                            if (error_less) error_less = false;
                                        } else if (j === 3 && !parseInt(cp[elm1])) {
                                            var errorElem = document.getElementById(`chargepointerror${i}${j}`);
                                            if (errorElem) errorElem.innerHTML = "Only numbers are allowed."
                                            validationErrors.push({ field: 'chargepoints', index: `${i}-${elm1}`, message: "Only numbers are allowed.", extra: {i, j, elm1} });
                                            if (error_less) error_less = false;
                                        } else if (j!==4){
                                            var errorElem = document.getElementById(`chargepointerror${i}${j}`);
                                            if (errorElem) errorElem.innerHTML = ""
                                        }
                                    }
                                }
                                if (typeof (cp[elm1]) === "object" && elm1 === "connectors") {
                                    let numeric_fields = [5, 6, 8]
                                    cp[elm1].forEach((connector, k) => {
                                        if (!deleted_connectors_from_frontend[i].includes(k)) {
                                            var dummy_connector = connector;
                                            var connector__keys = Object.keys(connector)
                                            connector__keys.forEach((con, x) => {
                                                if (con !== 'deleted') {

                                                    if (connector__keys.includes("con_on_updation")) {
                                                        if (x > 1) {
                                                            if (dummy_connector[con] == null ){
                                                                document.getElementById(`chargepointerror${i}${k}${x - 2}`).innerHTML = "This field is required"
                                                                validationErrors.push({ field: 'connectors', index: `${i}-${k}-${con}`, message: "This field is required", extra: {i, k, con} });
                                                                if (error_less) error_less = false;
                                                            }
                                                            else if (dummy_connector[con].length === 0 ) {

                                                                document.getElementById(`chargepointerror${i}${k}${x - 2}`).innerHTML = "This field is required"
                                                                validationErrors.push({ field: 'connectors', index: `${i}-${k}-${con}`, message: "This field is required", extra: {i, k, con} });
                                                                if (error_less) error_less = false;
                                                            } else if (numeric_fields.includes(x - 2)) {
                                                                let num = parseFloat(dummy_connector[con]);
                                                                if (isNaN(num) || num <= 0.0) {
                                                                    document.getElementById(`chargepointerror${i}${k}${x - 2}`).innerHTML = "Value is not valid.";
                                                                    validationErrors.push({ field: 'connectors', index: `${i}-${k}-${con}`, message: "Value is not valid.", extra: {i, k, con} });
                                                                    if (error_less) error_less = false;
                                                                } else if (num > 100 && x != 7) {
                                                                    document.getElementById(`chargepointerror${i}${k}${x - 2}`).innerHTML = "Can't be more than 100.";
                                                                    validationErrors.push({ field: 'connectors', index: `${i}-${k}-${con}`, message: "Can't be more than 100.", extra: {i, k, con} });
                                                                    if (error_less) error_less = false;
                                                                } else {
                                                                    document.getElementById(`chargepointerror${i}${k}${x - 2}`).innerHTML = ''
                                                                }
                                                            }
                                                            else document.getElementById(`chargepointerror${i}${k}${x - 2}`).innerHTML = ""
                                                        }
                                                    } else if (dummy_connector[con] !== null) {
                                                        if (dummy_connector[con].length === 0) {// && x !==9) {
                                                            document.getElementById(`chargepointerror${i}${k}${x}`).innerHTML = "This field is required";
                                                            validationErrors.push({ field: 'connectors', index: `${i}-${k}-${con}`, message: "This field is required", extra: {i, k, con} });
                                                            if (error_less) error_less = false;
                                                        } else if (numeric_fields.includes(x)) {
                                                            let num = parseFloat(dummy_connector[con]);
                                                            if (isNaN(num) || num <= 0.0) {
                                                                document.getElementById(`chargepointerror${i}${k}${x}`).innerHTML = "Value is not valid.";
                                                                validationErrors.push({ field: 'connectors', index: `${i}-${k}-${con}`, message: "Value is not valid.", extra: {i, k, con} });
                                                                if (error_less) error_less = false;
                                                            } else if (num > 100 && x != 5) {
                                                                document.getElementById(`chargepointerror${i}${k}${x}`).innerHTML = "Can't be more than 100.";
                                                                validationErrors.push({ field: 'connectors', index: `${i}-${k}-${con}`, message: "Can't be more than 100.", extra: {i, k, con} });
                                                                if (error_less) error_less = false;
                                                            } else {
                                                                document.getElementById(`chargepointerror${i}${k}${x}`).innerHTML = ''
                                                            }
                                                        }
                                                        else{
                                                            // if(x!==9)
                                                            document.getElementById(`chargepointerror${i}${k}${x}`).innerHTML = ""
                                                        }
                                                         
                                                    }
                                                }
                                            })
                                        }
                                        else {
                                            dataToUpload.chargepoints[i].connectors[k]['deleted'] = true
                                        }
                                    })
                                }
                                if (elm1 === "ampeco_charge_point_id" && cp[elm1].length === 0) {
                                    var ampecoIdError = document.getElementById(`chargepointerror${i}5`);
                                    if (ampecoIdError) ampecoIdError.innerHTML = "This field is required";
                                    validationErrors.push({ field: 'chargepoints', index: `${i}-ampeco_charge_point_id`, message: "This field is required", extra: {i} });
                                    if (error_less) error_less = false;
                                } else if (elm1 === "ampeco_charge_point_id" && cp[elm1].length > 30) {
                                    var ampecoIdError = document.getElementById(`chargepointerror${i}5`);
                                    if (ampecoIdError) ampecoIdError.innerHTML = "You can't enter more than 30 chars";
                                    validationErrors.push({ field: 'chargepoints', index: `${i}-ampeco_charge_point_id`, message: "You can't enter more than 30 chars", extra: {i} });
                                    if (error_less) error_less = false;
                                }
                            }
                        })
                    }
                    else {
                        dataToUpload.chargepoints[i]['deleted'] = true
                    }
                })
            }
        }

        if (typeof (dataToUpload[element]) === "object" && $('#ValetingCheck').val() === "Yes" && element === "valeting_terminals") {
            
            var duplicateValetingTerminalsChecker = []
            dataToUpload.valeting_terminals.forEach((valeting_terminal, valeting_terminal_index) => {
                if (!valeting_terminal.deleted) {
                    valeting_terminal.payter_serial_number.length > 20 ?
                        ($(`#valeting_error${valeting_terminal_index}0`).html("Can't be more than 20 characters"), error_less = false) :
                        valeting_terminal.payter_serial_number === "" ?
                            ($(`#valeting_error${valeting_terminal_index}0`).html("This field is required"), error_less = false) :
                            duplicateValetingTerminalsChecker.includes(valeting_terminal.payter_serial_number) ?
                                ($(`#valeting_error${valeting_terminal_index}0`).html("This terminal is already entered"), error_less = false) :
                                ($(`#valeting_error${valeting_terminal_index}0`).html(""), duplicateValetingTerminalsChecker.push(valeting_terminal.payter_serial_number));
                    !valeting_terminal.amenities.length ?
                        ($(`#valeting_error${valeting_terminal_index}1`).html("Please select atleast one amenity"), error_less = false) :
                        $(`#valeting_error${valeting_terminal_index}1`).html("");
                    valeting_terminal.status === "" ?
                        ($(`#valeting_error${valeting_terminal_index}2`).html("This field is required"), error_less = false) :
                        $(`#valeting_error${valeting_terminal_index}2`).html("");
                }
            })
        }

        if (typeof (dataToUpload[element]) === "object" && $('#ValetingCheck').val() === "Yes" && element === "valeting_machines") {
            var duplicateValetingMachinesChecker = [];
            dataToUpload.valeting_machines.forEach((valeting_machine, valeting_machine_index) => {
                const status = valeting_machine.status || 
                                (valeting_machine.is_active ? "Active" : "Inactive");
                const is_active = valeting_machine.is_active !== undefined ? 
                                valeting_machine.is_active : 
                                valeting_machine.status === "Active";

                // Validate machine_id
                valeting_machine.machine_id === "" ?
                    ($(`#valeting_machine_error${valeting_machine_index}0`).html("Machine ID is required"), error_less = false) :
                    duplicateValetingMachinesChecker.includes(valeting_machine.machine_id) ?
                        ($(`#valeting_machine_error${valeting_machine_index}0`).html("This machine ID already exists"), error_less = false) :
                        ($(`#valeting_machine_error${valeting_machine_index}0`).html(""), duplicateValetingMachinesChecker.push(valeting_machine.machine_id));

                // Validate machine_name
                valeting_machine.machine_name === "" ?
                    ($(`#valeting_machine_error${valeting_machine_index}1`).html("Machine name is required"), error_less = false) :
                    ($(`#valeting_machine_error${valeting_machine_index}1`).html(""));

                // Validate status
                status === "" ?
                    ($(`#valeting_machine_error${valeting_machine_index}3`).html("Status is required"), error_less = false) :
                    ($(`#valeting_machine_error${valeting_machine_index}3`).html(""));
                
                valeting_machine.status = status;
                valeting_machine.is_active = is_active;
            });
        }
        if (index === 33) {
            // Read value directly from input
            let value = '';
            const inputElem = document.getElementById('ampeco-site-id-input');
            if (inputElem) value = inputElem.value;
            var ampecoSiteIdError = document.getElementById('error_field33');
            if (value === null || value.trim() === '') {
                if (ampecoSiteIdError) ampecoSiteIdError.innerHTML = 'Site ID cannot be null or empty';
                validationErrors.push({ field: element, index, message: 'Site ID cannot be null or empty' });
                error_less = false;
                dataToUpload[element] = null;
            } else {
                if (ampecoSiteIdError) ampecoSiteIdError.innerHTML = '';
                dataToUpload[element] = value;
            }
        }
        if (index === 34) {
            // Read value directly from input
            let value = '';
            const inputElem = document.getElementById('ampeco-site-title-input');
            if (inputElem) value = inputElem.value;
            var ampecoSiteTitleError = document.getElementById('error_field34');
            const trimmed = value ? value.trim() : '';
            if (trimmed === '') {
                dataToUpload[element] = null;
            } else {
                dataToUpload[element] = trimmed;
            }
            if (ampecoSiteTitleError) ampecoSiteTitleError.innerHTML = '';
        }
    });
    // let error_less = true;

    location_mapping_arr = []

    dataToUpload.backoffice.forEach((back_office, back_office_index) =>{
        dataToUpload.chargepoints.forEach((charge_point, index) => {            
            charge_point.connectors.forEach((connector,connector_index) => {
                
                if (
                    // back_office.back_office === connector.back_office && 
                    back_office.deleted === false && 
                    connector.deleted === false && 
                    back_office.location_id !== "" &&
                    !deleted_backoffice_from_frontend.includes(back_office)
                ){
                    location_obj = {
                        'location_id': back_office.location_id,
                        'evse_uid': connector.evse_uid,
                        'connector_id': connector.ocpi_connector_id,
                    }
                    location_mapping_arr.push(location_obj)
                }
            });
        });
    });    

    if (error_less){
        $('#loader_for_mfg_ev_app').show();
        $.ajax({
            url: validate_ocpi_location_url,
            data: {
                "location_data":JSON.stringify({
                    location_mapping_arr
                }),
                "station_type":dataToUpload["station_type"],
                "charge_points":JSON.stringify(dataToUpload.chargepoints),
                "back_office":dataToUpload.backoffice[0].back_office
             },
            headers: { "X-CSRFToken": token },
            dataType: 'json',
            type: 'POST',

            success: function (res) {
                
                if (res.valid) {
                    dataToUpload.removeImages = remove_images;
                    dataToUpload.prev_station_id = prev_station_id;
                    
                    // $('#loader_for_mfg_ev_app').show();
                    $.ajax({
                        url: submit_station_data_url,
                        data: { 'getdata': JSON.stringify(dataToUpload) },
                        headers: { "X-CSRFToken": token },
                        dataType: 'json',
                        type: 'POST',

                        success: function (res, _status) {
                            if (res.status) {
                                window.location.href = window.origin + res.url + query_params_str_edit_station
                            }
                            else {
                                $('#loader_for_mfg_ev_app').hide();
                                try {
                                    if (res.message == "Station with this id already exists") {
                                        scrollPageFunction('formSection')
                                        document.getElementById(`error_field0`).innerHTML = res.message;
                                    }
                                }
                                catch (err) {
                                }
                                customAlert(res.message)
                            }
                        },
                        error: function (res) {
                            $('#loader_for_mfg_ev_app').hide();
                            customAlert("Something went wrong");
                        }
                    });
                    // window.location.href = window.origin + res.url + query_params_str_edit_station;
                } else {
                    $('#loader_for_mfg_ev_app').hide();
                    if (res.status === "Please enter valid location - evse - connector mapping") {
                        scrollPageFunction('formSection');
                        document.getElementById('error_field0').innerHTML = res.message;
                        error_less = false;
                    }
                    customAlert(res.message);
                }
            },
            error: function (xhr, status, error) {
                $('#loader_for_mfg_ev_app').hide();
                
                let errorMessage = "Please enter valid location - evse - connector mapping";
                try {
                    const responseJson = JSON.parse(xhr.responseText);
                    if (responseJson.message) {
                        errorMessage = responseJson.message;
                    }
                } catch (e) {
                    console.warn("Could not parse error response JSON:", e);
                }

                customAlert(errorMessage);
                error_less = false;
            }

        });
    }else{
        document.getElementById(`formSection`).scrollIntoView();
    }

    //commented code for future reference and debugging

    // if (validationErrors.length > 0) {
    //     const errorList = validationErrors.map(
    //         err => `• Field: ${err.field}, Index: ${err.index}, Message: ${err.message}${err.extra ? ', Extra: ' + JSON.stringify(err.extra) : ''}`
    //     ).join('\n');
    //     console.log(
    //         '%cVALIDATION ERRORS:\n' + errorList,
    //         'color: white; background: #d32f2f; font-weight: bold; font-size: 10px; padding: 8px; border-radius: 4px;'
    //     );
    // }
}
