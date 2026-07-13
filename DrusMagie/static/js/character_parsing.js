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
    to_html() {
        return '<div class="character-gap"></div>';
    }
}

// SpellList headers look like "LABEL" or "LABEL: N" (LABEL one of the spell
// tiers) - rendered as bold label + italic gray number instead of plain text.
const SPELL_TIERS = ['Základní', 'Pokročilá', 'Mistrovská', 'Velmistrovská'];
const SPELL_TIER_CLASS = ['tier-label-zakladni', 'tier-label-pokrocila', 'tier-label-mistrovska', 'tier-label-velmistrovska'];

// Line: a parsed line - leading "- " bullet and trailing ":" stripped, "(...)"
// comment extracted. Renders as <h3> at the top level, <li> when nested.
class Line {
    constructor(text, indent) {
        var data = Line.extractComment(Line.stripLineDecorations(text));
        this.text = data.text;
        this.comment = data.comment;
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
        if (s.slice(0, 2) === '- ') s = s.slice(2).trim();
        if (s.slice(-1) === ':') s = s.slice(0, -1).trim();
        return s;
    }

    static commentHtml(comment) {
        return comment ? ' <i style="color:gray">(' + escapeHtml(comment) + ')</i>' : '';
    }
    static normalizeTier(s) {
        return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
    }

    isSpellCategory() {
        return Line.asSpellCategory(this.text) !== null;
    }

    static asSpellCategory(text) {
        var norm_text = Line.normalizeTier(text);
        var m = /^([^:]+?)(?:\s*:\s*(\d+))?$/.exec(norm_text);
        if (!m) return null;
        var idx = SPELL_TIERS.map(Line.normalizeTier).indexOf(m[1]);
        if (idx === -1) return null;
        return { label: SPELL_TIERS[idx], number: m[2] };
    }

    spellCategoryHtml(count) {
        var m = Line.asSpellCategory(this.text);
        var tierIdx = SPELL_TIERS.indexOf(m.label);
        var number = m.number ?? count.toString();
        return '<b class="' + SPELL_TIER_CLASS[tierIdx] + '">' + escapeHtml(m.label) + '</b>' +
            (number ? ' <i style="color:gray">' + escapeHtml(number) + '</i>' : '');
    }

    to_html_default(top_level) {
        var tag = top_level ? 'h3' : 'li';
        return '<' + tag + '>' + escapeHtml(this.text) + Line.commentHtml(this.comment) + '</' + tag + '>';
    }

    to_html_spell() {
        return '<li>' + parseSpellName(this.text) + Line.commentHtml(this.comment) + '</li>';
    }

    to_html_spell_category(spell_count) {
        return this.spellCategoryHtml(spell_count);
    }


}

// ParseError: a malformed piece of input (e.g. an indented block with no
// header line above it) rendered inline instead of aborting the whole page.
class ParseError {
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
    constructor(header, block) {
        this.header = header;
        this.block = block;
        if (this.isSpellList()) {
            this.block.lines.forEach(function (l) { l.isSpell = true; });
        }
    }
    isSpellList() {
        return this.header.isSpellCategory();
    }
    to_html(top_level) {
        var tag = top_level ? 'h3' : 'li';
        var is_spell_list = this.isSpellList();
        var headerContent = is_spell_list ? this.header.to_html_spell_category(this.block.line_count()) : escapeHtml(this.header.text);
        var html = '<' + tag + '>' + headerContent + Line.commentHtml(this.header.comment) + (top_level ? '</' + tag + '>' : '');
        html += is_spell_list ? this.block.to_html_spell_list() : this.block.to_html(false);
        if (!top_level) html += '</li>';
        return html;
    }
}

// CharacterSpells: groups consecutive SpellLists (at any nesting depth) into
// one <ul class="spell-tier-list">, each tier rendered as a nested <li>.
class CharacterSpells {
    constructor(lists) {
        this.contents = lists;
    }
    to_html() {
        return '<ul class="spell-tier-list">' + this.contents.map(function (c) { return c.to_html(false); }).join('') + '</ul>';
    }
}

// IndentedBlock: turns a flat run of Line/LineBreak tokens (all sharing a
// common indent level) into the structured nodes above.
class IndentedBlock {
    constructor(tokens) {
        var rawIndents = tokens.filter(function (t) { return t instanceof Line; }).map(function (t) { return t.indent; });
        var indent = rawIndents.length ? Math.min.apply(null, rawIndents) : 0;
        tokens.forEach(function (t) { if (t instanceof Line) t.indent -= indent; });
        this.lines = IndentedBlock.combineSpellLists(IndentedBlock.processEmptySpellCategories(IndentedBlock.combineIndentedBlocksToLists(IndentedBlock.mergeIndentedBlocks(tokens))));
    }

    // Merge runs of indented lines into IndentedBlock tokens, so that the next stage can parse them as a unit instead of line-by-line.
    static mergeIndentedBlocks(tokens) {
        return createGroupsBy(tokens, function (t) { return t instanceof Line && t.indent > 0; }, function (group) { return new IndentedBlock(group); });
    }

    static combineIndentedBlocksToLists(tokens) {
        var result = [];
        for (var i = 0; i < tokens.length; i++) {
            var t1 = tokens[i];
            var t2 = tokens[i + 1] ?? null;

            if (t2 instanceof IndentedBlock) {
                if (t1 instanceof Line) {
                    result.push(new List(t1, t2));
                } else {
                    result.push(new ParseError('Odsazený seznam bez nadpisu.'));
                }
                i++;
            } else {
                result.push(t1);
            }
        }
        return result;
    }

    static processEmptySpellCategories(tokens) {
        return tokens.map(function (t) {
            if (t instanceof Line && t.isSpellCategory()) {
                return new List(t, new IndentedBlock([]));
            }
            return t;
        });
    }

    static combineSpellLists(tokens) {
        return createGroupsBy(tokens, function (t) { return t instanceof List && t.isSpellList(); }, function (group) { return new CharacterSpells(group); });
    }

    to_html(top_level, is_spell_list = false) {
        if (this.lines.length) {
            return '<ul>' + this.lines.map(function (c) {
                if (c instanceof Line) {
                    if (is_spell_list) return c.to_html_spell();
                    return c.to_html_default(top_level);
                } else {
                    // Else: List, ParseError, CharacterSpells or IndentedBlock. All just have a to_html() method, so we can just call it recursively.
                    return c.to_html(top_level);
                }
            }).join('') + '</ul>';
        }
        return "";
    }

    to_html_spell_list() {
        return this.to_html(false, true);
    }

    line_count() {
        return this.lines.length;
    }
}
