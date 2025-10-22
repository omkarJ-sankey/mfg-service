window.onload = function () {
  checkAssignedTo(assigned_to);
  fileTypeImageDisplayerInModal();
  mainModalAttachmentDisplayer();
  displayUserEmail();
};

//global variables
let error_count = 0;
let scroll_flag = false;
let filesArray = [];
let existingFileArrayWithUrl = lst_of_attachments_for_update_page;
let image_display_divs_in_modal = "";
var fileExtension;
let image_display_divs_in_main_page = "";
let allowed_file_types = list_of_allowed_file_types;
let update_files_total_size = 0;
let total_size_of_all_files = 0;
let total_file_size_limit_exceed_flag = false;
let old_file_size = 0;
let user_email_array = user_emails;
let view_email_container = "";

$('.footer-year').html(`${new Date().getFullYear()}`);

$(document).keydown(function (objEvent) {
  if (objEvent.keyCode == 9) {
    //tab pressed
    objEvent.preventDefault(); // stops its action
  }
});

//validations
function validateData() {
  if ($("#user_category").val() == "Select") {
    $("#assign-to-error").html("Please select other value");
    error_count += 1;
    scroll_flag = true;
    if (error_count == 1 && scroll_flag) {
      document.getElementById("user_category").scrollIntoView();
    }
  }
  if ($("#user_category").val() === "Specific Users" && !user_email_array.length) {
    $("#user-email-error").html("Please enter atleast one valid email");
    error_count += 1;
    scroll_flag = true;
    if (error_count == 1 && scroll_flag) {
      document.getElementById("user_category").scrollIntoView();
    }
  }
  if ($("#user_category").val() === "Postcode Specific" && $("#postcode-input").val().length < 2) {
    $("#postcode-error").html("This field requires atleat 2 characters");
    error_count += 1;
    scroll_flag = true;
    if (error_count == 1 && scroll_flag) {
      document.getElementById("user_category").scrollIntoView();
    }
  }
  if (
    $("#email_preference").val() === "Select"
  ) {
    $("#preference-type-error").html("Please select other value");
    error_count += 1;
    scroll_flag = true;
    if (error_count == 1 && scroll_flag) {
      document.getElementById("user_category").scrollIntoView();
    }
  }

  if (
    typeof ($("#subject-input").val()) != "string" ||
    $("#subject-input").val() === ""
  ) {
    $("#subject-error").html("This field is required");
    error_count += 1;
    scroll_flag = true;
    if (error_count == 1 && scroll_flag) {
      document.getElementById("user_category").scrollIntoView();
    }
  }

  var iframe = document.getElementsByClassName(
    "ck ck-content ck-editor__editable ck-rounded-corners ck-editor__editable_inline ck-blurred"
  )[0];
  var element = iframe.innerHTML;
  let ckeditorRegex = /^(?!\s*$)(?:<br>|<\/br>|<p>|<\/p>|&nbsp;|\s|\u200B)+$/;
  if (ckeditorRegex.test(element) || element.length == "") {
    $("#ckeditor-error").html("This field is required");
    error_count += 1;
    scroll_flag = true;
    if (error_count == 1 && scroll_flag) {
      document.getElementById("ckeditor-error").scrollIntoView();
    }
  }
  return !(error_count > 0);
}

const addUserEmail = () => {
  $("#user-email-error").html("");
  let user_email = $("#user-email-input").val().trim().toLowerCase();
  const emailRegex = /[^\s@]+@[^\s@]+\.[^\s@]+/
  if (user_email_array.includes(user_email)) {
    $("#user-email-error").html("Email already entered");
  } else if (!emailRegex.test(user_email) || user_email.length == 0) {
    $("#user-email-error").html("Please enter valid email");
  } else {
    $("#loader_for_mfg_ev_app").show();
    $.ajax({
      url: validate_user_email,
      data: JSON.stringify({
        "email": user_email,
      }),
      headers: { "X-CSRFToken": token },
      type: "POST",
      success: function (res) {
        $("#loader_for_mfg_ev_app").hide();
        if (!res.status) {
          $("#user-email-error").html(res.message);
        } else {
          $("#user-email-input").val("")
          user_email_array.push(user_email);
          displayUserEmail(user_email);
        }
      },
      error: function (_) {
        $("#loader_for_mfg_ev_app").hide();
      },
    });
  }
};
const displayUserEmail = () => {
  view_email_container = ""
  user_email_array.forEach((email, index) => {
    view_email_container += `<div class="email-div" id="email-div">
    <p id="email-para">${email}</p>
    <img src="${cross_one_icn_url}" alt="" class="remove-email-btn" id="remove-email-btn" onclick="removeUserEmail(${index})">
</div>`;
  });
  $("#emails-dispaly-div").html(view_email_container)
};

