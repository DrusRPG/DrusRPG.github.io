---
title: "Postava"
navGroup: "Postava"
---

<div class="character-input">
  <textarea id="character-description" rows="16" placeholder="Popis postavy..."></textarea>
  <button id="preview-character-btn">Zobrazit náhled</button>
</div>

<script src="/js/common.js"></script>
<script>
var initialParam = getQueryParam('c');
if (initialParam) {
    document.getElementById('character-description').value = base64UrlDecode(initialParam);
}
document.getElementById('character-description').addEventListener('keydown', function (e) {
    if (e.key === 'Tab') {
        e.preventDefault();
        var start = this.selectionStart, end = this.selectionEnd;
        this.value = this.value.slice(0, start) + '\t' + this.value.slice(end);
        this.selectionStart = this.selectionEnd = start + 1;
    }
});
document.getElementById('preview-character-btn').addEventListener('click', function () {
    var text = document.getElementById('character-description').value;
    var b64url = base64UrlEncode(text);
    window.location.href = '/magic/postava_nahled/?c=' + encodeURIComponent(b64url);
});
</script>
