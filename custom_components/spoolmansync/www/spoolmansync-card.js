/**
 * SpoolmanSync AMS Card
 */
console.debug("SpoolmanSync card script loading...");

class SpoolmanSyncCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.tiles = [];
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
    ].filter(t => t.id && t.id !== "");

    const trayKey = trays.map(t => t.id).join('|');

    if (!this.tiles.length || this._trayKey !== trayKey) {
      this.content.innerHTML = "";
      this.tiles.length = 0;
      this._trayKey = trayKey;
      await this.createTiles(trays);
    } else {
      this.tiles.forEach(tile => {
        tile.hass = this._hass;
      });
    }
  }

  async createTiles(trays) {
    if (!this.helpers) {
      this.helpers = await window.loadCardHelpers();
    }
    const createCardElement = this.helpers.createCardElement;
    try {
      for (const tray of trays) {
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
        this.content.appendChild(tile);
        this.tiles.push(tile);
      }
    } catch (e) {
      console.error("Error creating SpoolmanSync tiles:", e);
    }
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
    this.attachShadow({ mode: "open" });
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
    this.shadowRoot.innerHTML = `
      <style>
        .card-config {
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
      </style>
    `;

    const configDiv = document.createElement("div");
    configDiv.className = "card-config";

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
    this.shadowRoot.appendChild(configDiv);
  }

  updateHass() {
    this.shadowRoot.querySelectorAll("ha-entity-picker").forEach((picker) => {
      picker.hass = this._hass;
    });
  }

  updatePickers() {
    this.shadowRoot.querySelectorAll("ha-entity-picker").forEach((picker) => {
      const field = picker.getAttribute("data-config");
      picker.value = this._config?.[field] || "";
    });
  }
}

console.debug("SpoolmanSyncCardEditor custom element defined");

window.customCards = window.customCards || [];
window.customCards.push({
  type: "spoolmansync-card",
  name: "SpoolmanSync AMS Card",
  description: "A card to manage your SpoolmanSync AMS trays",
  preview: true,
});
console.info("%c SPOOLMANSYNC-CARD loaded", "color: white; background: #03a9f4; font-weight: 700;");
console.debug("window.customCards:", window.customCards
console.info("%c SPOOLMANSYNC-CARD loaded", "color: white; background: #03a9f4; font-weight: 700;");