const removeUserEmail = (id) => {
  user_email_array.splice(id, 1);
  displayUserEmail();
};
// to handle the assign to type
const checkAssignedTo = (assign_to) => {
  assign_to === "Specific Users" ?
    (
      document.getElementById("email-data-container").style.display = "flex",
      document.getElementById("emails-dispaly-div").style.display = "flex"
    ) : (
      document.getElementById("email-data-container").style.display = "none",
      document.getElementById("emails-dispaly-div").style.display = "none"
    );
  assign_to === "Postcode Specific" ?
    document.getElementById("postcode-data-container").style.display = "flex" :
    document.getElementById("postcode-data-container").style.display = "none";
};

function displayAddAttachmentModal() {
  document.getElementById("attachment-modal").style.display = "block";
}
function hideAddAttachmentModal() {
  document.getElementById("attachment-modal").style.display = "none";
}

//file handling and validation of file inputs
let formData = new FormData();
const fileInput = document.getElementById("add-attachments");
fileInput.onchange = () => {
  const selectedFile = fileInput.files;
  formData.append("csrfmiddlewaretoken", token);
  old_file_size = total_size_of_all_files;
  for (i = 0; i < selectedFile.length; i++) {
    if (
      total_size_of_all_files + selectedFile[i].size >=
      email_notification_total_file_size_limit * 1000 * 1024
    ) {
      total_file_size_limit_exceed_flag = true;
      total_size_of_all_files = old_file_size;
      break;
    }
    total_size_of_all_files += selectedFile[i].size;
    fileExtension = selectedFile[i].name.substr(
      selectedFile[i].name.lastIndexOf(".") + 1
    );
    if (!list_of_allowed_file_types.includes(fileExtension.toLowerCase())) {
      error_count += 1;
      total_size_of_all_files = old_file_size;
    }
  }
  if (total_file_size_limit_exceed_flag) {
    $("#attachment-error-in-modal").html(`<p>total file size exceed 10 MB</p>`);
    total_file_size_limit_exceed_flag = false;
  } else if (error_count > 0) {
    error_count = 0;
    $("#attachment-error-in-modal").html(
      `<p>only these file type  : ${list_of_allowed_file_types}</p>`
    );
  } else {
    $("#attachment-error-in-modal").html(``);
    filesArray.push(...selectedFile);
    fileTypeImageDisplayerInModal();
  }
};

// this func remove attachments already uploaded while add
function removeAttachmentFromUpdatePage(i) {
  $("#attachment-error-in-modal").html(``);
  update_files_total_size -= existingFileArrayWithUrl[i].size;
  total_size_of_all_files -= existingFileArrayWithUrl[i].size;
  existingFileArrayWithUrl.splice(i, 1);
  fileTypeImageDisplayerInModal();
}

// this func remove attachments just added in input
function removeAttachment(i) {
  $("#attachment-error-in-modal").html(``);
  total_size_of_all_files -= filesArray[i].size;
  filesArray.splice(i, 1);
  fileTypeImageDisplayerInModal();
}

// function to display images in modal view and also to store files for main image conatiner

function fileTypeImageDisplayerInModal() {
  image_display_divs_in_modal = "";
  image_display_divs_in_main_page = "";
  existingFileDisplayer();
  for (let i = 0; i < filesArray.length; i++) {
    file_type_image = "";
    fileExtension = filesArray[i].name.substr(
      filesArray[i].name.lastIndexOf(".") + 1
    );
    if (list_of_allowed_file_types.includes(fileExtension.toLowerCase())) {
      file_type_image = getFileTypeImage(fileExtension);
    }
    if (file_type_image != "") {
      image_display_divs_in_modal += `<div class="stored_image_container"><img class="image-view" src=${file_type_image} alt=""><div class="image-view-remover-cross"><button class="image-view-remover-cross-btn" onclick="removeAttachment(${i})">+</button></div><div class="file-name-div"><p class="file-name-para">${filesArray[i].name}</p></div></div>`;
      image_display_divs_in_main_page += `<div class="stored_image_container"><img class="image-view" src=${file_type_image} alt=""><div class="file-name-div"><p class="file-name-para">${filesArray[i].name}}</p></div></div>`;
    }
  }
  total_count_of_files = existingFileArrayWithUrl.length + filesArray.length;
  if (total_count_of_files < 10) {
    $("#count-span").html(`<b>0${total_count_of_files}</b> Added`);
  } else {
    $("#count-span").html(`<b>${total_count_of_files}</b> Added`);
  }
  $("#assigned-images-container").html(image_display_divs_in_modal);
}

