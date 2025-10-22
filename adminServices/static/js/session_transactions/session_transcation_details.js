function executePreAuth() {

  $('#loader_for_mfg_ev_app').show()
  $.ajax({
    url: collect_pre_auth_url,
    headers: { "X-CSRFToken": token },
    data: {"is_ocpi": is_ocpi}, 
    type: 'POST',
    dataType: 'json',
    success: function (res, status) {
      $('#loader_for_mfg_ev_app').hide()
      document.getElementById("preauth_status_message").innerHTML = res.message;
      if(res.status_code === 200){
        $("#preauth_status_message").addClass("alert-success")
        document.getElementById("preauth_button").classList.remove("delete_button") 
        $("#preauth_button").addClass("delete_button_disable")
        document.getElementById("preauth_button").removeAttribute("onclick")
      }
      else{
        $("#preauth_status_message").addClass("alert-danger")
      }
    },
    error: function (err) {
      $('#loader_for_mfg_ev_app').hide()
      $("#preauth_status_message").addClass("alert-danger")
      document.getElementById("preauth_status_message").innerHTML = "Failed to collect preauth";
    }
  });

}