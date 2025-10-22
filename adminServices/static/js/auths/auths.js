function getCookie(cname) {
  const name = cname + "=";
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(";");
  for (var i of ca){
    let c = i;
    while (c.charAt(0) == " ") {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
  }

function setCookie(name, value, days) {
  var expires = "";
  if (days) {
    const date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    expires = "; expires=" + date.toUTCString();
  }
  document.cookie = name + "=" + (value || "") + expires + "; path=/";
}
function rememeberMeToggler() {
  if (document.getElementById("remeber_me_id").checked)
    setCookie("remember_me", "Yes");
  else setCookie("remember_me", "No", 90000);
}
function handlingRememberMeCheckbox() {
  let remeber_me_checkbox = document.getElementById("remeber_me_id");
  if (remeber_me_checkbox) {
    if (getCookie("remember_me") === "Yes") remeber_me_checkbox.checked = true;
    else remeber_me_checkbox.checked = false;
  }
}
const password = document.getElementById("password");
const toggle = document.getElementById("toggle");

  function showHidePassword(){
    password.setAttribute('type', password.type === 'password' ? 'text' : 'password')
  }
  function validateFields(val,type){
    
    const button = document.getElementById('submit_button')
    if (type === 'email'){
            const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
            const result = re.test(String(val).toLowerCase());
            if (result){ document.getElementById(`${type}_error`).innerHTML= ""
              
                button.classList.remove('disabled')
                button.removeAttribute("disabled");
                document.getElementById(`email`).style="";
             }
            else {
                button.classList.add('disabled')
                button.setAttribute("disabled",true);
                document.getElementById(`${type}_error`).innerHTML= "Please enter email in valid format";
                document.getElementById(`email`).style="border: 1px solid var(--mfg-red)";
            }
    }
    if (type === 'password'){
            const re = /^(?=.*[0-9])(?=.*[!@#$%^&*])[a-zA-Z0-9!@#$%^&*]{8,16}$/;
            
            const result = re.test(String(val).toLowerCase());
            if (result) {document.getElementById(`${type}_error`).innerHTML= ""
                button.classList.remove('disabled')
                button.removeAttribute("disabled");
                document.getElementsByClassName(`pass_container`)[0].classList.remove("enable_error_border");
                const passField = document.getElementById(`password1`);
                if(passField){
                  passField.style="";
                }
             }
            else {
                button.classList.add('disabled')
                button.setAttribute("disabled",true);
                document.getElementById(`${type}_error`).innerHTML= "Please enter password in valid format";
                document.getElementsByClassName(`pass_container`)[0].classList.add("enable_error_border");
                const passField = document.getElementById(`password1`);
                if(passField){
                  passField.style="border: 1px solid var(--mfg-red)";
                }
            }
    }
    if (type === 'otp'){
      const re = /^(\s*\d{4}\s*)(,\s*\d{4}\s*)*,?\s*$/;
            
      const result = re.test(String(val).toLowerCase());
      if (result) {document.getElementById(`${type}_error`).innerHTML= ""
                button.classList.remove('disabled')
                button.removeAttribute("disabled");
                document.getElementById(`otp`).style="";
             }
            else {
                button.classList.add('disabled');
                button.setAttribute("disabled",true);
                document.getElementById(`${type}_error`).innerHTML= "OTP must be in numbers and containing 4 numbers";   
                document.getElementById(`otp`).style="border: 1px solid var(--mfg-red)";
        }
            
    }
  }

$(document).ready(function () {
  $(".hid-box").css("top", "0px");
});

// change passowrd js
$(document).ready(function () {
  setTimeout(function () {
    $("#otp").val("");
    $("#password1").val("");
    $("#password").val("");
  }, 500);
});
// Option.html js
function resetSubmission() {
  const button = document.getElementById("submit_button");
  button.classList.remove("disabled");
  button.removeAttribute("disabled");
  document.getElementById("otp_error").innerHTML = "";
}
