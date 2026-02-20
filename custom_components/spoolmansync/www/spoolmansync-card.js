/**
 * SpoolmanSync AMS Card
 */
console.debug("SpoolmanSync card script loading...");

class SpoolmanSyncCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.tiles = [];
    this._tileMap = {};
    this.helpers = null;
    this._trayKey = null;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      this.render();
    }
    this.update();
  }

  setConfig(config) {
    this._config = config;
    if (this.content) {
      this.update();
    }
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        .grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
        }
      </style>
      <div class="grid"></div>
    `;
    this.content = this.shadowRoot.querySelector(".grid");
  }

  async update() {
  if (!this.content || !this._config || !this._hass) return;

  const trays = [
    { id: this._config.tray1, name: "Tray 1", color: "blue" },
    { id: this._config.tray2, name: "Tray 2", color: "orange" },
    { id: this._config.tray3, name: "Tray 3", color: "green" },
    { id: this._config.tray4, name: "Tray 4", color: "purple" }
  ].filter(t => t.id && t.id.trim() !== "");

  const trayKey = trays.map(t => t.id).sort().join('|'); // sort to make order-independent

  if (this._trayKey !== trayKey) {
    // Clear only when the set of entities actually changed
    this.content.innerHTML = "";
    this.tiles.length = 0;
    this._tileMap = {};
    this._trayKey = trayKey;
    await this.createTiles(trays);
  } else {
    // Just update hass on existing tiles
    this.tiles.forEach(tile => {
      if (tile && typeof tile.hass === 'object') {
        tile.hass = this._hass;
      }
    });
  }
}

  async createTiles(trays) {
      if (!this.helpers) {
        this.helpers = await window.loadCardHelpers();
      }
      const createCardElement = this.helpers.createCardElement;

      // 1. Collect what should exist (key = entity id)
      const desiredKeys = new Set(trays.map(t => t.id).filter(Boolean));

      // 2. Remove wrappers that are no longer wanted
      Array.from(this.content.children).forEach(child => {
        const entityId = child.getAttribute("data-spoolmansync-entity");
        if (entityId && !desiredKeys.has(entityId)) {
          child.remove();
          delete this._tileMap[entityId];
        }
      });

      // 3. Create or update wanted trays – in order
      this.tiles = []; // we'll rebuild this list

      for (const tray of trays) {
        if (!tray.id) continue;

        let entry = this._tileMap[tray.id];

        if (!entry) {
          // Create new
          const tileConfig = {
            type: "tile",
            entity: tray.id,
            name: tray.name,
            icon: "mdi:printer-3d-nozzle",
            color: tray.color,
            vertical: false,
            features_position: "bottom"
          };

          const tile = await createCardElement(tileConfig);
          tile.hass = this._hass;

          const wrapper = document.createElement("div");
          wrapper.className = "spoolmansync-tile-wrapper";
          wrapper.setAttribute("data-spoolmansync-entity", tray.id);
          wrapper.appendChild(tile);

          this.content.appendChild(wrapper);

          entry = { wrapper, tile };
          this._tileMap[tray.id] = entry;
        } else {
          // Already exists → just update hass & name/icon/color if changed
          entry.tile.hass = this._hass;

          // Optional: update tile config if name/color can change dynamically
          // (normally tile card doesn't react to these changes after creation,
          //  so you may need to recreate in that case – but usually not needed)
        }

        this.tiles.push(entry.tile);
      }

      // Optional: force layout update if grid changed
      this.content.style.display = "none";
      this.content.offsetHeight; // reflow
      this.content.style.display = "";
    }
  

  static getConfigElement() {
    return document.createElement("spoolmansync-card-editor");
  }

  static getStubConfig() {
    return { tray1: "", tray2: "", tray3: "", tray4: "" };
  }
}

customElements.define("spoolmansync-card", SpoolmanSyncCard);
console.debug("SpoolmanSyncCard custom element defined");

class SpoolmanSyncCardEditor extends HTMLElement {
  constructor() {
    super();
    // Do NOT use shadow DOM for the editor so Home Assistant editor
    // components (like `ha-entity-picker`) can render and inherit styles.
  }

  set hass(hass) {
    this._hass = hass;
    if (!this.initialized) {
      this.render();
      this.initialized = true;
    } else {
      this.updateHass();
    }
  }

  setConfig(config) {
    this._config = config;
    if (this.initialized) {
      this.updatePickers();
    }
  }

  render() {
    this.innerHTML = `
      <style>
        .card-config {
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
      </style>
      <div class="card-config"></div>
    `;

    const configDiv = this.querySelector(".card-config");

    const trays = ["tray1", "tray2", "tray3", "tray4"];
    trays.forEach((field, index) => {
      const picker = document.createElement("ha-entity-picker");
      picker.hass = this._hass;
      picker.value = this._config?.[field] || "";
      picker.label = `AMS Tray ${index + 1}`;
      picker.includeDomains = ["select"];
      picker.setAttribute("data-config", field);
      picker.addEventListener("value-changed", (ev) => {
        const value = ev.detail.value;
        const event = new CustomEvent("config-changed", {
          detail: { config: { ...this._config, [field]: value } },
          bubbles: true,
          composed: true,
        });
        this.dispatchEvent(event);
      });
      configDiv.appendChild(picker);
    });
  }

  updateHass() {
    this.querySelectorAll("ha-entity-picker").forEach((picker) => {
      picker.hass = this._hass;
    });
  }

  updatePickers() {
    this.querySelectorAll("ha-entity-picker").forEach((picker) => {
      const field = picker.getAttribute("data-config");
      picker.value = this._config?.[field] || "";
    });
  }
}

customElements.define("spoolmansync-card-editor", SpoolmanSyncCardEditor);
console.debug("SpoolmanSyncCardEditor custom element defined");

window.customCards = window.customCards || [];
window.customCards.push({
  type: "spoolmansync-card",
  name: "SpoolmanSync AMS Card",
  description: "A card to manage your SpoolmanSync AMS trays",
  preview: true,
});
console.debug("window.customCards:", window.customCards);
console.info("%c SPOOLMANSYNC-CARD loaded", "color: white; background: #03a9f4; font-weight: 700;");