
 function customAlertm(msg){
    $('.msg_calert').text('Error: '+msg)
    $('.alert_c').addClass("show");
    $('.alert_c').removeClass("hide-custom");
    $('.alert_c').addClass("showAlert");
    setTimeout(function(){
      $('.alert_c').removeClass("show");
      $('.alert_c').addClass("hide-custom");
    },4000);
  }
  $('.close-btn-custom').click(function(){
    $('.alert_c').removeClass("show");
    $('.alert_c').addClass("hide-custom");
  });

  var updated_image = '';
  
  function setUpdateImage(url){
    updated_image = url.includes("None") ? '' : url;
  }

  $(document).on('change', '#i_file_edit', function (event) {
    if (event.target.files) {
        const reader = new FileReader();
        reader.readAsDataURL(event.target.files[0]);
        reader.onload = (event) => {
            let url = event.target.result;
            updated_image =  url;
            $("#add_images_container_edit").html(`<div class="profile_container"><div id='discard_edit' class='discard'>x</div><img class="profile_image_" src=${url} ></div>`);
            
        }
    }

});
  async function  update(url,token,validate,id){
    const data = JSON.stringify(
    {
        full_name:$('#editScreen #first_name_edit').val()+' ' +$('#editScreen #last_name_edit').val(),
        user_name:$('#editScreen #user_name').val(),
        email:$('#editScreen #email').val(),
        role:$('#editScreen #role_two').val(),
        id:id,
        image: updated_image
    }  );
        if(validate('#editform',{
            first_name:$('#editScreen #first_name_edit').val(),
            last_name:$('#editScreen #last_name_edit').val(),
            user_name:$('#editScreen #user_name').val(),
            email:$('#editScreen #email').val(),
            role:$('#editScreen #role_two').val(),
        })){
    $('#loader_for_mfg_ev_app').show()

         await  fetch(url,{                   
                body: data, 
                headers: { "X-CSRFToken": token },
                dataType: 'json',
                method: 'POST',
            }).then(response => response.json())
            .then(data => {
                if(data.status=='true'){
                    location.reload();
                }
                else{
                    document.getElementById('user_form_errors_edit').innerHTML = `<p style="padding:3px 15px;color:red;font-size:14px;">Error - ${data.messages}</p>`
                  
                }
                $('#loader_for_mfg_ev_app').hide()
            })
            .catch((error) => {
                $('#loader_for_mfg_ev_app').hide()
                document.getElementById('user_form_errors_edit').innerHTML = `<p style="padding:3px 15px;color:red;font-size:14px;">Error - ${data.messages}</p>`
            });}
}

function approve(url, token,ids){
    $('#loader_for_mfg_ev_app').show();
 
    const filter = {
        'search':$('#search').val(),
        'flag':$('#flag').val()
    }
    const data = Array.from(ids);
    fetch(url,{
                    
        body: JSON.stringify({data:data,filter:filter}), 
        headers: { "X-CSRFToken": token },
        dataType: 'json',
        method: 'POST',
    }).then(res=>{
        location.reload();
    }).catch(err=>{
        alert(err.responseText)
    });
}

function disapprove(url, token,ids){
    $('#loader_for_mfg_ev_app').show();
    const filter = {
        'search':$('#search').val(),
        'flag':$('#flag').val()
    }
    const data = Array.from(ids);
    fetch(url,{     
        body: JSON.stringify({data:data,filter:filter}), 
        headers: { "X-CSRFToken": token },
        dataType: 'json',
        method: 'POST',
    }).then(res=>{
        location.reload();
    }).catch(err=>{
        alert(err.responseText)
    });
}
