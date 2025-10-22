
function emailV(formid,value, id) {
    const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+$/;
    const ctrl = value;
    if (!regex.test(ctrl) || ctrl.trim().length == 0) {
        $(`${formid}> div > ${id}`).text('Invalid value')
        return false;
    }
    else {
        $(`${formid}> div > ${id}`).text('')
        return true;
    }
}

$("input#first_name").on({
    keydown: function(e) {
      if (e.which === 32)
        return false;
    },
    change: function() {
      this.value = this.value.replace(/\s/g, "");
    }
});
function restrictSpaces(id){
    let value = document.getElementById(id).value
    document.getElementById(id).value = value.replace(/\s/g, "");
}

$("input#last_name").on({
    keydown: function(e) {
      if (e.which === 32)
        return false;
    },
    change: function() {
      this.value = this.value.replace(/\s/g, "");
    }
});

function editValName(formid,value, id) {
    if (value.trim().length == 0) {

        $(`${formid}> div > ${id}`).text('Invalid value')
        return false;
    }
    else {
        $(`${formid}> div > ${id}`).text('')
        return true;
    }
}
function empty(formid,value, id) {
    const regex = /^[a-zA-Z*][a-zA-Z0-9!@#$%^&*]{3,15}$/;
    if (!regex.test(value) || value.trim().length == 0) {
        $(`${formid}> div > ${id}`).text('Invalid value')
        return false;
    } else {
        $(`${formid}> div > ${id}`).text('')
        return true;
    }
}
function password_validator(formid,value, id) {
    const regex = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,20}$/;
    if (!regex.test(value) || value.trim().length == 0) {

        $(`${formid}> div > ${id}`).text('Password must be alphanumeric and with a special character')
        return false;
    }
    else {
        $(`${formid}> div > ${id}`).text('')
        return true;
    }
}

function phone_validator(formid,value, id) {
    const regex = /^[0-9]{10,13}$/;
    if (!regex.test(value) || value.trim().length == 0 || value.length != 10) {
        $(`${formid}> div > ${id}`).text('Invalid value')
        return false;
    } else {
        $(`${formid}> div > ${id}`).text('')
        return true;
    }
}
function formValidation(formid,data){
    let isValid = [];
    if(data){
        for (const [key, value] of Object.entries(data)) {
            switch(key){
                case 'email':
                    isValid = isValid.concat(emailV(formid,value,`#${key}_err`))
                    break;
                case 'first_name':
                    isValid=isValid.concat(editValName(formid,value,`#${key}_err`))
                    break;
                case 'last_name':
                    isValid=isValid.concat(editValName(formid,value,`#${key}_err`))
                    break;
                case 'user_name':
                    isValid=isValid.concat(empty(formid,value,`#${key}_err`))
                    break;
                case 'password':
                    isValid=isValid.concat(password_validator(formid,value,`#${key}_err`))
                    break;
                case 'phone':
                    isValid=isValid.concat(phone_validator(formid,value,`#${key}_err`))
                    break;
            }
        }
    }
    return !isValid.includes(false);
}


var counter = 0;
var typingTimer;                //timer identifier
var doneTypingInterval = 1000;  //time in ms, 5 second for example
var $input = $('#search');
var isSearching = false;
$('#searchingMsg').hide();
$('#showUserDetails').show();
//user is "finished typing," do something
function doneTyping () {
    isSearching = true;
    var vals = $('#search').val();
    $('#searchingMsg').show();
    $('#showUserDetails').hide();
    filterFunction('search',vals)
}

//on keyup, start the countdown
$input.on('keyup', function () {
    clearTimeout(typingTimer);
    typingTimer = setTimeout(doneTyping, doneTypingInterval);
});

//on keydown, clear the countdown 
$input.on('keydown', function () {
    clearTimeout(typingTimer);
});



function showDownloadError(){
    $('#no_download_box').modal('show');
    setTimeout(function(){ $('#no_download_box').modal('hide'); }, 3000);
}
const password_toggler = document.getElementById('password');
const toggle = document.getElementById('toggle');

function showHidePassword() {
    if (password_toggler.type === 'password') {
        password_toggler.setAttribute('type', 'text');

    }
    else {

        password_toggler.setAttribute('type', 'password');
    }
}

$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();
});

// Navigation
$('#addButton').on('click', function () {
    $('#userMan').removeClass('active_form');
    $($('#formContainer')).addClass('active_form');
    $("#user_name").val("")
    $("#password").val("")
    $("#user_name_err").html("");
});

$('#backButton').on('click', function () {

    $('#formContainer').removeClass('active_form');
    $('#editScreen').removeClass('active_form');
    $($('#userMan')).addClass('active_form');
});
$('#cancel').on('click', () => {

    $('#formContainer').removeClass('active_form');
    $($('#userMan')).addClass('active_form');
})

