$('#assignAmount').on('hidden.bs.modal', function (e) {
    $(this)
    .find('input').css("border-color", "#0000003d").end()
      .find("input")
         .val('')
         .end()
      .find("input[type=checkbox], input[type=radio]")
         .prop("checked", "")
         .end()
      .find('span').remove().end();
      onCancelConfirm();
  })

window.onload = () => $('tr[data-href]').on("click", function() {
    showLoader()
    document.location = $(this).data('href');
});
$(document).ready(() => { 
    $(`#rolef option[value="${prev_role}"]`).attr('selected', 'selected');
    $("#search").val(prev_search);
});
let difference =to_date_difference_from_current_date.includes('day')?-parseInt(to_date_difference_from_current_date):0
$(function() {
    $("#from_date").datepicker({ dateFormat: 'dd/mm/yy',
        showOn: "button",
        buttonImage: "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
        buttonImageOnly: true,
        buttonText: "Select date",
        maxDate: difference,
        beforeShowDay: function(date) {
            var selectedDate = $("#from_date").datepicker("getDate");
            if (selectedDate && date.getTime() === selectedDate.getTime()) {
              return [true, "highlight-selected-date", "Selected Date"];
            } else {
              return [true, "", ""];
            }
          }
    });
});
$(function() {
    $("#to_date").datepicker({ dateFormat: 'dd/mm/yy',
        showOn: "button",
        buttonImage: "https://mfgevqastorage.blob.core.windows.net/static/images/calendar-1.png",
        buttonImageOnly: true,
        buttonText: "Select date",
        minDate: $("#from_date").datepicker("getDate"),
        maxDate:0,
        beforeShowDay: function(date) {
            var selectedDate = $("#to_date").datepicker("getDate");
            if (selectedDate && date.getTime() === selectedDate.getTime()) {
              return [true, "highlight-selected-date", "Selected Date"];
            } else {
              return [true, "", ""];
            }
          }
    });
});

