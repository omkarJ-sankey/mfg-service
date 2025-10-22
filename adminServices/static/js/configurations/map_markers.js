
  
function orderByFunction(type){
    
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


var selectedItemID = 0;
var globalIndicatorType = "";
function addBrandIndicator(){
    $('#brand_image_path_src').val("");
    $('#brand_indicator_type').val("");
    $("#add_brand_indicator_images_container").html(
        `  
            <div id="d-flex flex-column"  class="mr-tp">
                <input type="file" id="brand_indicator_file"  name="brand_indicator_file" hidden accept=".jpeg,.jpg,.png"/>
                <label for="brand_indicator_file" class="add_images_label"><strong class=" pick-img">Add Image</strong></label>
            </div>
        `
    );
}

function addEVIndicator(){
    $('#ev_image_path_src').val("");
    $('#ev_indicator_type').val("");
    $("#add_ev_indicator_images_container").html(
        `  
        <div id="d-flex flex-column"  class="mr-tp">
            <input type="file" id="ev_indicator_file"  name="ev_indicator_file" hidden accept=".jpeg,.jpg,.png"/>
            <label for="ev_indicator_file" class="add_images_label"><strong class=" pick-img">Add Image</strong></label>
        </div>
        `
    );
}
function updateEVIndicator(){
    const id = $('#ev_indicator_id').val();
    const ev_indicator_type = $('#edit_ev_indicator_type').val();
    const url = $('#edit_ev_image_path_src').val();
    const requestData = {
        "id":id,
        "indicator_type":ev_indicator_type,
        "url":url,
        "type":"ev_indicator"
    };

    $('#loader_for_mfg_ev_app').show();

    $.ajax({
        url: update_indicator_url,
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

function updateBrandIndicator(){
    const id = $('#brand_indicator_id').val();
    const brand_indicator_type = $('#edit_brand_indicator_type').val();
    const url = $('#edit_brand_image_path_src').val();
    const requestData = {
        "id":id,
        "indicator_type":brand_indicator_type,
        "url":url,
        "type":"brand_indicator"
    };
    $('#loader_for_mfg_ev_app').show();
    $.ajax({
        url: update_indicator_url,
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


function addBrandIndicatorDetails(){
    const brand_indicator_type = $('#brand_indicator_type').val();
    const url = $('#brand_image_path_src').val();
    const requestData = {
        "indicator_type":brand_indicator_type,
        "url":url,
        "type":"brand_indicator"
    };
    
    $('#loader_for_mfg_ev_app').show();
    $.ajax({
        url: add_indicator_url,
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

function addEVIndicatorDetails(){
    const ev_indicator_type = $('#ev_indicator_type').val();
    const url = $('#ev_image_path_src').val();
    const requestData = {
        "indicator_type":ev_indicator_type,
        "url":url,
        "type":"ev_indicator"
    };
    
    $('#loader_for_mfg_ev_app').show();
    $.ajax({
        url: add_indicator_url,
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
function editBrandMarkerDetails(id, type, url){    

    $("#edit_brand_indicator_images_container").html(`<div class="profile_container">
                        <div id='edit_brand_indicator_discard' class='discard'>x</div>
                        <img class="profile_image_ service_image" src=${group_png_url} >
                    </div>`);
    $('#edit_brand_image_path_src').val(url);
    $('#edit_brand_indicator_type').val(type);
    $('.profile_image_').attr("src",url);
    $('#brand_indicator_id').val(id);
}
function editEVMarkerDetails(id, type, url){    

    $("#edit_ev_indicator_images_container").html(`<div class="profile_container">
                        <div id='edit_ev_indicator_discard' class='discard'>x</div>
                        <img class="profile_image_ service_image" src=${group_png_url} >
                    </div>`);
    $('#edit_ev_image_path_src').val(url);
    $('#edit_ev_indicator_type').val(type);
    $('.profile_image_').attr("src",url);
    $('#ev_indicator_id').val(id);
}
function switchToBrandAndEVEditor(){   
    const type = $('.view-con-typ').html();
    const url = $('.view-con-img').attr('src');
    if (globalIndicatorType === "brand_indicator"){

        $('#editBrandConnector').modal('show');
        editBrandMarkerDetails(selectedItemID,type,url);
    }else{
        $('#editEVConnector').modal('show');
        editEVMarkerDetails(selectedItemID,type,url);

    }
}
function viewMarkerDetails(id,type,img,indicatorType){
    selectedItemID = id;
    globalIndicatorType = indicatorType
    $('.view-con-typ').html(type);
    $('.view-amenity-id').html(indicatorType);
    $('.view-con-img').attr("src",img);
}

function deleteConnector(){
    window.location.href = "/administrator/configurations/delete-amenities/"+selectedItemID+"/";   
}

$(function () {  
    // For Delete Connector 
    $(".del-con-itm-icn").click(function () {
            //get data from table row
            var id = $(this).parent().prev().prev().prev().prev().prev().text();
            var name = $(this).parent().prev().prev().prev().text();

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


$(document).on('change', '#brand_indicator_file' , function(event) {
 
    if (event.target.files){
        const reader = new FileReader();  
        reader.readAsDataURL(event.target.files[0]);
        reader.onload = (eventdata) => {

        let url = eventdata.target.result;

        $('#brand_image_path_src').val(url);
        
        $("#add_brand_indicator_images_container").html(`<div class="profile_container"><div id='brand_indicator_discard' class='discard'>x</div><img  class="profile_image_ service_image" src=${url} ></div>`);
        
        }
    }
});
   
$(document).on('change', '#ev_indicator_file' , function(event) {
 
    if (event.target.files){
      const reader = new FileReader();  
      reader.readAsDataURL(event.target.files[0]);
      reader.onload = (eventdata) => {
   
        let url = eventdata.target.result;
   
        $('#ev_image_path_src').val(url);
        
        $("#add_ev_indicator_images_container").html(`<div class="profile_container"><div id='ev_indicator_discard' class='discard'>x</div><img  class="profile_image_ service_image" src=${url} ></div>`);
       
       }
    }
});
$(document).on('change', '#edit_brand_indicator_file' , function(event) {
 
    if (event.target.files){
        const reader = new FileReader();  
        reader.readAsDataURL(event.target.files[0]);
        reader.onload = (eventdata) => {

        let url = eventdata.target.result;

        $('#edit_brand_image_path_src').val(url);
        
        $("#edit_brand_indicator_images_container").html(`<div class="profile_container"><div id='edit_brand_indicator_discard' class='discard'>x</div><img  class="profile_image_ service_image" src=${url} ></div>`);
        
        }
    }
});
   
$(document).on('change', '#edit_ev_indicator_file' , function(event) {
 
    if (event.target.files){
      const reader = new FileReader();  
      reader.readAsDataURL(event.target.files[0]);
      reader.onload = (eventdata) => {
   
        let url = eventdata.target.result;
   
        $('#edit_ev_image_path_src').val(url);
        
        $("#edit_ev_indicator_images_container").html(`<div class="profile_container"><div id='edit_ev_indicator_discard' class='discard'>x</div><img  class="profile_image_ service_image" src=${url} ></div>`);
       
       }
    }
});


// Discard Selected Add Image
$(document).on('click', '#brand_indicator_discard' , function(event) {
    $('#brand_image_path_src').val("");
    $("#add_brand_indicator_images_container").html(
        `  
            <div id="d-flex flex-column"  class="mr-tp">
                <input type="file" id="brand_indicator_file"  name="brand_indicator_file" hidden accept=".jpeg,.jpg,.png"/>
                <label for="brand_indicator_file" class="add_images_label"><strong class=" pick-img">Add Image</strong></label>
            </div>
        `
    );
});
// Discard Selected Add Image
$(document).on('click', '#ev_indicator_discard' , function(event) {
    $('#ev_image_path_src').val("");
    $("#add_ev_indicator_images_container").html(
        `  
        <div id="d-flex flex-column"  class="mr-tp">
            <input type="file" id="ev_indicator_file"  name="ev_indicator_file" hidden accept=".jpeg,.jpg,.png"/>
            <label for="ev_indicator_file" class="add_images_label"><strong class=" pick-img">Add Image</strong></label>
        </div>
        `
    );
});
// Discard Selected Add Image
$(document).on('click', '#edit_brand_indicator_discard' , function(event) {
    $('#edit_brand_image_path_src').val("");
    $("#edit_brand_indicator_images_container").html(
        `  
            <div id="d-flex flex-column"  class="mr-tp">
                <input type="file" id="edit_brand_indicator_file"  name="edit_brand_indicator_file" hidden accept=".jpeg,.jpg,.png"/>
                <label for="edit_brand_indicator_file" class="add_images_label"><strong class=" pick-img">Add Image</strong></label>
            </div>
        `
    );
});
// Discard Selected Add Image
$(document).on('click', '#edit_ev_indicator_discard' , function(event) {
    $('#edit_ev_image_path_src').val("");
    $("#edit_ev_indicator_images_container").html(
        `  
        <div id="d-flex flex-column"  class="mr-tp">
            <input type="file" id="edit_ev_indicator_file"  name="edit_ev_indicator_file" hidden accept=".jpeg,.jpg,.png"/>
            <label for="edit_ev_indicator_file" class="add_images_label"><strong class=" pick-img">Add Image</strong></label>
        </div>
        `
    );
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

// Tooltips
$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})

function clearSelected() {
    document.getElementById('map_indicator').classList.add('menu-item');
  }
function importData() {
  const input = document.createElement('input');
  input.type = 'file';
  input.click();
  
}
//Amenities Search
$(document).ready(function (){
  clearSelected();
});