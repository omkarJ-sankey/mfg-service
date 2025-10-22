let service;
let infowindow;
let markers = [];
let geocoder;
let lat_value;
let lng_value;
let town_value;
let postal_code_value
let backup_lat_value;
let backup_lng_value;
let backup_town_value;
let backup_postal_code_value;

function initMap() {
    if(services_data1){
        document.getElementById('lat-1').innerHTML = Number((dataToUpload.latitude).toFixed(6));
        document.getElementById('lon-1').innerHTML = Number((dataToUpload.longitude).toFixed(6));
        document.getElementById('lat-2').innerHTML = Number((dataToUpload.latitude).toFixed(6));
        document.getElementById('lon-2').innerHTML = Number((dataToUpload.longitude).toFixed(6));
        document.getElementById('town_container').innerHTML= dataToUpload.town
        document.getElementById('postal_code_container').innerHTML= dataToUpload.postal_code

                
        backup_lat_value  = dataToUpload.latitude;
        backup_lng_value  = dataToUpload.longitude;
        backup_town_value  = dataToUpload.town;
        backup_postal_code_value  = dataToUpload.postal_code;
    }
    
    const locCoordinates = new google.maps.LatLng(dataToUpload.latitude, dataToUpload.longitude);
    infowindow = new google.maps.InfoWindow();
    let map = new google.maps.Map(document.getElementById("map"), {
        center: locCoordinates,
        zoom: 15,
    });
    
    geocoder = new google.maps.Geocoder();
    map.addListener("click", (mapsMouseEvent) => {
        // Close the current InfoWindow.
        infowindow.close();
        // Create a new InfoWindow.
        infowindow = new google.maps.InfoWindow({
            position: mapsMouseEvent.latLng,
        });
        geocodeLatLng(geocoder, map, infowindow,mapsMouseEvent.latLng);
    });
    let place_postal_code = 'London'
    if (dataToUpload.postal_code.length > 0) place_postal_code = dataToUpload.postal_code
    const request = {
        query: `${place_postal_code}`,
        fields: ["name", "geometry","place_id"],
    };
    service = new google.maps.places.PlacesService(map);
    service.findPlaceFromQuery(request, (results, status) => {
        if (status === google.maps.places.PlacesServiceStatus.OK && results) {
        for (var i of results){
            createMarker(i,{lat:results[0].geometry.location.lat(),lng:results[0].geometry.location.lng()})
        }
        map.setCenter(results[0].geometry.location);
        }
    });
}

function setMapOnAll(map) {
    for (var i of markers){
        i.setMap(map)
    }
}

// Removes the markers from the map, but keeps them in the array.
function hideMarkers() {
    setMapOnAll(null);
}

// Deletes all markers in the array by removing references to them.
function deleteMarkers() {
    hideMarkers();
    markers = [];
}

