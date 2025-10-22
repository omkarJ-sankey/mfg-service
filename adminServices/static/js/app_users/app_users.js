
const togglePhoneOrEmailField = (value) => {
    if (value) {
        if (value === "3") {
            document.getElementById("phoneInput").style.display = "block";
            document.getElementById("emailInput").style.display = "none";
            document.getElementById("phone").required = true;
            document.getElementById("country_code").required = true;
            document.getElementById("email").required = false;
        }
        else {
            document.getElementById("emailInput").style.display = "block";
            document.getElementById("phoneInput").style.display = "none";
            document.getElementById("phone").required = false;
            document.getElementById("country_code").required = false;
            document.getElementById("email").required = true;
        }
    }
}

let viewBlockedEmailListButton = document.getElementById('view-blocked-emails-button');
let viewBlockedPhoneListButton = document.getElementById('view-blocked-phones-button');
let searchBlockedListBox = document.getElementById('search-box-content');
let tableContent = document.getElementById('table-content');

const filterBlockedlist = (listData, value=null) => {
    let filteredData = (
        (value) ? listData.filter(
            data => data.toLowerCase().includes(value.toLowerCase())
        ) : listData
    )

    if (filteredData.length) return filteredData.map((data)=>`
        <li class="list-group-item font-weight-bold border border-secondary rounded-0">${data}</li>
    `).join(" ")
    return `<li class="list-group-item font-weight-bold border border-secondary rounded-0">No matching data found</li>`

}

const filterData = (type, value) => {
    if (type === 'email') {
        if (value) {
            tableContent.innerHTML = filterBlockedlist(blocked_email, value)
        }
        else {
            viewBlockedEmailListButton.classList.remove('btn-light');
            viewBlockedEmailListButton.classList.add('btn-secondary');
            viewBlockedPhoneListButton.classList.remove('btn-secondary');
            viewBlockedPhoneListButton.classList.add('btn-light');
            searchBlockedListBox.innerHTML = `
                <img src="${searchIconUrl}" >
                <input type="text" id="fname" name="fname" class="inputs w-100" value="" placeholder="Johndoe@gmail.com" onkeyup="filterData('email', this.value);">
            `;
            tableContent.innerHTML = filterBlockedlist(blocked_email);
        }
    } else {
        if (value) {
            tableContent.innerHTML = filterBlockedlist(blocked_phone_numbers, value);
        }
        else {
            viewBlockedPhoneListButton.classList.remove('btn-light');
            viewBlockedPhoneListButton.classList.add('btn-secondary');
            viewBlockedEmailListButton.classList.remove('btn-secondary');
            viewBlockedEmailListButton.classList.add('btn-light');
            searchBlockedListBox.innerHTML = `
                <img src="${searchIconUrl}" >
                <input type="text" id="fname" name="fname" class="inputs w-100" value="" placeholder="+446677887799" onkeyup="filterData('phone', this.value);">
            `;
            tableContent.innerHTML = filterBlockedlist(blocked_phone_numbers);
        }
    }
}