// Navigation End



function goback() {
    $('#editScreen').removeClass('active_form');
    $($('#userMan')).addClass('active_form');
}
    
    function openEdit(props) {   
        function checkImage(url) {
        setUpdateImage(url);    
        if (url && url !== blob_root_url && !url.includes("None")) {
            $("#add_images_container_edit").removeAttr("hidden")
            $("#add_images_container_edit").html(`<div class="profile_container"><img class="profile_image_" src=${url} ></div>`);
        } else {
            $("#add_images_container_edit").html(` <input type="file" id="i_file_edit" name="filename" hidden accept=".jpeg,.jpg,.png"/>
    <label for="i_file_edit" class="add_images_label">Add images</label>`)
        }

    }
        var fullNameSplit = props.fullName.split(' ');
        let role_html_new = ''
        for (var i of role_list){
            if (i === `${props.role}`) role_html_new+= `<option selected value="${i}">${i}</option>`
            else role_html_new+= `<option value="${i}">${i}</option>`    
        }

        var userform = `
    <div class="custom_dialouge" role="document">

    <div class="">
        <div>
            <div class="user_management_edit_user_container" >
                <div>
                    <i id="backButton" onclick='goback()'class="arrow cursor-pointer left-arrow back_button_styl"></i>
                    <a class="user_back_navigation" id="container_heading">User details</a>
                </div>
                <div id='editbtn' class="edit_btn_container">
                    <button  style="visibility: ${ (props.id === props.reqUserId || props.status !== 'Active') ? 'hidden':'visible' };" class="delete_btn" id="delete_user_button" data-toggle="modal" data-target="#exampleModalCenter"  id="" ><svg xmlns="http://www.w3.org/2000/svg" width="16" height="19.7" viewBox="0 0 16 19.7" style="
                        color: #000                                                                                               ;
                        background: border-box;
                        "><defs><style>.a{fill:#888;}</style></defs><g transform="translate(0.003 0.001)"><path class="ab" d="M222.859,154.7a.461.461,0,0,0-.461.461v8.72a.461.461,0,1,0,.923,0v-8.72A.461.461,0,0,0,222.859,154.7Zm0,0" transform="translate(-212.141 -147.567)"></path><path class=ab d="M104.859,154.7a.461.461,0,0,0-.461.461v8.72a.461.461,0,1,0,.923,0v-8.72A.461.461,0,0,0,104.859,154.7Zm0,0" transform="translate(-99.585 -147.567)"></path><path class=ab d="M1.307,5.863V17.23a2.545,2.545,0,0,0,.677,1.755,2.272,2.272,0,0,0,1.648.713h8.729a2.271,2.271,0,0,0,1.648-.713,2.545,2.545,0,0,0,.677-1.755V5.863A1.762,1.762,0,0,0,14.234,2.4H11.872V1.821A1.812,1.812,0,0,0,10.045,0h-4.1A1.812,1.812,0,0,0,4.121,1.821V2.4H1.759a1.762,1.762,0,0,0-.452,3.466ZM12.361,18.776H3.632a1.461,1.461,0,0,1-1.4-1.546V5.9H13.764V17.23a1.461,1.461,0,0,1-1.4,1.546ZM5.044,1.821a.889.889,0,0,1,.9-.9h4.1a.889.889,0,0,1,.9.9V2.4H5.044ZM1.759,3.32H14.234a.83.83,0,1,1,0,1.661H1.759a.83.83,0,1,1,0-1.661Zm0,0" transform="translate(0 0)"></path><path class=ab d="M163.859,154.7a.461.461,0,0,0-.461.461v8.72a.461.461,0,1,0,.923,0v-8.72A.461.461,0,0,0,163.859,154.7Zm0,0" transform="translate(-155.863 -147.567)"></path></g></svg></button>
                    <button id="edit_user_button" onclick='editUser()' class="edit_user" style="width: 4rem;" id="edit" ><svg xmlns="http://www.w3.org/2000/svg" width="16" height="15.983" viewBox="0 0 16 15.983"><defs><style>.a{fill:#fff;}</style></defs><g transform="translate(0 -0.247)"><path class="a" d="M9.88,82.473l-8.8,8.8a.351.351,0,0,0-.091.161L.01,95.354a.346.346,0,0,0,.336.43.344.344,0,0,0,.084-.01L4.346,94.8a.346.346,0,0,0,.161-.091l8.8-8.8Zm0,0" transform="translate(0 -79.555)"/><path class="a" d="M338.959,1.717l-.98-.98a1.775,1.775,0,0,0-2.451,0l-1.2,1.2,3.431,3.431,1.2-1.2a1.733,1.733,0,0,0,0-2.451Zm0,0" transform="translate(-323.467 0)"/></g></svg></button>
                </div>  
             </div>
            </div>
        <div>
            <div>
                <div>
                    <div>
                        <a class="usr_detaile input_container">User Details</a>  
                    </div>
                    <div class="user_form_container">
                    <form id="editform" class="form"  >
                        ${csrf_token}
                        <div class="input_container">
                            <label class="field_lable">First Name</label>
                            <input id="first_name_edit" onkeyup="editValName('#editform',this.value,'#first_name_err'); restrictSpaces('first_name_edit');" value= ${fullNameSplit[0]} type="text" class="new_user_text_field zero_left_padding" data-lpignore="true"/>
                            <p id='first_name_err' class='error'></p>
                        </div>
                        <div class="input_container">
                            <label class="field_lable">Last Name</label>
                            <input id="last_name_edit" onkeyup="editValName('#editform',this.value,'#last_name_err'); restrictSpaces('last_name_edit');" type="text" value=${fullNameSplit[1]} class="new_user_text_field zero_left_padding"  data-lpignore="true"/>
                            <p id='last_name_err' class='error'></p>
                        </div>
                        <div class="input_container">
                            <label class="field_lable">Username</label>
                            <input style=" ${(props.reqUserId == props.id) ? 'background:#bdbdbd;' : ''}"" ${(props.reqUserId == props.id) ? 'disabled' : null}  id="user_name" onkeyup="empty('#editform',this.value,'#user_name_err')" autocomplete="off" data-lpignore="true" type="text" value=${props.userName} class="new_user_text_field zero_left_padding grey_out" />
                            <p id='user_name_err' class='error'></p>
                        </div>
                            
                        <div class="input_container">
                            <label class="field_lable">Role</label>
                            <a id="role_a_id" style="${(props.reqUserId == props.id) ? 'background:#bdbdbd;' : ''} width: 200px; font-size: 14px; padding: 5px; border-radius:4px; color: #666666">${props.role}</a>
                            <select id="role_two" style="display:none; ${(props.reqUserId == props.id) ? 'background:#bdbdbd;' : ''}" ${(props.reqUserId == props.id) ? 'disabled' : null}  value="${props.role}" class="dropdown_input_to" >
                                ${role_html_new}
                            </select>                                
                            <p id='role_err' class='error'></p>
                        </div>
                        <div class="input_container">
                            <label class="field_lable">Email</label>
                            <input onkeyup="emailV('#editform',this.value,'#email_err')" id="email" value=${props.email} type="text" class="new_user_text_field zero_left_padding" autocomplete="off" data-lpignore="true"/>
                            <p id='email_err' class='error'></p>

                        </div>
                       
                    </form>
                    
                    <div class="input_container" >
                            <label class="field_lable">Profile Picture</label>
                            <div id="add_images_container_edit">
                                <input type="file" id="i_file_edit"  name="filename" hidden accept=".jpeg,.jpg,.png"/>
                                <label for="i_file_edit" class="add_images_label view_remove_img">Add Image</label>
                            </div>
                    </div>
                        
                    <div id="user_form_errors_edit">
                                    

                    </div>
                    </div>
                    
                </div>
                <div id='editDone' class="btn_container">
                    <button  onclick="goback()" class="cancel" id="" >Cancel</button>
                    <button onclick='update("${update_user_url}","${token}",formValidation,${props.id})' class="new_user submit_new_user_data" id="done" >Submit</button>

                </div>
            </div>
        </div>
    </div>
    <div class="modal fade" id="exampleModalCenter" tabindex="-1" role="dialog" aria-labelledby="exampleModalCenterTitle" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered" role="document">
            <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="exampleModalLongTitle">Deactivate User</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body">
                Are you sure you want to deactivate <a class="bold_font">${props.fullName}</a>?
            </div>
            <div class="modal-footer">
                <button type="button" class="cancel" data-dismiss="modal">No</button>
                <button type="button" class="new_user" onclick='deactivate("${props.id}")'>Yes</button>
            </div>
            </div>
        </div>
    </div>
    </div>`


        $('#userMan').removeClass('active_form');
        $($('#editScreen')).addClass('active_form');
        $('#editScreen').html(userform);
        $('#editScreen input').prop('readonly', true)
        $('#editScreen input').css('border', 'none')
        $('#editDone').css('display', 'none')
        $("#add_images_container_edit").attr("hidden", true)
        checkImage(props.profileImage)

    }

    function editUser() {
        $("#add_images_container_edit>div").append(`<div id='discard_edit' class='discard'>x</div>`);
        document.getElementById('container_heading').innerHTML = 'Edit User'
        document.getElementById("delete_user_button").style.display = 'none';
        document.getElementById("edit_user_button").style.display = 'none';
        $('#editScreen input').prop('readonly', false)
        $('#editScreen input').css('border', '')
        $('#editDone').css('display', 'flex')
        $('#editScreen select').css('display', 'flex')
        $('#editScreen #role_a_id').css('display', 'none')
        $('#editScreen input').removeClass('zero_left_padding')
        $("#add_images_container_edit").removeAttr("hidden")
    }

    function opendEdit(props) {
        var op = requsted_user_id
        props.reqUserId = op;
        openEdit(props);
        editUser();
        $('#role_two').val(props.role);
    }

    var image = '';
    $(document).on('change', '#i_file', function (event) {
        if (event.target.files) {
            let reader = new FileReader();
            reader.readAsDataURL(event.target.files[0]);
            reader.onload = (event) => {
                let url = event.target.result;
                image = url;
                $("#add_images_container").html(`<div class="profile_container"><div id='discard' class='discard'>x</div><img class="profile_image_" src=${url} ></div>`);

            }
        }

    });


    $(document).on('click', '#discard', function (event) {
        $("#add_images_container").html(` <input type="file" id="i_file" name="filename" hidden accept=".jpeg,.jpg,.png"/>
                                    <label for="i_file" class="add_images_label">Add images</label>`);
    });

    $(document).on('click', '#discard_edit', function (event) {
        setUpdateImage('');
        $("#add_images_container_edit").html(` <input type="file" id="i_file_edit" name="filename" hidden accept=".jpeg,.jpg,.png"/>
                                    <label for="i_file_edit" class="add_images_label">Add images</label>`);
        $('#i_file_edit').val('')
    });
   
    function createUser(event) {
        const data =
        {
            full_name: $('#first_name').val() + ' ' + $('#last_name').val(),
            user_name: $('#user_name').val(),
            email: $('#email').val(),
            password: $('#password').val(),
            role: $('#role').val(),
            image: image,
        }


        if (formValidation('#userform', {
            first_name: $('#first_name').val(),
            last_name: $('#last_name').val(),
            user_name: $('#user_name').val(),
            email: $('#email').val(),
            password: $('#password').val(),
            role: $('#role').val()
        }
        )) {
            showLoader();
            $.ajax({
                url: newuser_url,
                data: { data: JSON.stringify(data) },
                headers: { "X-CSRFToken": token },
                dataType: 'json',
                type: 'POST',

                success: function (res, status) {
                    location.reload();
                },
                error: function (res) {
                    hideLoader();
                    document.getElementById('user_form_errors').innerHTML = `<p class="usr_frm_error">Error - ${JSON.parse(res.responseText).messages}</p>`
                }
            });
        }
        
    }
    function emailCheck(formid, email) {

        $.ajax({
            url: validate_email_url,
            data: { data: email },
            headers: { "X-CSRFToken": token },
            dataType: 'json',
            type: 'POST',

            success: function (res, status) {
               $(`${formid}> div > #email_err`).text('')

            },
            error: function (res) {
                $(`${formid}> div > #email_err`).text('Email already exist')
            }
        });
    }

    function checkUsername(formid, username) {
        $.ajax({
            url: validate_username_url,
            data: { data: username },
            headers: { "X-CSRFToken": token },
            dataType: 'json',
            type: 'POST',

            success: function (res, status) {
                $(`${formid}> div > #user_name_err`).text('')

            },
            error: function (res) {
                $(`${formid}> div > #user_name_err`).text('User already exist')
            }
        });
    }


    //


    function deactivate(id, status) {
        let url;
        if (status){
            if (status === 'Active' && status) url = inactivate_user_url
            else url = activate_user_url;
        }else url = inactivate_user_url
        $.ajax({
            url: url,
            data: { data: `${id}` },
            headers: { "X-CSRFToken": token },
            dataType: 'json',
            type: 'POST',
            success: function (res, status) {
                location.reload();
            },
            error: function (res) {
                customAlert(JSON.parse(res.responseText).messages);
            }
        });
    }

    $(document).ready(() => { 
        $(`#rolef option[value="${prev_role}"]`).attr('selected', 'selected');
        $(`#status option[value="${prev_status}"]`).attr('selected', 'selected');
        $("#search").val(prev_search);

    });

    function orderByFunction(type) {
        let update_order = 'Descending';
        let new_url = '';
        const keys_for_ordering = ['order_by_name', 'order_by_status', 'order_by_date', 'order_by_email', 'order_by_role'];
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

    function hideLoader() {
        $('#loader_for_mfg_ev_app').hide();
    }
    function showLoader() {
        $('#loader_for_mfg_ev_app').show();
    }
    var prevDropDownId = -1;
    function changeUserStatus(id){
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