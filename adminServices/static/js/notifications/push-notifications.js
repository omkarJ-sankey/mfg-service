window.onload = function () {
    displayRegions();
    regionList();
    if (image_update == "/static/images/notification-logo.png") {
      uploaded_images = []
      $("#image_div").html(`<img src=${default_image} id="default-image">`);
    }
    else {
      uploaded_images = [image_update]
      temp_uploaded_images = [image_update]
      $("#image_div").html(`<img src=${image_update} >`);
    }
    updateDescriptionCount();  
    updateSubjectCount();
}
var description_length = $("#description-input").val()?.length
var subject_length = $("#subject-input").val()?.length

function orderByFunction(type) {
    $("#loader_for_mfg_ev_app").show();
    let update_order = 'Descending';
    let new_url = '';
    const keys_for_ordering = ['order_by_scheduled_time', 'order_by_delivered_time'];
    const params = new URLSearchParams(url_u);
    params.forEach(function (value, key) {
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

// logic to show checkboxes in select list
var expanded = [];

function showCheckboxes(n) {
    if (n) {
        const checkboxes = document.getElementById(`checkbosx${n}`);
        if (expanded.includes(n)) {
            checkboxes.style.display = "none";
            var position = expanded.indexOf(n)
            expanded.pop(position)
        } else {
            expanded.forEach(element => {
                var checkbx = document.getElementById(`checkbosx${element}`);
                if (checkbx.style.display !== "none" || checkboxes.style.display === "block") checkbx.style.display = "none";
            });
            expanded = []
            expanded.push(n)
            checkboxes.style.display = "block";
        }
    }
}

$(document).on('click', function (event) {
    if (!$(event.target).closest('.checkbox_select_box').length) {
        const checkbox_elements = document.getElementsByClassName('checkboxes');
        for (var i of checkbox_elements) {
            i.style.display = "none";
        }
    }
});

function show_info_box(x) {
    document.getElementById(`show_tooltip_${x}`).style.display = 'block'
}
function hide_info_box(x) {
    document.getElementById(`show_tooltip_${x}`).style.display = 'none'
}

function appendImages() {
    uploaded_images = temp_uploaded_images;
    remove_images = [];
    let content_for_image_container = ''
    for (var i = 0; i < uploaded_images.length; i++) {
        content_for_image_container += `<img src=${uploaded_images[i]} >`
    }
    final_upload_images = [];
    uploaded_images.forEach(x => {
        final_upload_images.push(x);
    })

    $("#images_container").html(content_for_image_container);
    $("#image_div").html(content_for_image_container);
    toggleModal();
}


var uploaded_images = []
var remove_images = []
var uploaded_images_copy = []
var backup_station_ids = []
var final_upload_images = []
let temp_uploaded_images = [];

function toggleModal() {
    const modal = document.getElementById("side_modal_id");
    modal.classList.toggle("active");
    let content_to_be_embed_in_side_modal


    var content_image_container = '';
    if (uploaded_images.length > 0) {

        temp_uploaded_images = [...uploaded_images];
        for (var i = 0; i < uploaded_images.length; i++) {
            content_image_container += `<div class="img-download">
                    <img src=${uploaded_images[i]} class="promotion_img_tag_style" alt="Notification Image">
                    <b class="promotion_discard_button-style"data="${i}" id="discard_edit" ref="${uploaded_images[i]}" onclick="removeAssignedImage(this)" class="discard">x</b>
                    </div>`
        }
    }
    else {
        content_image_container = `<div class="text_container"><div class="text_for_images"><p>Click 'Add Images' to add images here</p></div></div>`
    }

    content_to_be_embed_in_side_modal = ` <div class="content_of_modal"> 
        <div class="side_modal_heading">
            <p>Assign Image</p>
            <button class="close_button" onclick="toggleModal();"><p>X</p></button>

        </div>
        <div class="side_modal_heading1" id="side_modal_label">
            <p id="add_images_count">0${uploaded_images.length} added</p>
            
            <input type="file" id="i_file" name="filename" hidden accept=".jpeg,.jpg,.png"/>
            <label for="i_file" class="add_images_label opacity-limit" id="add-btn" >Add image</label>
        </div>
        <div class="horizontal-lines"></div>
        <p class='error_assigntp' id='limit-error'></p>
        
        <div id="add_images_container">
        
        ${content_image_container}
        </div>
    </div>
    <div class="add_images_button_cotainer">
        <button class="cancel_image_button" onclick="toggleModal();">Cancel</button>
        <button class="assign_image" onclick="appendImages();">Assign</button>
    </div>`
    $("#dynamic_content_container").html(content_to_be_embed_in_side_modal);


    if (uploaded_images.length == 1) {
        $("#limit-error").html("You won't be able to access this image once removed")
        document.getElementById("side_modal_label").hidden = true
    }
}
let add_new_image = []

function add_new_image_in_container() {
    temp_uploaded_images = [...add_new_image];
    $("#add_images_container").html(`<div class="img-download">
    <img src=${temp_uploaded_images[0]} class="promotion_img_tag_style notify_image" alt="Notification Image">
    <b class="promotion_discard_button-style"data="${uploaded_images.length}" ref="${temp_uploaded_images[0]}" id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
    </div>`);
    $('#restrict_image_upload').modal('hide')

}
function do_not_add_new_image_in_container() {
    add_new_image = [];
    $('#restrict_image_upload').modal('hide');
}


$(document).on('change', '#i_file', function (event) {
    if (event.target.files) {
        const reader = new FileReader();
        reader.onload = (event_data) => {
            let url = event_data.target.result;
            if (temp_uploaded_images.length > 0) {
                $('#restrict_image_upload').modal('show');
                add_new_image = []
                add_new_image.push(url)
            } else {
                if (temp_uploaded_images.length === 0) $("#add_images_container").html(`<div class="img-download">
                        <img src=${url} class="promotion_img_tag_style" alt="Notification Image">
                        <b class="promotion_discard_button-style"data="${temp_uploaded_images.length}" ref="${url}" id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
                        </div>`);
                else $("#add_images_container").append(`<div class="img-download">
                        <img src=${url} class="promotion_img_tag_style" alt="Notification Image">
                        <b class="promotion_discard_button-style"data="${temp_uploaded_images.length}" ref="${url}" id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
                        </div>`);
                temp_uploaded_images.push(url);
                $("#add_images_count").html(`0${temp_uploaded_images.length} added`)
                document.getElementById("side_modal_label").hidden = true;
                $("#limit-error").html("You won't be able to access this image once removed")
            }
        }
        reader.readAsDataURL(event.target.files[0]);
    }
});

function removeAssignedImage(event) {
    remove_images.push(event.getAttribute("ref"));
    temp_uploaded_images.splice(event.getAttribute("data"), 1);

    if (temp_uploaded_images.length == 0) {
        $("#add_images_container").html(`<div class="text_container"><div class="text_for_images"><p>Click 'Add Images' to add images here</p></div></div>`);
        document.getElementById("side_modal_label").hidden = false;
        $("#limit-error").html("")
    } else {
        const tempArray = temp_uploaded_images;
        temp_uploaded_images = [];
        tempArray.forEach(url => {
            if (temp_uploaded_images.length === 0) {
                $("#add_images_container").html(`<div class="img-download">
                <img src=${url} class="promotion_img_tag_style" alt="Notification Image">
                <b class="promotion_discard_button-style" data="${temp_uploaded_images.length}" ref="${url}" id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
                </div>`);
            }
            else {
                $("#add_images_container").append(`<div class="img-download">
                <img src=${url} class="promotion_img_tag_style notify_image" alt="Notification Image">
                <b class="promotion_discard_button-style" data="${temp_uploaded_images.length}" ref="${url}" id="discard_edit" onclick="removeAssignedImage(this)" class="discard">x</b>
                </div>`);
            }
            temp_uploaded_images.push(url)
        });
    }
    if (temp_uploaded_images.length < 10) $("#add_images_count").html(`0${temp_uploaded_images.length} added`)
    else $("#add_images_count").html(`${temp_uploaded_images.length} added`)
}

function updateSubjectCount(){
    var max = 60;
    if (subject_length){
        $('#text-count-for-subject').text(max - subject_length);
    }
}

function charCountSubject(textarea) {
    var max = 60;
    var length = textarea.value.length;
    if(length>max){
        textarea.value = textarea.value.substring(0,60);
    }
    else{
        $('#text-count-for-subject').text(max - length);
    }
}
function updateDescriptionCount(){
    var max = 100;
    if (description_length){
        $('#text-count-for-description').text(max - description_length);
    }
}


function charCountDescription(textarea) {
    var max = 100;
    var length = textarea.value.length;
    
    if(length>max){
        textarea.value = textarea.value.substring(0,100);
    }
    else{
        $('#text-count-for-description').text(max - length);
    }
}

function validateData() {
    let errorStatus = false
    let error_count = 0;
    let scroll_flag = true
    if ((typeof ($("#subject-input").val()) != 'string' || ($("#subject-input").val()).trim() === '')) {
        error_count += 1;
        scroll_flag = true
        $("#subject-error").html("Title is required")
        errorStatus = true
        if (error_count == 1 && scroll_flag) {
            document.getElementById("subject-input").scrollIntoView()
        }
    }

    if ((typeof ($("#description-input").val()) != 'string' || ($("#description-input").val()).trim() === '')) {
        error_count += 1;
        scroll_flag = true
        $("#description-error").html("Description is required")
        errorStatus = true
        if (error_count == 1 && scroll_flag) {
            document.getElementById("description-input").scrollIntoView()
        }
    }

    if ($("#category").val() === 'Select') {
        error_count += 1;
        scroll_flag = true
        $("#category-error").html("Please select other value")
        if (error_count == 1 && scroll_flag) {
            document.getElementById("category").scrollIntoView()
        }
        errorStatus = true
    }

    if ($("#assign_to").val() === 'Select') {
        error_count += 1;
        scroll_flag = true
        $("#assign-to-error").html("Please select other value")
        if (error_count == 1 && scroll_flag) {
            document.getElementById("assign_to").scrollIntoView()
        }
        errorStatus = true
    }
    if ($('#assign_to').val() === "Regions Specific" && $('#regions-list').val() === "Select" || $('#regions-list').val() === "") {
        error_count += 1;
        scroll_flag = true
        $("#regions-to-error").html("Please select the regions")
        errorStatus = true
        if (error_count == 1 && scroll_flag) {
            document.getElementById("regions_region").scrollIntoView()
        }
    }
    if ($('#push_notification').is(':checked') != true && $('#in_app_notification').is(':checked') != true) {
        error_count += 1;
        scroll_flag = true
        $("#dropdown-error").html("Please select the type of notification")
        errorStatus = true
        if (error_count == 1 && scroll_flag) {
            document.getElementById("push_notification").scrollIntoView()
        }
    }
    if ($('#assign_to').val() === "Domain Specific" && $("#domain").val() === 'Select') {
        error_count += 1;
        scroll_flag = true
        $("#domain-error").html("Please select Domain")
        if (error_count == 1 && scroll_flag) {
            document.getElementById("domain").scrollIntoView()
        }
        errorStatus = true
    }
    return errorStatus
}

function regionList() {
    const value = document.getElementById("assign_to").value;
    if (value === 'Regions Specific') {
        document.getElementById("region-data-container").style.display = 'flex';
        document.getElementById("domain-data-container").style.display = 'none';
        
    }
    else if (value === 'Domain Specific') {
        document.getElementById("domain-data-container").style.display = 'flex';
        document.getElementById("region-data-container").style.display = 'none';

    }
    else {
        document.getElementById("domain-data-container").style.display = 'none';
        document.getElementById("region-data-container").style.display = 'none';
    }
}



var arrayOfChecklist = []
var checkboxes = document.querySelectorAll('input#region_list:checked')

function displayRegions() {
    arrayOfChecklist = []
    checkboxes = document.querySelectorAll('input#region_list:checked')
    for (var i = 0; i < checkboxes.length; i++) {
        arrayOfChecklist.push(checkboxes[i].value)
    }
    if (arrayOfChecklist.length != 0) {
        document.getElementById('regions-list').innerHTML = arrayOfChecklist
    }
    else {
        document.getElementById('regions-list').innerHTML = "Select"
    }
}

function getArrayOfChecklist() {
    arrayOfChecklist = []
    checkboxes = document.querySelectorAll('input#region_list:checked')
    for (var i = 0; i < checkboxes.length; i++) {
        arrayOfChecklist.push(checkboxes[i].value)
    }
    return arrayOfChecklist
}
function sendPushData() {
    var formData = new FormData()
    $("#category-error").html("")
    $("#assign-to-error").html("")
    $("#regions-to-error").html("")
    $("#subject-error").html("")
    $("#link-error").html("")
    $("#dropdown-error").html("")
    $("#description-error").html("")
    $("#domain-error").html("")
    if (!validateData()) {
        formData.append('csrfmiddlewaretoken', token)
        formData.append('subject-input', ($('#subject-input').val()).trim())
        formData.append('screens-input', $('#screens').val())
        formData.append('description-input', ($('#description-input').val()).trim())
        formData.append('category', $('#category').val())
        
        let region_list = getArrayOfChecklist()
        if ($('#assign_to').val() == "Regions Specific" && region_list.length > 0) {
            formData.append('regions', region_list)
        }
        if ($('#assign_to').val() == "Domain Specific"){
            formData.append('domain', $('#domain').val())
        }
        if ($('#assign_to').val() != "Select") {
            formData.append('assign_to', $('#assign_to').val())
        }
        formData.append('push_notification', $('#push_notification').is(':checked'))
        formData.append('inapp_notification', $('#in_app_notification').is(':checked'))

        if (uploaded_images.length > 0) {
            formData.append('image', temp_uploaded_images[0])
        }
        else {
            formData.append('image', 'images/notification-logo.png')
        }
        $('#loader_for_mfg_ev_app').show()
        $.ajax({
            url: add_new_push_notification,
            processData: false,
            contentType: false,
            type: "POST",
            dataType: 'json',
            headers: { "X-CSRFToken": token },
            data: formData,
            success: function (data) {
                const base_url = window.location.origin
                location.replace(base_url + "/administrator/notifications/view-push-notification/" + data.id)
                $('#loader_for_mfg_ev_app').hide();
            },
            error: function (error) {
                $('#loader_for_mfg_ev_app').hide();
            }
        })
    }
}

function appendDeleteContent(id, subject) {
    const delete_url = document.location.origin + `/administrator/notifications/delete_push_notification/${id}`
    const content = `
        <p class="delete-modal-text">Are you sure you want to delete <strong>${subject}</strong>?</p>
        <div class="google_maps_submit_buttons">
            <div class="google_maps_container_buttons">
                
                <button class="cancle_button" data-bs-dismiss="modal">No</button>
                &nbsp;
                <a href="${delete_url}"><button class="done_button">Yes</button></a>
            </div>
        </div>
    `
    document.getElementById('delete-modal-content').innerHTML = content
}

function previewSubject(name) {
    document.getElementById('preview_subject').innerText = name.value;
}
function previewDescription(name) {
    document.getElementById('preview_description').innerText = name.value;
}
