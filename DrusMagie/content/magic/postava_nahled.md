---
title: "Náhled postavy"
hiddenInHomeList: true
---

<p id="character-text" class="character-text"></p>

<script>
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
        el.textContent = new TextDecoder().decode(bytes);
    } catch (e) {
        el.textContent = 'Neplatný odkaz na postavu.';
    }
})();
</script>
