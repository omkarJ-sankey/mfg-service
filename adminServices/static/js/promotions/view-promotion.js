
// logic to show checkboxes in select list
var expanded = [];

function showCheckboxes(checkboxesType) {
    if (checkboxesType) {
        const checkboxes = document.getElementById(checkboxesType);
        if (expanded.includes(checkboxesType)) {
            checkboxes.style.display = "none";
            var position = expanded.indexOf(checkboxesType)
            expanded.pop(position)
        } else {
            expanded.forEach(element => {
                var checkbx = document.getElementById(element);
                if (checkbx.style.display !== "none" || checkboxes.style.display === "block") checkbx.style.display = "none";
            });
            expanded = []
            expanded.push(checkboxesType)
            checkboxes.style.display = "block";
        }
    }
}

$(document).on('click', function (event) {
    if (!$(event.target).closest('.checkbox_select_box').length) {
        // ... clicked on the 'body', but not inside of #menutop
        const checkbox_elements = document.getElementsByClassName('checkboxes');
        for (var i of checkbox_elements) {
            i.style.display = "none";
        }
    }
});