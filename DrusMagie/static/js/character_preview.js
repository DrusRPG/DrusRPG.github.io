// 1) Decode the base64url-encoded character text from the URL param.
function decodeCharacterFile(b64url) {
    var b64 = b64url.replace(/-/g, '+').replace(/_/g, '/');
    while (b64.length % 4) b64 += '=';
    var binary = atob(b64);
    var bytes = Uint8Array.from(binary, function (c) { return c.charCodeAt(0); });
    return new TextDecoder().decode(bytes);
}

// 2) Basic lexing: flat token stream of raw lines (with indent) and blank-gap
// markers. No structure, no comment/decoration parsing yet.
function characterFileToTokens(text) {
    var tokens = [];
    var blanks = 0;
    text.split('\n').forEach(function (raw) {
        if (raw.trim() === '') {
            if (tokens.length != 0) {
                blanks++;
            }
            return;
        }
        var s = raw.replace('\t', '    ');
        var indent = 0;
        for (var i = 0; i < s.length; i++) {
            if (s[i] === ' ') {
                indent++;
            } else {
                break;
            }
        }
        indent = Math.ceil(indent / 4);

        if (blanks >= 2) tokens.push(new LineBreak());
        tokens.push(new RawLine(s, indent));
        blanks = 0;
    });
    return tokens;
}


function main() {
    var params = new URLSearchParams(window.location.search);
    var b64url = params.get('c');
    var el = document.getElementById('character-text');
    if (!b64url) {
        el.textContent = 'Žádný popis postavy nebyl zadán.';
        return;
    }
    try {
        var text = decodeCharacterFile(b64url);
        // 2) Basic lexing: flat token stream of raw lines (with indent) and blank-gap
        var tokens = characterFileToTokens(text);

        // 3a) First line is the character's name: pull it out for the title/header.
        if (tokens.length == 0) {
            el.textContent = 'Neplatný odkaz na postavu, prázdný obsah.';
            return;
        }

        var name = tokens[0];
        tokens.splice(0, 1);
        document.title = name;
        var titleEl = document.querySelector('.post-title');
        if (titleEl) titleEl.textContent = name;

        var tree = new List(null, tokens);
        // 6) Render the whole hierarchy to HTML.
        el.innerHTML = tree.to_html();
    } catch (e) {
        el.textContent = 'Neplatný odkaz na postavu.';
    }
}
main();
