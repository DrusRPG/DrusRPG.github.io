---
title: "Postava"
navGroup: "Postava"
---

<div class="character-input">
  <div class="character-history-controls">
    <select id="character-select">
      <option value="">(aktuální vstup)</option>
    </select>
    <select id="version-select" style="display:none;"></select>
    <button id="delete-character-btn" class="icon-btn" title="Smazat postavu" style="display:none;"><img src="/icons/character_delete.png" alt="Smazat"></button>
  </div>
  <textarea id="character-description" rows="16" placeholder="Popis postavy..."></textarea>
  <button id="preview-character-btn">Zobrazit náhled</button>
</div>

<script src="/js/common.js"></script>
<script src="/js/character.js"></script>
