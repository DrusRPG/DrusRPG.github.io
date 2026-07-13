// Shared utilities for reading URL query params and base64url encoding/decoding
// character text, used by both postava.md and postava_nahled.md.

function getQueryParam(name) {
    return new URLSearchParams(window.location.search).get(name);
}

function base64UrlEncode(text) {
    var bytes = new TextEncoder().encode(text);
    var binary = '';
    bytes.forEach(function (b) { binary += String.fromCharCode(b); });
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64UrlDecode(b64url) {
    var b64 = b64url.replace(/-/g, '+').replace(/_/g, '/');
    while (b64.length % 4) b64 += '=';
    var binary = atob(b64);
    var bytes = Uint8Array.from(binary, function (c) { return c.charCodeAt(0); });
    return new TextDecoder().decode(bytes);
}

// Local (per-browser) version history of characters: { name: [b64url, ...] }
function getCharacterHistory() {
    try {
        return JSON.parse(localStorage.getItem('characterHistory') || '{}');
    } catch (e) {
        return {};
    }
}

function saveCharacterVersion(name, b64url) {
    if (!name) return;
    var history = getCharacterHistory();
    if (!history[name]) history[name] = [];
    history[name].push(b64url);
    localStorage.setItem('characterHistory', JSON.stringify(history));
}
