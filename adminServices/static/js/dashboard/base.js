
function getCookie(cname) {
    const name = cname + "=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i of ca){
        let c = i;
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
            }
            if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
            }
        }
        return "";
    }
  

function afterBulkExportRefreshPage(){
    const export_checker = setInterval(function(){
        const exported_data = getCookie('exported_data_cookie_condition');
        if (exported_data === 'True'){
            location.reload();
            clearInterval(export_checker);
        } 
    }, 3000);
}
function hideLoader() {
    $('#loader_for_mfg_ev_app').hide();
}

function showNavLoader(params,url) {
    const currentLocation = window.location.href;
    if(currentLocation.includes('update-station') || currentLocation.includes('add-station')){
        if (url) window.location.href = window.origin+url
        else window.location.href = window.origin+'/stations/'+params;
        
    }
    $('#loader_for_mfg_ev_app').show();
}

$(document).on('click', function (event) {
    if (!$(event.target).closest('.navbar_header > .right_part').length) {
        $('#dropdown-part-container').hide();
    }
});
$(window).ready(hideLoader);

function scrollPageFunction(id){
    const elmnt = document.getElementById(id);
    const top = elmnt.offsetTop;
    window.scrollTo(0, top-10);
}
$(window).scroll(function() {
    const scrollDistance = $(window).scrollTop();
    const visibleSections = $('.page-section').filter(function() {
        return $(this).is(':visible') && !$(this).is(':disabled');
    });

    visibleSections.each(function(visibleIndex) {
        if ($(this).position().top <= scrollDistance + 150) {
            $('.side_content_indicator p.active1').removeClass('active1');
            $('.side_content_indicator p').filter(function() {
                return $(this).is(':visible') && !$(this).is(':disabled');
            }).eq(visibleIndex).addClass('active1');
        }
    });
}).scroll();


function user_avatar_generator(){
    const full_name = document.getElementById('user_full_name').innerHTML;
    const name_parts = full_name.split(" ");
    const avatar_text = `${name_parts[0][0]}${name_parts[1][0]}`
    if(document.getElementById('avatar_text') && document.getElementById('avatar_text_one') ){
        document.getElementById('avatar_text').innerHTML = avatar_text
        document.getElementById('avatar_text_one').innerHTML = avatar_text

    }
    
    $('#dropdown-part-container').hide();
}
user_avatar_generator();
function showUpdatePictureModal(){
    $('#profile_picture_popup').modal('show');
}

var image;

function removeProfilePicture(){
    showLoader();
    image = "";
    uploadImage();
}

function uploadImage(){
    $.ajax({
        url:change_picture_url,     
        data: {'getdata': JSON.stringify({'image': image})}, 
        headers: { "X-CSRFToken": token },
        dataType: 'json',
        type: 'POST',  
        success: function (res, status) {
            location.reload()
        },
        error: function (res) { 
            $('#loader_for_mfg_ev_app').hide();
            customAlert('Something went wrong');                                                                                                         
        }
    });
        
}
function uploadProfilePicture(){
    $('#loader_for_mfg_ev_app').show();
    const reader = new FileReader();  
        reader.onload = (event) => {
        let url = event.target.result;
        image = url
        
        if (image) uploadImage();
        }
    reader.readAsDataURL($("#selectPicture").get(0).files[0]);
}
function toggleDropdown(){
    $('#dropdown-part-container').toggle();
}

function Previous() {
        window.history.back()
}
function showLoader() {
    $('#loader_for_mfg_ev_app').show();
}