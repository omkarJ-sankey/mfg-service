
var selectedItemID = 0;


disableAddAndUpdateButtons('add_amenity_button');

function addConnector(){
    $('#image_path_src').val("");
    $('#service_name').val("");
    $('#add_unique_identifier').val("");
    let error_component = document.getElementById('add_amenity_unique_id_error');
    error_component.innerHTML = '';
    $("#add_images_container").html(` <div id="d-flex flex-column"  class="mr-tp">
                    <input type="file" id="i_file"  name="filename" hidden accept=".jpeg,.jpg,.png"/>
                    <label for="i_file" class="add_images_label"><b class=" pick-img">Add Image</b</label>              
                    </div>`);
}

function updateAmenity(){
    const id = $('#conn_id').val();
    const type = $('#conn_type').val();
    const url = $('#conn_img').val();
    const url_w_text = $('#conn_img_with_text').val();
    const unique_identifier = $('#update_unique_identifier').val();
    const requestData = {
        "id":id,
        "name":type,
        "url_w_o_text":url,
        "url_w_text":url_w_text,
        "unique_identifier":unique_identifier
    };

    $('#loader_for_mfg_ev_app').show();

    $.ajax({
        url: update_amenity_url,
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(requestData),
        headers: { "X-CSRFToken": token },
        success: function (result) {
            location.reload();
        },
        error:  function (result) {
            
            $('#loader_for_mfg_ev_app').hide();
            customAlert('Please enter valid data or image with proper size'); 
        }        
    });
}


$('#add_unique_identifier').on('input', function (e) {
    setTimeout(function(){ checkUniqueIdAvailability('add_unique_identifier',
        'add_amenity_unique_id_error','add_amenity_button'); }, 200);
    
});

$('#update_unique_identifier').on('input', function (e) {
    setTimeout(function(){ checkUniqueIdAvailability('update_unique_identifier',
        'update_amenity_unique_id_error','update_amenity_button','conn_id'); }, 200);
    
});

function addAmenityDetails(){
    const name = $('#service_name').val();
    const url_w_o_text = $('#image_path_src').val();
    const url_w_text = $('#image_path_w_text_src').val();
    const unique_identifier = $('#add_unique_identifier').val();
    const requestData = {
        "service_name":name,
        "url_w_o_text":url_w_o_text,
        "url_w_text":url_w_text,
        "unique_identifier":unique_identifier
    };
    
    $('#loader_for_mfg_ev_app').show();
    $.ajax({
        url: add_amenity_url,
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(requestData),
        headers: { "X-CSRFToken": token },
        success: function (result) {
            location.reload();
        },
        error:  function (result) {
            
            $('#loader_for_mfg_ev_app').hide();
            customAlert('Please enter valid data or image with proper size'); 
        }      
    });
}
function editConnectorDetails(id, type, url, url_w_text,u_id){    
    const error_component = document.getElementById('update_amenity_unique_id_error');
    error_component.innerHTML = '';

    $("#add_images_container1").html(`<div class="profile_container">
        <div id='discard1' class='discard'>x</div>
        <img class="profile_image_ service_image" src=${group_png_url} >
    </div>`);
    $("#add_images_container1_with_text").html(`<div class="profile_container">
        <div id='discard1_with_text' class='discard'>x</div>
        <img class="profile_image_ service_image profile_image_with_text" src=${group_png_url} >
    </div>`);
    $('#conn_type').val(type);
    $('#conn_img').val(url);
    $('#conn_img_with_text').val(url_w_text);
    $('#update_unique_identifier').val(u_id);
    $('.profile_image_').attr("src",url);
    $('.profile_image_with_text').attr("src",url_w_text);
    
    $('#conn_id').val(id);
}
function switchToAmenityEditor(){   
    const type = $('.view-con-typ').html();
    const url = $('.view-con-img').attr('src');
    const img_w_text = $('.view-con-img-with-text').attr('src');
    const view_amenity_id = $('#view_amenity_id').text();
    $('#editConnector').modal('show');
    editConnectorDetails(selectedItemID,type,url,img_w_text,view_amenity_id);
}
function viewConnectorDetails(id,type,img,img_w_text,u_id){
    selectedItemID = id;
    $('.view-con-typ').html(type);
    $('.view-amenity-id').html(u_id);
    $('.view-con-img').attr("src",img);
    $('.view-con-img-with-text').attr("src",img_w_text);
}

function deleteConnector(){
    window.location.href = "/administrator/configurations/delete-amenities/"+selectedItemID+"/";   
}

