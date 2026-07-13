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
        var s = raw.replace(/\t/g, '    ');
        var indent = 0;
        for (var i = 0; i < s.length; i++) {
            if (s[i] === ' ') {
                indent++;
            } else {
                break;
            }
        }
        indent = Math.floor(indent / 4);

        if (blanks >= 2) tokens.push(new LineBreak());
        tokens.push(new Line(s, indent));
        blanks = 0;
    });
    return tokens;
}


async function main() {
    var el = document.getElementById('character-text');
    var text = await readCharacterParam();
    if (!text) {
        el.textContent = 'Žádný popis postavy nebyl zadán.';
        return;
    }
    try {
        // 2) Basic lexing: flat token stream of raw lines (with indent) and blank-gap
        var tokens = characterFileToTokens(text);

        // 3a) First line is the character's name: pull it out for the title/header.
        if (tokens.length == 0) {
            el.textContent = 'Neplatný odkaz na postavu, prázdný obsah.';
            return;
        }

        var name = tokens[0].text.trim();
        tokens.splice(0, 1);
        saveCharacterVersion(name, base64UrlEncode(text));
        document.title = name;
        var titleEl = document.querySelector('.post-title');
        if (titleEl) {
            titleEl.textContent = name;
            var editLink = document.createElement('a');
            editLink.href = '/magic/postava/?cz=' + encodeURIComponent(await base64UrlEncodeCompressed(text));
            editLink.className = 'edit-character-link';
            editLink.title = 'Upravit postavu';
            var editIcon = document.createElement('img');
            editIcon.src = '/icons/edit_character.png';
            editIcon.alt = 'Upravit';
            editIcon.className = 'edit-character-icon';
            editLink.appendChild(editIcon);
            titleEl.appendChild(editLink);
        }

        var block = new IndentedBlock(tokens);
        // 6) Render the whole hierarchy to HTML.
        el.innerHTML = block.to_html(true);
    } catch (e) {
        el.textContent = 'Neplatný odkaz na postavu. ' + e.toString();
        throw e;
    }
}
main();
