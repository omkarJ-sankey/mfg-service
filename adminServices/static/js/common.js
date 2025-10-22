
function filterFunction(type, val) {
    let new_url = ''
    const params = new URLSearchParams(url_u);
    params.forEach(function (value, key) {
        if (key !== type) new_url += `&${key}=${value}`
    });
    if (type) window.location.href = `${window_radirect_location}?${type}=${val}${new_url}`;
}
function showLoader() {
    $('#loader_for_mfg_ev_app').show();
}