function showFromDatePicker(){
    $("#from_date").datepicker('show');
}
function showToDatePicker(){
    $("#to_date").datepicker('show');
}
function orderByFunction(type) {
    let update_order = 'Descending';
    let new_url = '';
    const keys_for_ordering = ['order_by_receiver', 'order_by_assigned', 'order_by_role', 'order_by_date', 'order_by_role'];
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

function validateForm(){
    const email = $("#autocomplete");
    const amount = $("#amount");
    const description = $("#description");
    const expiryDays = $("#expiryDays");
    const emailInput = email.find('input');
    const amountInput = amount.find('input');
    const descriptionInput = description.find('input');
    const expiryDaysInput = expiryDays.find('input');
    let validate = true;
    if(emailInput.length > 0 && emailInput[0].value === ''){
        email.find("span").remove();
        email.style="border-color:red;";
        email[0].appendChild(errorMsg("email not valid", 'emailError'))
        validate = false;
    }else{
        emailInput[0].style="border-color:#0000003d;";
        email.find("span").remove();
    }
    if(amountInput.length > 0 && amountInput[0].value === ''){
        amount.find("span").remove();
        amountInput[0].style="border-color:red;";
        amount[0].appendChild(errorMsg("enter valid amount", 'amountError'))
        validate = false;
    }else{
        amount.find("span").remove();
        amountInput[0].style="border-color:#0000003d;";
    }
    if(descriptionInput.length > 0 && descriptionInput[0].value === ''){
        description.find("span").remove();
        descriptionInput[0].style="border-color:red;";
        description[0].appendChild(errorMsg("enter valid description", 'descriptionError'));
        validate = false;
    }else{
        descriptionInput[0].style="border-color:#0000003d;";
        description.find("span").remove();
    }
    if(expiryDaysInput.length > 0 && expiryDaysInput[0].value === ''){
        expiryDays.find("span").remove();
        expiryDaysInput[0].style="border-color:red;";
        expiryDays[0].appendChild(errorMsg("enter valid expiry", 'expiryDaysError'));
        validate = false;
    }else{
        expiryDaysInput[0].style="border-color:#0000003d;";
        expiryDays.find("span").remove();
    }
    return validate;
}
function errorMsg(msg, id){
    const span = document.createElement("span");
    const textnode = document.createTextNode(msg);
    span.classList.add("formError")
    span.id= id;
    span.appendChild(textnode);
    return span;
}

function submitForm(){
    
    data = {};
    ['amount','username','description','userId','expiryDays'].forEach(
        value => {data[value] = document.getElementById(`${value}Input`).value}
    )
    showLoader()
    $.ajax({
        url: "/administrator/wallet/assign-amount",
        data: JSON.stringify(data),
        headers: { "X-CSRFToken": token },
        type: 'POST',

        success: function (res, status) {
            location.reload();
        },
        error: function (res) {
            hideLoader();
            customAlert(res.responseText);

        }
    });}
function checkSubmitButton(){
    data = {};
    ['amount','username','description', 'driivz', 'expiryDays'].forEach(value => {data[value] = document.getElementById(`${value}Input`).value})
    if(Object.values(data).filter(e => e === '' || e === null || e === undefined).length > 0)
    {
        document.getElementById('assign_btn').disabled = true;
    }
    else
    {
        document.getElementById('assign_btn').disabled = false;
    }
}

function makeConfirm(){
    if(!validateForm()){
        return;
    }
    $('#assignAmount')
    .find('.wallet-inputs').css("border-color", "#fff").end()
      .find("input")
         .prop("disabled", "true")
         .end()
      .find('span').remove().end()
      .find('h6').text('Do you want to confirm this voucher ?').end();
      document.getElementById('confirmSubmit').style.display='None';
      document.getElementById('finalSubmit').style.display='flex';
      document.getElementById('autocompleteSearchButton').style.display='none';
      document.getElementById('autocomplete').style.background='#fafafa';
      document.getElementById('emailInput').style.width='95%';
}
function discardConfirm(){
    $('#assignAmount')
    .find('.wallet-inputs').css("border-color", "#0000003d").end()
      .find(".user-input-txt")
         .removeAttr("disabled")
         .end()
      .find("#emailInput")
         .removeAttr("disabled")
         .end()
      .find('span').add().end()
      .find('h6').text('').end();
    document.getElementById('confirmSubmit').style.display='flex';
    document.getElementById('finalSubmit').style.display='None';
    document.getElementById('autocompleteSearchButton').style.display='block';
    document.getElementById('autocomplete').style.background='#ffffff';
    document.getElementById('emailInput').style.width='75%';
}
function onCancelConfirm(){
    $('#assignAmount')
    .find('input').css("border-color", "#0000003d").end()
      .find('span').remove().end()
      .find('h6').text('Assign Voucher').end();
      ['email','amount','description'].forEach(value => {document.getElementById(`${value}Input`).disabled = false})
      document.getElementById('confirmSubmit').style.display='flex';
      document.getElementById('finalSubmit').style.display='None';
      document.getElementById('assign_btn').disabled=true;
      document.getElementById('emailInput').style.width='75%';
}

function validateOtherData(){
    const drivze = $("#drivze");
    const receiver = $("#receiver");
    const receiverInput = receiver.find('input')
    const drivzeInput = drivze.find('input')
    let validate = true;
    if(receiverInput.length > 0 && receiverInput[0].value === ''){
        receiver.find("span").remove();
        receiverInput[0].style="border-color:red;";
        receiver[0].appendChild(errorMsg("receiver not found", 'receiverError'))
        validate = false;
    }else{
        receiverInput[0].style="border-color:#0000003d;";
        receiver.find("span").remove();
    }
    if(drivzeInput.length > 0 && drivzeInput[0].value === ''){
        drivze.find("span").remove();
        drivzeInput[0].style="border-color:red;";
        drivze[0].appendChild(errorMsg("DRIIVZ ID not found ", 'drivzeError'))
        validate = false;
    }else{
        drivze.find("span").remove();
        drivzeInput[0].style="border-color:#0000003d;";
    }
    return validate;
}
