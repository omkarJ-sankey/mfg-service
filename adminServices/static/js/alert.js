
 function customAlert(msg){
    $('.msg_calert').text('Error: '+msg)
    $('.alert_c').addClass("show");
    $('.alert_c').removeClass("hide-custom");
    $('.alert_c').addClass("showAlert");
    setTimeout(function(){
      $('.alert_c').removeClass("show");
      $('.alert_c').addClass("hide-custom");
    },10000);
  }
  $('.close-btn-custom').click(function(){
    $('.alert_c').removeClass("show");
    $('.alert_c').addClass("hide-custom");
  });