if (is_error.length > 0) customAlert(errors[0]);
function closeModal(id){ 
    $(id).modal('hide');
}

function UnicodeDecodeB64(strInp) {
    return decodeURIComponent(atob(strInp));
};
function b64EncodeUnicode(strInp) {
    return btoa(encodeURIComponent(strInp));
};
  

function configurationOrderByFunction(type){
    
    let update_order = 'Descending';
    let params = new URLSearchParams(url_u);
    params.forEach(function(value, key) {
        if (key === type)  {
            if (value === `Ascending`) update_order = 'Descending'
            else update_order = 'Ascending'
        }
    });
    document.getElementById(type).classList.toggle('order-by');
    window.location.href = `${window_radirect_location}?${type}=${update_order}`;
}
function show_info_box(x){
    document.getElementById(`show_tooltip_${x}`).style.display='block'
}
function hide_info_box(x){
    document.getElementById(`show_tooltip_${x}`).style.display='none'
}

function disableAddAndUpdateButtons(id){
    document.getElementById(id).disabled = true
}
function enableAddAndUpdateButtons(id){
    document.getElementById(id).disabled = false
}
function checkUniqueIdAvailability(id, error_component_id,disable_button_id,amenity_elm_id){
    
    disableAddAndUpdateButtons(disable_button_id)
    var unique_identifier = $(`#${id}`).val();
    let error_component = document.getElementById(error_component_id);
    error_component.innerHTML = '';
    if (unique_identifier.length > 0)
    {   
         var requestData = {
            "unique_identifier":unique_identifier,
            "update_query": false,
            "column_id": null,
        };
        if (amenity_elm_id){
            requestData["update_query"] = true;
            requestData["column_id"] = $(`#${amenity_elm_id}`).val();
        }

        error_component.classList.remove('error')
        error_component.classList.remove('success')
        error_component.innerHTML = 'Checking availability of sorting order...'
        

        $.ajax({
            url:check_service_id_availability_url,
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(requestData),
            headers: { "X-CSRFToken": token },
            success: function (result) {
                error_component.classList.remove('error')
                error_component.classList.add('success')
                error_component.innerHTML = 'Sorting order available'
                enableAddAndUpdateButtons(disable_button_id);
            },
            error:  function (result) {
                error_component.classList.remove('success')
                error_component.classList.add('error')
                error_component.innerHTML = `${result.responseJSON.messages}`
                disableAddAndUpdateButtons(disable_button_id);
            }        
        });
    }
}


function selectOption(url) {
    window.location.href= url;
}