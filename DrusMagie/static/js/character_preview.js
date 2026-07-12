function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Extract "(...)" comments from anywhere in a line: strips them out of the
// text and returns the concatenated inner contents separately.
function extractComment(text) {
    var comments = [];
    var clean = text.replace(/\s*\(([^)]*)\)/g, function (_, inner) {
        comments.push(inner);
        return '';
    }).trim();
    return { text: clean, comment: comments.join(' ') };
}
function commentHtml(comment) {
    return comment ? ' <i style="color:gray">(' + escapeHtml(comment) + ')</i>' : '';
}

// Line: a leaf entry with no children. Renders <p> at the top level, <li> when nested.
function Line(text, top, comment) {
    this.text = text;
    this.top = !!top;
    this.comment = comment || '';
}
Line.prototype.to_html = function () {
    var tag = this.top ? 'h3' : 'li';
    // Spell HTML is shared with the public school pages and may carry the
    // secret_spell class, which the site-wide reveal script force-hides -
    // strip it so a character's own sheet always shows its spells in full.
    var content = this.isSpell ? parse_spell_name(this.text).replace(/\bsecret_spell\b/g, '') : escapeHtml(this.text);
    return '<' + tag + '>' + content + commentHtml(this.comment) + '</' + tag + '>';
};

// List: a header line followed by nested content, rendered as one unit
// (top level: <h3>header</h3><ul>...</ul>, nested: <li>header<ul>...</ul></li>).
function List(header, contents, top, comment) {
    this.header = header;
    this.contents = contents || [];
    this.top = !!top;
    this.comment = comment || '';
}
List.prototype.to_html = function () {
    var openTag = this.top ? 'h3' : 'li';
    var html = '<' + openTag + '>' + escapeHtml(this.header) + commentHtml(this.comment) + (this.top ? '</' + openTag + '>' : '');
    if (this.contents.length) {
        html += '<ul>' + this.contents.map(function (c) { return c.to_html(); }).join('') + '</ul>';
    }
    if (!this.top) html += '</li>';
    return html;
};

// SpellList: like List, but header is "LABEL" or "LABEL: N" (LABEL one of the
// spell tiers) - rendered as bold label + italic gray number instead of plain text.
var SPELL_TIERS = ['základní', 'pokročilá', 'mistrovská', 'velmistrovská'];
var SPELL_TIER_DISPLAY = ['Základní', 'Pokročilá', 'Mistrovská', 'Velmistrovská'];
function normalizeTier(s) {
    return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
}
function matchSpellListHeader(text) {
    var m = /^([^:]+?)(?:\s*:\s*(\d+))?$/.exec(text.trim());
    if (!m) return null;
    var idx = SPELL_TIERS.map(normalizeTier).indexOf(normalizeTier(m[1]));
    if (idx === -1) return null;
    return { label: SPELL_TIER_DISPLAY[idx], number: m[2] };
}
function SpellList(header, contents, top, comment) {
    List.call(this, header, contents, top, comment);
    this.match = matchSpellListHeader(header);
}
SpellList.prototype = Object.create(List.prototype);
SpellList.prototype.constructor = SpellList;
SpellList.prototype.to_html = function () {
    var openTag = this.top ? 'h3' : 'li';
    var headerHtml = '<b>' + escapeHtml(this.match.label) + '</b>' +
        (this.match.number ? ' <i style="color:gray">' + escapeHtml(this.match.number) + '</i>' : '') +
        commentHtml(this.comment);
    var html = '<' + openTag + '>' + headerHtml + (this.top ? '</' + openTag + '>' : '');
    if (this.contents.length) {
        html += '<ul>' + this.contents.map(function (c) { return c.to_html(); }).join('') + '</ul>';
    }
    if (!this.top) html += '</li>';
    return html;
};
function makeListNode(header, contents, top, comment) {
    return matchSpellListHeader(header) ? new SpellList(header, contents, top, comment) : new List(header, contents, top, comment);
}

// CharacterSpells: groups consecutive top-level SpellLists that appear in ascending
// tier order (základní -> pokročilá -> mistrovská -> velmistrovská) into one <ul>,
// each tier rendered as a nested <li>.
function CharacterSpells(spellLists) {
    this.contents = spellLists.map(function (sl) { sl.top = false; return sl; });
}
CharacterSpells.prototype.to_html = function () {
    return '<ul class="spell-tier-list">' + this.contents.map(function (c) { return c.to_html(); }).join('') + '</ul>';
};
function combineSpellLists(tokens) {
    var result = [];
    var i = 0;
    while (i < tokens.length) {
        var t = tokens[i];
        if (t instanceof SpellList && t.match) {
            var run = [t];
            var lastTier = SPELL_TIER_DISPLAY.indexOf(t.match.label);
            var j = i + 1;
            while (j < tokens.length && tokens[j] instanceof SpellList && tokens[j].match &&
                SPELL_TIER_DISPLAY.indexOf(tokens[j].match.label) > lastTier) {
                lastTier = SPELL_TIER_DISPLAY.indexOf(tokens[j].match.label);
                run.push(tokens[j]);
                j++;
            }
            if (run.length > 1) {
                result.push(new CharacterSpells(run));
                i = j;
                continue;
            }
        }
        result.push(t);
        i++;
    }
    return result;
}

