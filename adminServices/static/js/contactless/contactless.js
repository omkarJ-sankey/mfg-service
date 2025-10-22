// function to send data to backend if data is valid
function onFileSelected() {
    const fileInput = document.getElementById("data-file");
    const fileNameSpan = document.getElementById("file-name");
    const uploadBtn = document.getElementById("upload-btn");
    if (fileInput.files.length > 0) {
        fileNameSpan.textContent = fileInput.files[0].name;
        // Enable upload if source is also selected
        uploadBtn.disabled = !document.getElementById("source-select").value;
    } else {
        fileNameSpan.textContent = "";
        uploadBtn.disabled = true;
    }
}

document.getElementById("source-select").addEventListener("change", function() {
    // Clear file input and file name when source changes
    const fileInput = document.getElementById("data-file");
    const fileNameSpan = document.getElementById("file-name");
    fileInput.value = '';
    fileNameSpan.textContent = '';
    document.getElementById("upload-btn").disabled = true;
});

function sendThirdPartyData() {
    const source = document.getElementById("source-select").value;
    const fileInput = document.getElementById("data-file");
    const dataFile = fileInput.files[0];
    const fileName = dataFile ? dataFile.name : "";
    const helperList = fileName.split(".");
    if (!source) {
        document.getElementById("error-field").textContent = "Please select a data source.";
        return;
    }
    if (!dataFile || !["xlsx", "csv"].includes(helperList[helperList.length-1])) {
        document.getElementById("error-field").textContent = "Invalid file type.";
        return;
    }
    $("#loader_for_mfg_ev_app").show();
    document.getElementById("success-field").textContent = "";
    document.getElementById("error-field").textContent = "";
    let formData = new FormData();
    formData.append("dataFile", dataFile);
    formData.append("source", source);
    formData.append("fileName", fileName);
    $.ajax({
        url: third_party_data_save_url,
        processData: false,
        contentType: false,
        headers: { "X-CSRFToken": token },
        data: formData,
        type: "POST",
        dataType: "json",
        success: function (data) {
            $("#loader_for_mfg_ev_app").hide();
            document.getElementById("success-field").textContent = data.message;
            fileInput.value = '';
            document.getElementById("file-name").textContent = '';
            document.getElementById("upload-btn").disabled = true;
        },
        error: function (error) {
            $("#loader_for_mfg_ev_app").hide();
            document.getElementById("error-field").textContent = error.responseJSON.error;
            fileInput.value = '';
            document.getElementById("file-name").textContent = '';
            document.getElementById("upload-btn").disabled = true;
        },
    });
}