// function to display images in main attchment cobatiner
function mainModalAttachmentDisplayer() {
  hideAddAttachmentModal();
  $("#main-attachment-container").html(image_display_divs_in_main_page);
}
//get the icon based on file type
const getFileTypeImage = (fileExtension) => {
  if (["xls", "xlsx", "csv"].includes(fileExtension.toLowerCase())) {
    file_type_image = excel_icon;
  } else if (["png", "jpg", "jpeg"].includes(fileExtension.toLowerCase())) {
    file_type_image = image_icon;
  } else if (["doc", "docx"].includes(fileExtension.toLowerCase())) {
    file_type_image = document_icon;
  } else if (["pdf"].includes(fileExtension.toLowerCase())) {
    file_type_image = pdf_icon;
  } else {
    file_type_image = common_filetype_icon;
  }
  return file_type_image;
};
function existingFileDisplayer() {
  image_display_divs_in_modal = "";
  image_display_divs_in_main_page = "";
  if (existingFileArrayWithUrl.length > 0) {
    existingFileArrayWithUrl.forEach((file_name_url, index) => {
      update_files_total_size += file_name_url.size;
      total_size_of_all_files = update_files_total_size;
      const key = Object.keys(file_name_url)[0];
      fileExtension = file_name_url[key].substr(
        file_name_url[key].lastIndexOf(".") + 1
      );
      file_name = file_name_url[key].split("/images/")[1];
      file_type_image = getFileTypeImage(fileExtension);
      image_display_divs_in_modal += `<div class="stored_image_container"><img class="image-view" src=${file_type_image} alt=""><div class="image-view-remover-cross"><button class="image-view-remover-cross-btn" onclick="removeAttachmentFromUpdatePage(${index})">+</button></div><div class="file-name-div"><p class="file-name-para">${file_name}</p></div></div>`;
      image_display_divs_in_main_page += `<div class="stored_image_container"><img class="image-view" src=${file_type_image} alt=""><div class="file-name-div"><p class="file-name-para">${file_name}</p></div></div>`;
    });
  }
}

// func to preview email
function previewEmail() {
  var iframe = document.getElementsByClassName(
    "ck ck-content ck-editor__editable ck-rounded-corners ck-editor__editable_inline ck-blurred"
  )[0];
  var element = iframe.innerHTML;
  $(".email-custom-body").html(element);
}

// function to send data to backend if data is valid
function sendEmailData() {
  $("#assign-to-error").html("");
  $("#subject-error").html("");
  $("#preference-type-error").html("");
  if (validateData()) {
    formData.append("user_category", $("#user_category").val());
    $("#user_category").val() === "Specific Users" && formData.append("user_email_list", JSON.stringify(user_email_array))
    $("#user_category").val() === "Postcode Specific" && formData.append("postcode", $("#postcode-input").val())
    let iframe = document.getElementsByClassName(
      "ck ck-content ck-editor__editable ck-rounded-corners ck-editor__editable_inline ck-blurred"
    )[0];
    let element = iframe.innerHTML;
    for (i = 0; i < filesArray.length; i++) {
      formData.append("files", filesArray[i]);
    }
    formData.append(
      "existing_file_array_with_url",
      JSON.stringify(existingFileArrayWithUrl)
    );
    formData.append("email_subject", $("#subject-input").val());
    formData.append("custom_template_body", element);
    formData.append("email_preference", $("#email_preference").val());
    $("#loader_for_mfg_ev_app").show();
    $.ajax({
      url: add_update_new_email_notification_url,
      processData: false,
      contentType: false,
      headers: { "X-CSRFToken": token },
      data: formData,
      type: "POST",
      dataType: "json",
      success: function (data) {
        const base_url = window.location.origin;
        location.replace(
          base_url + "/administrator/notifications/view-email-notification/" + data.id
        );
      },
      error: function (_error) {
        $("#loader_for_mfg_ev_app").hide();
      },
    });
  } else {
    error_count = 0;
    scroll_flag = false;
  }
}
