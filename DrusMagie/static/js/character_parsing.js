function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}





function createGroupsBy(list, predicateFunc, createFunc) {
    const result = [];
    let i = 0;

    while (i < list.length) {
        if (!predicateFunc(list[i])) {
            result.push(list[i]);
            i++;
            continue;
        }
        // Find the end of the continuous matching range.
        const start = i;
        while (i < list.length && predicateFunc(list[i])) {
            i++;
        }
        result.push(createFunc(list.slice(start, i)));
    }
    return result;
}


// LineBreak: a visual gap between two blank-line-separated blocks.
class LineBreak {
    constructor() { }
    to_html() {
        return '<div class="character-gap"></div>';
    }
}
// SpellList: like List, but header is "LABEL" or "LABEL: N" (LABEL one of the
// spell tiers) - rendered as bold label + italic gray number instead of plain text.
const SPELL_TIERS = ['Základní', 'Pokročilá', 'Mistrovská', 'Velmistrovská'];
const SPELL_TIER_CLASS = ['tier-label-zakladni', 'tier-label-pokrocila', 'tier-label-mistrovska', 'tier-label-velmistrovska'];
class Line {
    constructor(contents, indent) {
        // Parse a string into a line: This means stripping (XX: and - XX; then extracting the comment if there is one)
        var data = extractComment(stripLineDecorations(this.contents));
        this.text = data.text;
        this.comment = data.comment
        this.indent = indent;
    }

    // Extract "(...)" comments from anywhere in a line: strips them out of the
    // text and returns the concatenated inner contents separately.
    static extractComment(text) {
        var comments = [];
        var clean = text.replace(/\s*\(([^)]*)\)/g, function (_, inner) {
            comments.push(inner);
            return '';
        }).trim();
        return { text: clean, comment: comments.join(' ') };
    }

    // Strip a leading "- " bullet marker and/or a trailing ":" (with any
    // surrounding whitespace) from a line's text.
    static stripLineDecorations(text) {
        var s = text.trim();
        if (s === '-') return '';
        if (s.slice(0, 1) === '-') s = s.slice(1).trim();
        if (s.slice(-1) === ':') s = s.slice(0, -1).trim();
        return s;
    }

    isSpellCategory() {
        return Line.asSpellCategory(this.text) !== null;
    }

    static asSpellCategory(text) {
        var norm_text = text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
        var m = /^([^:]+?)(?:\s*:\s*(\d+))?$/.exec(norm_text);
        if (!m) return null;
        var idx = SPELL_TIERS.map(normalizeTier).indexOf(normalizeTier(m[1]));
        if (idx === -1) return null;
        return { label: SPELL_TIERS[idx], number: m[2] };
    }

    static parseSpellCategory(text) {
        var m = Line.asSpellCategory(text);
        var tierIdx = SPELL_TIERS.indexOf(m.label);
        var headerHtml = '<b class="' + SPELL_TIER_CLASS[tierIdx] + '">' + escapeHtml(m.label) + '</b>' +
            (this.match.number ? ' <i style="color:gray">' + escapeHtml(m.number) + '</i>' : '') +
            commentHtml(this.comment);
        var html = '<' + openTag + '>' + headerHtml + (this.top ? '</' + openTag + '>' : '');
        if (this.contents.length) {
            html += '<ul>' + this.contents.map(function (c) { return c.to_html(); }).join('') + '</ul>';
        }
        if (!this.top) html += '</li>';
        return html;
    }

    to_html(top_level, parse_as_spell_category, parse_as_spell) {
        var tag = top_level ? 'h3' : 'li';
        var content = parse_as_spell ? parseSpellName(this.text) : (parse_as_spell_category ? parseSpellCategory(this.text) : escapeHtml(this.text));
        return '<' + tag + '>' + content + commentHtml(this.comment) + '</' + tag + '>';
    }

    static commentHtml(comment) {
        return comment ? ' <i style="color:gray">(' + escapeHtml(comment) + ')</i>' : '';
    }
}
class IndentedBlock {
    constructor(lines) {
        var indent = lines[0].indent;
        for (var i = 0; i < lines.length; i++) {
            indent = Math.min(indent, lines[i].indent);
        }
        for (var i = 0; i < lines.length; i++) {
            lines[i].indent -= indent;
        }
        this.lines = combineSpellLists(combineIndentedBlocksToLists(mergeIndentedBlocks(lines)));
        this.indent = indent;
    }