// LineBreak: a visual gap between two blank-line-separated blocks.
function LineBreak() {}
LineBreak.prototype.to_html = function () {
    return '<div class="character-gap"></div>';
};

// Strip a leading "- " bullet marker and/or a trailing ":" (with any
// surrounding whitespace) from a line's text.
function stripLineDecorations(text) {
    var s = text.trim();
    if (s === '-') return '';
    if (s.slice(0, 2) === '- ') s = s.slice(2).trim();
    if (s.slice(-1) === ':') s = s.slice(0, -1).trim();
    return s;
}

function parseCharacterText(text) {
    var lines = [];
    var blanks = 0;
    text.split('\n').forEach(function (raw) {
        if (raw.trim() === '') { blanks++; return; }
        var s = raw;
        var indent = 0;
        while (s.slice(0, 4) === '    ') { indent++; s = s.slice(4); }
        while (s[0] === '\t') { indent++; s = s.slice(1); }
        var parsed = extractComment(stripLineDecorations(s));
        lines.push({ indent: indent, text: parsed.text, comment: parsed.comment, gapBefore: blanks >= 2 });
        blanks = 0;
    });

    var tokens = [];
    var stack = []; // stack[i] = List node whose .contents holds items at depth i+1
    lines.forEach(function (line) {
        if (line.gapBefore) {
            stack = [];
            tokens.push(new LineBreak());
        }
        if (line.indent === 0) {
            stack = [];
            var node = makeListNode(line.text, [], true, line.comment);
            tokens.push(node);
            stack.push(node);
            return;
        }
        var level = line.indent;
        if (level > stack.length + 1) level = stack.length + 1;
        var target;
        if (level <= stack.length) {
            stack.length = level;
            target = stack[level - 1];
        } else {
            var parent = stack.length ? stack[stack.length - 1] : null;
            var lastChild = parent && parent.contents.length ? parent.contents[parent.contents.length - 1] : null;
            if (!lastChild) {
                // ponytail: no enclosing top-level line to nest under (e.g. text starts indented) -
                // fall back to a fresh top-level entry instead of crashing.
                lastChild = makeListNode(line.text, [], true, line.comment);
                tokens.push(lastChild);
                stack = [lastChild];
                return;
            }
            stack.push(lastChild);
            target = lastChild;
        }
        var newNode = makeListNode(line.text, [], false, line.comment);
        if (target instanceof SpellList) newNode.isSpell = true;
        target.contents.push(newNode);
    });

    // Collapse List nodes with no children into plain Line tokens.
    function simplify(node) {
        if (node instanceof List) {
            node.contents = node.contents.map(simplify);
            if (!node.contents.length && !node.top && !(node instanceof SpellList && node.match)) {
                var line = new Line(node.header, false, node.comment);
                line.isSpell = node.isSpell;
                return line;
            }
        }
        return node;
    }
    // Combine tier runs at every nesting level, not just the top one, so a
    // nested spell-tier header run also collapses into a CharacterSpells block.
    function combineSpellListsDeep(list) {
        list.forEach(function (t) {
            if (t instanceof List) t.contents = combineSpellListsDeep(t.contents);
        });
        return combineSpellLists(list);
    }
    return combineSpellListsDeep(tokens.map(simplify));
}

function renderCharacterHierarchy(text, container) {
    var tokens = parseCharacterText(text);
    container.innerHTML = tokens.map(function (t) { return t.to_html(); }).join('');
}

(function () {
    var params = new URLSearchParams(window.location.search);
    var b64url = params.get('c');
    var el = document.getElementById('character-text');
    if (!b64url) {
        el.textContent = 'Žádný popis postavy nebyl zadán.';
        return;
    }
    try {
        var b64 = b64url.replace(/-/g, '+').replace(/_/g, '/');
        while (b64.length % 4) b64 += '=';
        var binary = atob(b64);
        var bytes = Uint8Array.from(binary, function (c) { return c.charCodeAt(0); });
        var text = new TextDecoder().decode(bytes);

        // First non-empty line is the character's name: pull it out for the
        // title/header and parse the rest as the character body.
        var lines = text.split('\n');
        var nameIdx = lines.findIndex(function (l) { return l.trim() !== ''; });
        var name = nameIdx !== -1 ? lines[nameIdx].trim() : '';
        if (nameIdx !== -1) lines.splice(nameIdx, 1);

        if (name) {
            document.title = name;
            var titleEl = document.querySelector('.post-title');
            if (titleEl) titleEl.textContent = name;
        }
        renderCharacterHierarchy(lines.join('\n'), el);
    } catch (e) {
        el.textContent = 'Neplatný odkaz na postavu.';
    }
})();