$(function () {  
    // For Delete Connector 
    $(".del-con-itm-icn").click(function () {
            //get data from table row
            var id = $(this).parent().prev().prev().prev().prev().prev().prev().text();
            var name = $(this).parent().prev().prev().prev().prev().text();

            //assign to value for input box inside modal
            $("#del-con-msg").html(`Are you sure you want to remove <b>`+name+`</b> amenity?`);

            //Delete Aminity
            $("#del-amen-itm").click(function () {
                window.location.href = "/administrator/configurations/delete-amenities/"+id+"/";       
            })

        })
   
    // For View Connector Details
    // $(".view-con-itm").click(function () {
    //         //get data from table row
    //         var id = $(this).parent().prev().prev().prev().prev().prev().text();
    //         var path = $(this).parent().prev().prev().prev().prev().text();
    //         var type = $(this).parent().prev().prev().prev().text();
    //         var name = $(this).parent().prev().prev().text();
    //     })
    })

// Add and Preview Image
$(document).on('change', '#i_file' , function(event) {
 
 if (event.target.files){
   const reader = new FileReader();  
   reader.readAsDataURL(event.target.files[0]);
   reader.onload = (eventdata) => {

    let url = eventdata.target.result;

    $('#image_path_src').val(url);
   
    $("#add_images_container").html(`<div class="profile_container"><div id='discard' class='discard'>x</div><img  class="profile_image_ service_image" src=${url} ></div>`);
    
    }
    }
});

$(document).on('change', '#i_file_w_text' , function(event) {

    if (event.target.files){
        const reader = new FileReader();  
        reader.readAsDataURL(event.target.files[0]);
        reader.onload = (eventdata) => {

        let url = eventdata.target.result;

        $('#image_path_w_text_src').val(url);
        
        $("#add_images_container_w_text").html(`<div class="profile_container"><div id='discard_w_text' class='discard'>x</div><img  class="profile_image_ service_image" src=${url} ></div>`);
        
        }
    }
});

// Discard Selected Add Image
$(document).on('click', '#discard' , function(event) {
 $('#image_path_src').val("");
 $("#add_images_container").html(`<div id="d-flex flex-column"  class="mr-tp">
                    <input type="file" id="i_file"  name="filename" hidden accept=".jpeg,.jpg,.png"/>
                    <label for="i_file" class="add_images_label"><b class=" pick-img">Add Image</b</label>
                
                    </div>`);

});
$(document).on('click', '#discard_w_text' , function(event) {
 $('#image_path_src').val("");
 $("#add_images_container_w_text").html(`
 <div id="d-flex flex-column"  class="mr-tp">
 <input type="file" id="i_file_w_text"  name="filename_w_text" hidden accept=".jpeg,.jpg,.png"/>
 <label for="i_file_w_text" class="add_images_label"><strong class=" pick-img">Add Image</strong></label>
 </div>`);

});

// Discard Selected Update Image
$(document).on('click', '#discard1' , function(event) {
 $('#conn_img').val("");
 $("#add_images_container1").html(`<div id="d-flex flex-column"  class="mr-tp">
                    <input type="file" id="i_file1"  name="filename" hidden accept=".jpeg,.jpg,.png"/>
                    <label for="i_file1" class="add_images_label"><b class=" pick-img">Add Image</b</label>
                
                    </div>`);

});
$(document).on('click', '#discard1_with_text' , function(event) {
 $('#conn_img_with_text').val("");
 $("#add_images_container1_with_text").html(`<div id="d-flex flex-column"  class="mr-tp">
                    <input type="file" id="i_file1_with_text"  name="filename" hidden accept=".jpeg,.jpg,.png"/>
                    <label for="i_file1_with_text" class="add_images_label"><b class=" pick-img">Add Image</b</label>
                
                    </div>`);

});

// Update and Preview Image
$(document).on('change', '#i_file1' , function(event) {
 if (event.target.files){
   const reader = new FileReader();  
   reader.readAsDataURL(event.target.files[0]);
   reader.onload = (eventdata) => {

    let url = eventdata.target.result;

    $('#conn_img').val(url);
   
    $("#add_images_container1").html(`<div class="profile_container"><div id='discard1' class='discard'>x</div><img class="profile_image_ service_image" src=${url} ></div>`);
    
    }
    }
});
$(document).on('change', '#i_file1_with_text' , function(event) {
 if (event.target.files){
   const reader = new FileReader();  
   reader.readAsDataURL(event.target.files[0]);
   reader.onload = (eventdata) => {

    let url = eventdata.target.result;

    $('#conn_img_with_text').val(url);
   
    $("#add_images_container1_with_text").html(`<div class="profile_container"><div id='discard1_with_text' class='discard'>x</div><img class="profile_image_ service_image" src=${url} ></div>`);
    
    }
    }
});

// Tooltips
$(function () {
  $('[data-toggle="tooltip"]').tooltip()
});

function clearSelected() {
    document.getElementById('amen').classList.add('menu-item');
  }
function importData() {
  const input = document.createElement('input');
  input.type = 'file';
  input.click();
  
}
//Amenities Search
$(document).ready(function(){
  clearSelected();
});