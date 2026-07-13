(async function () {

var text = await readCharacterParam();
if (text) {
    document.getElementById('character-description').value = text;
}

var characterHistory = getCharacterHistory();
var characterSelect = document.getElementById('character-select');
var versionSelect = document.getElementById('version-select');

function firstLineName(text) {
    return (text.split('\n')[0] || '').trim();
}

function addCharacterOption(name) {
    var opt = document.createElement('option');
    opt.value = name;
    opt.textContent = name;
    characterSelect.appendChild(opt);
}

Object.keys(characterHistory).sort().forEach(addCharacterOption);

function populateVersions(name) {
    versionSelect.innerHTML = '';
    var versions = characterHistory[name] || [];
    versions.forEach(function (b64url, i) {
        var opt = document.createElement('option');
        opt.value = b64url;
        opt.textContent = 'v' + (i + 1);
        versionSelect.appendChild(opt);
    });
    versionSelect.style.display = versions.length ? '' : 'none';
}

characterSelect.addEventListener('change', function () {
    var name = characterSelect.value;
    if (!name) {
        versionSelect.style.display = 'none';
        return;
    }
    populateVersions(name);
    if (versionSelect.options.length) {
        versionSelect.selectedIndex = versionSelect.options.length - 1;
        versionSelect.dispatchEvent(new Event('change'));
    }
});

versionSelect.addEventListener('change', function () {
    var textarea = document.getElementById('character-description');
    var currentText = textarea.value;
    var currentName = firstLineName(currentText);
    var selectedName = characterSelect.value;
    if (currentText && currentName && currentName !== selectedName) {
        saveCharacterVersion(currentName, base64UrlEncode(currentText));
        characterHistory = getCharacterHistory();
        if (!Array.from(characterSelect.options).some(function (o) { return o.value === currentName; })) {
            addCharacterOption(currentName);
        }
    }
    textarea.value = base64UrlDecode(versionSelect.value);
});

var descriptionTextarea = document.getElementById('character-description');
function fitTextareaToViewport() {
    descriptionTextarea.style.height = 'auto';
    var maxHeight = window.innerHeight - descriptionTextarea.getBoundingClientRect().top - 250;
    descriptionTextarea.style.height = Math.max(200, maxHeight) + 'px';
}
window.addEventListener('resize', fitTextareaToViewport);
fitTextareaToViewport();

document.getElementById('character-description').addEventListener('keydown', function (e) {
    if (e.key !== 'Tab') return;
    e.preventDefault();
    var start = this.selectionStart, end = this.selectionEnd;

    if (start === end) {
        if (e.shiftKey) return;
        this.value = this.value.slice(0, start) + '\t' + this.value.slice(end);
        this.selectionStart = this.selectionEnd = start + 1;
        return;
    }

    var lineStart = this.value.lastIndexOf('\n', start - 1) + 1;
    var lineEndSearch = this.value.indexOf('\n', end);
    var lineEnd = lineEndSearch === -1 ? this.value.length : lineEndSearch;
    var block = this.value.slice(lineStart, lineEnd);
    var lines = block.split('\n');

    if (e.shiftKey) {
        var removedFirstLine = 0, totalRemoved = 0;
        lines = lines.map(function (line, i) {
            var removed;
            if (line[0] === '\t') {
                removed = 1;
            } else {
                removed = 0;
                while (removed < 4 && line[removed] === ' ') removed++;
            }
            if (i === 0) removedFirstLine = removed;
            totalRemoved += removed;
            return line.slice(removed);
        });
        var newBlock = lines.join('\n');
        this.value = this.value.slice(0, lineStart) + newBlock + this.value.slice(lineEnd);
        this.selectionStart = Math.max(lineStart, start - removedFirstLine);
        this.selectionEnd = Math.max(this.selectionStart, end - totalRemoved);
    } else {
        var newBlock = lines.join('\n\t');
        newBlock = '\t' + newBlock;
        this.value = this.value.slice(0, lineStart) + newBlock + this.value.slice(lineEnd);
        this.selectionStart = start + 1;
        this.selectionEnd = end + lines.length;
    }
});
document.getElementById('preview-character-btn').addEventListener('click', async function () {
    var text = document.getElementById('character-description').value;
    var b64url = await base64UrlEncodeCompressed(text);
    window.location.href = '/magic/postava_nahled/?cz=' + encodeURIComponent(b64url);
});

})();