    //Merge runs of indented lines into IndentedBlock tokens, so that the next stage can parse them as a unit instead of line-by-line.
    static mergeIndentedBlocks(tokens) {
        return createGroupsBy(tokens, function (t) { return t instanceof RawLine && t.indent > 0; }, function (group) { return new IndentedBlock(group); });
    }
    static combineIndentedBlocksToLists(tokens) {
        var result = [];

        for (var i = 0; i < tokens.length; i++) {
            var t1 = tokens[i];
            var t2 = tokens[i + 1] ?? null;

            if (t2 instanceof IndentedBlock) {
                if (t1 instanceof RawLine) {
                    result.push(new List(t1.parseRawLine(), t2.lines));
                } else {
                    result.push(new Error("Odsazený seznam bez nadpisu."));
                }
                i++;
            }
            else {
                result.push(t);
            }
        }
        return result;
    }
    static combineSpellLists(tokens) {
        return createGroupsBy(tokens, function (t) { return t instanceof List && t.isSpellList(); }, function (group) { return new CharacterSpells(group); });
    }

    to_html(is_spell_list) {
        return '<ul>' + this.lines.map(function (c) { return c.to_html(false, is_spell_list); }).join('') + '</ul>';
    }
}
class Error {
    constructor(message) {
        this.message = message;
    }
    to_html() {
        return '<div class="spell-parse-error">' + escapeHtml(this.message) + '</div>';
    }
}





// List: a header line followed by nested content, rendered as one unit
// (top level: <h3>header</h3><ul>...</ul>, nested: <li>header<ul>...</ul></li>).
class List {
    constructor(header, contents) {
        this.header = header;
        this.block = new IndentedBlock(contents);
    }
    isSpellList() {
        return this.header.isSpellCategory();
    }
    to_html(top_level) {
        return this.header.to_html(top_level, false) + this.block.to_html(this.isSpellList());
    }
}


// CharacterSpells: groups consecutive top-level SpellLists that appear in ascending
// tier order (základní -> pokročilá -> mistrovská -> velmistrovská) into one <ul>,
// each tier rendered as a nested <li>.
class CharacterSpells {
    constructor(spellLists) {
        this.contents = spellLists.map(function (sl) { sl.top = false; return sl; });
    }
    to_html(top_level) {
        return '<ul class="spell-tier-list">' + this.contents.map(function (c) { return c.to_html(top_level); }).join('') + '</ul>';
    }
}







// tokens.forEach(function (t) {
//     // Indent = 0 if LineBreak, else line indent
//     var current_indent = t instanceof RawLine ? t.indent : 0;
//     // A list has ended
//     if (current_indent < last_indent) {
//         result.push(List(last_line, buildTree(indented_lines)));
//         indented_lines = [];
//         last_indent = current_indent;
//         last_line = t;
//     }




//     var parsed = extractComment(stripLineDecorations(t.contents));
//     if (t.indent === 0) {
//         stack = [];
//         var node = makeListNode(parsed.text, [], true, parsed.comment);
//         result.push(node);
//         stack.push(node);
//         return;
//     }
//     var level = t.indent;
//     if (level > stack.length + 1) level = stack.length + 1;
//     var target;
//     if (level <= stack.length) {
//         stack.length = level;
//         target = stack[level - 1];
//     } else {
//         var parent = stack.length ? stack[stack.length - 1] : null;
//         var lastChild = parent && parent.contents.length ? parent.contents[parent.contents.length - 1] : null;
//         if (!lastChild) {
//             // ponytail: no enclosing top-level line to nest under (e.g. text starts indented) -
//             // fall back to a fresh top-level entry instead of crashing.
//             lastChild = makeListNode(parsed.text, [], true, parsed.comment);
//             result.push(lastChild);
//             stack = [lastChild];
//             return;
//         }
//         stack.push(lastChild);
//         target = lastChild;
//     }
//     var newNode = makeListNode(parsed.text, [], false, parsed.comment);
//     if (target instanceof SpellList) newNode.isSpell = true;
//     target.contents.push(newNode);
// });
// return result.map(simplify);
//}