function createMarker(place, co_ords) {
    deleteMarkers()
    if (!place.geometry || !place.geometry.location) return;
    const marker = new google.maps.Marker({
        map,
        position: place.geometry.location,
    });
    markers.push(marker)
    const infoWindow = new google.maps.InfoWindow({
        content: "Click the map to get Lat/Lng!",
        position: co_ords,
    });
    google.maps.event.addListener(marker, "click", () => {
        geocodeLatLng(geocoder, map, infowindow,marker.position);
        infoWindow.setContent(place.name || "");
        infoWindow.open(map);
    });
}


 // gecoder function
 function geocodeLatLng(geocoder, map, infowindow, co_ords) {
    deleteMarkers()
    const latlng = {
        lat: parseFloat(co_ords.lat()),
        lng: parseFloat(co_ords.lng()),
    };
    let map_geo = new google.maps.Map(document.getElementById("map"), {
        center: new google.maps.LatLng(co_ords.lat(), co_ords.lng()),
        zoom: 18,
    });
    map_geo.addListener("click", (mapsMouseEvent) => {
        geocodeLatLng(geocoder, map_geo, infowindow,mapsMouseEvent.latLng);
    });
    
    lat_value = Number((co_ords.lat()).toFixed(6));
    lng_value = Number((co_ords.lng()).toFixed(6));
    
    document.getElementById('lat-2').innerHTML = Number((co_ords.lat()).toFixed(6));
    document.getElementById('lon-2').innerHTML = Number((co_ords.lng()).toFixed(6));
    geocoder
    .geocode({ location: latlng })
    .then((response) => {
        if (response.results[0]) {
            for(var i=0;i<response.results[0].address_components.length;i++){
                if(response.results[0].address_components[i].types.includes('postal_code')){
                    postal_code_value = response.results[0].address_components[i].long_name
                }
                if(response.results[0].address_components[i].types.includes('postal_town')){
                    town_value = response.results[0].address_components[i].long_name
                }

            }
        const marker = new google.maps.Marker({
            position: latlng,
            map: map_geo,
        });
        google.maps.event.addListener(marker, "click", () => {
            geocodeLatLng(geocoder, map_geo, infowindow,marker.position);
        });
        
        markers.push(marker)
        infowindow.setContent(response.results[0].formatted_address);
        infowindow.open(map_geo, marker);
        } else {
        window.alert("No results found");
        }
    })
    .catch((e) => window.alert("Geocoder failed due to: " + e));
}
function findLocation(val){
    if(val.length > 1){
        $('#loader_for_mfg_ev_app').show();
        const request = {
            query: val,
            fields: ["name", "geometry","place_id"],
        };
        let place_id = ''
        service = new google.maps.places.PlacesService(map);
        
        service.findPlaceFromQuery(request, (results, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK && results) {
        
            for(var i of results){
                geocodeLatLng(geocoder, map, infowindow,i.geometry.location);
            }
            lat_value = Number((results[0].geometry.location.lat()).toFixed(6));
            lng_value = Number((results[0].geometry.location.lng()).toFixed(6));
            
            document.getElementById('lat-2').innerHTML = Number((results[0].geometry.location.lat()).toFixed(6));
            document.getElementById('lon-2').innerHTML = Number((results[0].geometry.location.lng()).toFixed(6));
            $('#loader_for_mfg_ev_app').hide();
            place_id = results[0].place_id
            map.setCenter(results[0].geometry.location);
            }
        });
    }
}
function assign_map_values(cancle){
    if (cancle){
        if(services_data1){
            town_value =backup_town_value
            postal_code_value = backup_postal_code_value
            lat_value = backup_lat_value
            lng_value = backup_lng_value
            dataToUpload.town = backup_town_value
            dataToUpload.postal_code = backup_postal_code_value
            dataToUpload.latitude = backup_lat_value
            dataToUpload.longitude = backup_lng_value
        
            document.getElementById('lat-1').innerHTML = backup_lat_value
            document.getElementById('lon-1').innerHTML = backup_lng_value;
            document.getElementById('town_container').innerHTML= backup_town_value;
            document.getElementById('postal_code_container').innerHTML= backup_postal_code_value;

        }else{
            town_value =''
            postal_code_value = ''
            lat_value = 0.0
            lng_value = 0.0
            
            dataToUpload.town = ''
            dataToUpload.postal_code = ''
            dataToUpload.latitude = 0.0
            dataToUpload.longitude = 0.0
        
            document.getElementById('lat-1').innerHTML = 'Latitude'
            document.getElementById('lon-1').innerHTML = "Longitude";
            document.getElementById('lat-2').innerHTML = '0.0';
            document.getElementById('lon-2').innerHTML = '0.0';
            document.getElementById('town_container').innerHTML= 'Enter town';
            document.getElementById('postal_code_container').innerHTML= "Enter postal code";

        }
    }else{
        document.getElementById('lat-1').innerHTML = lat_value
        document.getElementById('lon-1').innerHTML = lng_value
        document.getElementById('town_container').innerHTML= town_value
        document.getElementById('postal_code_container').innerHTML= postal_code_value

        
        dataToUpload.town = town_value
        dataToUpload.postal_code = postal_code_value
        dataToUpload.latitude = lat_value
        dataToUpload.longitude = lng_value
    }
    
            
}




