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

// Compressed variants (deflate, native browser API) for the 'cz' URL param,
// used for new links so long character text doesn't hit the URI-too-long limit.
// The uncompressed 'c' param/functions above are kept so old shared links keep working.
async function base64UrlEncodeCompressed(text) {
    var bytes = new TextEncoder().encode(text);
    var cs = new CompressionStream('deflate-raw');
    var writer = cs.writable.getWriter();
    writer.write(bytes);
    writer.close();
    var compressed = new Uint8Array(await new Response(cs.readable).arrayBuffer());
    var binary = '';
    compressed.forEach(function (b) { binary += String.fromCharCode(b); });
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function base64UrlDecodeCompressed(b64url) {
    var b64 = b64url.replace(/-/g, '+').replace(/_/g, '/');
    while (b64.length % 4) b64 += '=';
    var binary = atob(b64);
    var bytes = Uint8Array.from(binary, function (c) { return c.charCodeAt(0); });
    var ds = new DecompressionStream('deflate-raw');
    var writer = ds.writable.getWriter();
    writer.write(bytes);
    writer.close();
    var decompressed = await new Response(ds.readable).arrayBuffer();
    return new TextDecoder().decode(decompressed);
}

// Reads either the compressed 'cz' param or the legacy plain 'c' param, returning
// just the decoded character text. New links are always written back as 'cz'
// (see base64UrlEncodeCompressed) — 'c' is read-only/legacy.
async function readCharacterParam() {
    var cz = getQueryParam('cz');
    if (cz) return await base64UrlDecodeCompressed(cz);
    var c = getQueryParam('c');
    if (c) return base64UrlDecode(c);
    return null;
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

function deleteCharacter(name) {
    var history = getCharacterHistory();
    delete history[name];
    localStorage.setItem('characterHistory', JSON.stringify(history));
}
