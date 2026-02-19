/**
 * SpoolmanSync AMS Card
 */
class SpoolmanSyncCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      this.render();
    } else {
      this.update();
    }
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
    this.update();
  }

  async update() {
    if (!this.content || !this._config || !this._hass) return;

    this.content.innerHTML = "";

    const trays = [
      { id: this._config.tray1, name: "Tray 1", color: "blue" },
      { id: this._config.tray2, name: "Tray 2", color: "orange" },
      { id: this._config.tray3, name: "Tray 3", color: "green" },
      { id: this._config.tray4, name: "Tray 4", color: "purple" }
    ].filter(t => t.id && t.id !== "");

    try {
      const helpers = await window.loadCardHelpers();
      const createCardElement = helpers.createCardElement;
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
      }
    } catch (e) {
      console.error("Error rendering SpoolmanSync tiles:", e);
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
    }
  }

  setConfig(config) {
    this._config = config;
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
      <div class="card-config">
        <ha-entity-picker
          .hass=${this._hass}
          .value="${this._config?.tray1 || ""}"
          .label="AMS Tray 1"
          .includeDomains=${['select']}
          data-config="tray1"
        ></ha-entity-picker>
        <ha-entity-picker
          .hass=${this._hass}
          .value="${this._config?.tray2 || ""}"
          .label="AMS Tray 2"
          .includeDomains=${['select']}
          data-config="tray2"
        ></ha-entity-picker>
        <ha-entity-picker
          .hass=${this._hass}
          .value="${this._config?.tray3 || ""}"
          .label="AMS Tray 3"
          .includeDomains=${['select']}
          data-config="tray3"
        ></ha-entity-picker>
        <ha-entity-picker
          .hass=${this._hass}
          .value="${this._config?.tray4 || ""}"
          .label="AMS Tray 4"
          .includeDomains=${['select']}
          data-config="tray4"
        ></ha-entity-picker>
      </div>
    `;
    
    this.shadowRoot.querySelectorAll("ha-entity-picker").forEach(picker => {
      picker.addEventListener("value-changed", (ev) => {
        const field = picker.getAttribute("data-config");
        const value = ev.detail.value;
        const event = new CustomEvent("config-changed", {
          detail: { config: { ...this._config, [field]: value } },
          bubbles: true,
          composed: true,
        });
        this.dispatchEvent(event);
      });
    });
  }
}

customElements.define("spoolmansync-card-editor", SpoolmanSyncCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "spoolmansync-card",
  name: "SpoolmanSync AMS Card",
  description: "A card to manage your SpoolmanSync AMS trays",
  preview: true,
});

console.info(
  "%c SPOOLMANSYNC-CARD %c 1.2.3 ",
  "color: white; background: #03a9f4; font-weight: 700;",
  "color: #03a9f4; background: white; font-weight: 700;"
);
