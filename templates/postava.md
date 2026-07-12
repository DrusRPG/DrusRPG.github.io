---
title: "Postava"
---

<div class="character-input">
  <textarea id="character-description" rows="16" placeholder="Popis postavy..."></textarea>
  <button id="preview-character-btn">Zobrazit náhled</button>
</div>

<script>
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
    var bytes = new TextEncoder().encode(text);
    var binary = '';
    bytes.forEach(function (b) { binary += String.fromCharCode(b); });
    var b64url = btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    window.location.href = '/magic/postava_nahled/?c=' + encodeURIComponent(b64url);
});
</script>
