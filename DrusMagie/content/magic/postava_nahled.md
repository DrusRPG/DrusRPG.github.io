---
title: "Náhled postavy"
hiddenInHomeList: true
---

<div id="character-text" class="character-text"></div>

<script>
function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Line: a leaf entry with no children. Renders <p> at the top level, <li> when nested.
function Line(text, top) {
    this.text = text;
    this.top = !!top;
}
Line.prototype.to_html = function () {
    var tag = this.top ? 'p' : 'li';
    return '<' + tag + '>' + escapeHtml(this.text) + '</' + tag + '>';
};

// List: a header line followed by nested content, rendered as one unit
// (top level: <p>header</p><ul>...</ul>, nested: <li>header<ul>...</ul></li>).
function List(header, contents, top) {
    this.header = header;
    this.contents = contents || [];
    this.top = !!top;
}
List.prototype.to_html = function () {
    var openTag = this.top ? 'p' : 'li';
    var html = '<' + openTag + '>' + escapeHtml(this.header) + (this.top ? '</' + openTag + '>' : '');
    if (this.contents.length) {
        html += '<ul>' + this.contents.map(function (c) { return c.to_html(); }).join('') + '</ul>';
    }
    if (!this.top) html += '</li>';
    return html;
};

// SpellList: like List, but header is "LABEL" or "LABEL: N" (LABEL one of the
// spell tiers) - rendered as bold label + italic gray number instead of plain text.
var SPELL_TIERS = ['základní', 'pokročilá', 'mistrovská', 'velmistrovská'];
function matchSpellListHeader(text) {
    var m = /^(základní|pokročilá|mistrovská|velmistrovská)(?:\s*:\s*(\d+))?$/.exec(text.trim());
    if (!m) return null;
    return { label: m[1], number: m[2] };
}
function SpellList(header, contents, top) {
    List.call(this, header, contents, top);
    this.match = matchSpellListHeader(header);
}
SpellList.prototype = Object.create(List.prototype);
SpellList.prototype.constructor = SpellList;
SpellList.prototype.to_html = function () {
    var openTag = this.top ? 'p' : 'li';
    var headerHtml = '<b>' + escapeHtml(this.match.label) + '</b>' +
        (this.match.number ? ' <i style="color:gray">' + escapeHtml(this.match.number) + '</i>' : '');
    var html = '<' + openTag + '>' + headerHtml + (this.top ? '</' + openTag + '>' : '');
    if (this.contents.length) {
        html += '<ul>' + this.contents.map(function (c) { return c.to_html(); }).join('') + '</ul>';
    }
    if (!this.top) html += '</li>';
    return html;
};
function makeListNode(header, contents, top) {
    return matchSpellListHeader(header) ? new SpellList(header, contents, top) : new List(header, contents, top);
}

// LineBreak: a visual gap between two blank-line-separated blocks.
function LineBreak() {}
LineBreak.prototype.to_html = function () {
    return '<div class="character-gap"></div>';
};

function parseCharacterText(text) {
    var lines = [];
    var blanks = 0;
    text.split('\n').forEach(function (raw) {
        if (raw.trim() === '') { blanks++; return; }
        var s = raw;
        var indent = 0;
        while (s.slice(0, 4) === '    ') { indent++; s = s.slice(4); }
        while (s[0] === '\t') { indent++; s = s.slice(1); }
        lines.push({ indent: indent, text: s.trim(), gapBefore: blanks >= 2 });
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
            var node = makeListNode(line.text, [], true);
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
                lastChild = makeListNode(line.text, [], true);
                tokens.push(lastChild);
                stack = [lastChild];
                return;
            }
            stack.push(lastChild);
            target = lastChild;
        }
        target.contents.push(makeListNode(line.text, []));
    });

    // Collapse List nodes with no children into plain Line tokens.
    function simplify(node) {
        if (node instanceof List) {
            node.contents = node.contents.map(simplify);
            if (!node.contents.length && !node.top) return new Line(node.header);
        }
        return node;
    }
    return tokens.map(simplify);
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
        renderCharacterHierarchy(text, el);
    } catch (e) {
        el.textContent = 'Neplatný odkaz na postavu.';
    }
})();
</script>
