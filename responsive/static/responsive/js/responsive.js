(function() {
    var cookieName = 'resolution';
    var i, key, value, prevSet, cookies = document.cookie.split(";");
    function isCookieSet() {
        for (i = 0; i < cookies.length; i++) {
            key = cookies[i].substr(0, cookies[i].indexOf("="));
            value = cookies[i].substr(cookies[i].indexOf("=") + 1);
            key = key.replace(/^\s+|\s+$/g, "");
            if (key == cookieName) return true;
        }
        return false;
    }
    // Check if cookie was previously set
    prevSet = isCookieSet();
    // Set the cookie
    document.cookie = cookieName + '=' + screen.width + ':' + screen.height + '; path=/';
    // Force browser refresh if not previously set
    if (!prevSet) document.location.reload(true);
}(document, screen));


