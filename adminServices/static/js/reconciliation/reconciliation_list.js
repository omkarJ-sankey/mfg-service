function orderByFunction(type) {
    let update_order = 'Descending';
    const params = new URLSearchParams(url_u);
    let new_url = '';
    params.forEach(function (value, key) {
        if (key !== type) new_url += `&${key}=${value}`;
        else {
            if (value === `Ascending`) update_order = 'Descending'
            else update_order = 'Ascending'
        }
    });

    document.getElementById(type).classList.toggle('order-by');
    window.location.href = `${window_radirect_location}?${type}=${update_order}${new_url}`;

}

