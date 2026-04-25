import { html, css, type CSSResultGroup } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { CoreElement } from './CoreElement';

@customElement('ui-login')
export class UiLogin extends CoreElement {
  // --- Textes Customisables (Props) ---
  @property({ type: String }) submitLabel = 'Se connecter';
  @property({ type: String }) loadingLabel = 'Connexion en cours...';
  
  @property({ type: String }) identifierLabel = "Nom d'utilisateur ou Email";
  @property({ type: String }) identifierPlaceholder = "Entrez votre identifiant";
  
  @property({ type: String }) passwordLabel = "Mot de passe";
  @property({ type: String }) passwordPlaceholder = "••••••••";

  // --- Compte démo pré-rempli ---
  @property({ type: String }) defaultIdentifier = "";
  @property({ type: String }) defaultPassword = "";

  // --- Gestion des erreurs et états ---
  @property({ type: String }) errorMessage = "";
  @state() private isLoading = false;
  @state() private showPassword = false;

  static override styles: CSSResultGroup = [
    ...(CoreElement.styles as any[]), 
    css`
      :host {
        display: block;
        width: 100%;
        box-sizing: border-box;
        animation: fadeIn 0.5s ease-out;
      }

      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }

      .login-card {
        max-width: var(--ui-login-max-width, 400px);
        margin: var(--ui-login-margin, 0 auto); 
        padding: 2rem;
        background: var(--ui-bg, #ffffff);
        border: 1px solid #e2e8f0;
        border-radius: var(--ui-radius, 8px);
        box-shadow: var(--ui-shadow, 0 4px 6px -1px rgb(0 0 0 / 0.1));
        font-family: var(--ui-font-sans, sans-serif);
        color: var(--ui-text, #1e293b);
        transition: all 0.3s ease;
      }

      .logo-slot {
        margin-bottom: 1.5rem;
        text-align: center;
      }

      .logo-slot ::slotted(*) {
        display: block;
      }

      .form-group { margin-bottom: 1.25rem; }
      
      label {
        display: block;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
      }

      input {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        box-sizing: border-box;
        font-size: 1rem;
        transition: all 0.2s;
      }

      input:focus {
        outline: none;
        border-color: var(--ui-primary, #2563eb);
        box-shadow: 0 0 0 3px var(--ui-primary-soft, rgba(37, 99, 235, 0.1));
      }

      .password-wrapper {
        position: relative;
      }

      .password-wrapper input {
        padding-right: 2.75rem;
      }

      .password-toggle {
        position: absolute;
        right: 0.75rem;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        padding: 0;
        width: auto;
        cursor: pointer;
        color: #94a3b8;
        display: flex;
        align-items: center;
        transition: color 0.15s ease;
      }

      .password-toggle:hover:not(:disabled) {
        background: none;
        color: #475569;
      }

      .password-toggle:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }

      .error-banner {
        background-color: #fef2f2;
        color: #dc2626;
        padding: 0.75rem;
        border-radius: 6px;
        font-size: 0.875rem;
        margin-bottom: 1.25rem;
        border: 1px solid #fee2e2;
        display: flex;
        align-items: center;
        animation: shake 0.4s ease-in-out;
      }

      @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-4px); }
        75% { transform: translateX(4px); }
      }

      button {
        width: 100%;
        padding: 0.875rem;
        background: var(--ui-primary, #2563eb);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      button:hover:not(:disabled) { 
        background: var(--ui-primary-hover, #1d4ed8);
      }

      button:disabled { 
        opacity: 0.7; 
        cursor: not-allowed; 
      }

      .demo-banner {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 6px;
        padding: 0.625rem 0.875rem;
        margin-bottom: 1.25rem;
        font-size: 0.8125rem;
        color: #15803d;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
      }

      .demo-banner span { font-weight: 600; }

      .demo-fill-btn {
        width: auto;
        padding: 0.25rem 0.625rem;
        font-size: 0.75rem;
        font-weight: 600;
        background: #16a34a;
        border-radius: 4px;
        color: white;
        border: none;
        cursor: pointer;
        flex-shrink: 0;
      }

      .demo-fill-btn:hover:not(:disabled) { background: #15803d; }

      @media (max-width: 640px) {
        .login-card {
          padding: 1.5rem;
          max-width: var(--ui-login-mobile-max-width, 100%);
        }
      }
    `
  ];

  private _fillDemo = () => {
    const form = this.shadowRoot?.querySelector('form');
    if (!form) return;
    const idInput = form.querySelector<HTMLInputElement>('input[name="identifier"]');
    const pwInput = form.querySelector<HTMLInputElement>('input[name="password"]');
    if (idInput) idInput.value = this.defaultIdentifier;
    if (pwInput) pwInput.value = this.defaultPassword;
  };

  private _handleSubmit = async (e: Event) => {
    e.preventDefault();
    if (this.isLoading) return;

    this.isLoading = true;
    this.errorMessage = ""; // Reset de l'erreur au clic
    
    const formData = new FormData(e.target as HTMLFormElement);
    const data = Object.fromEntries(formData.entries());

    this.emit('auth-submit', { 
      ...data,
      timestamp: Date.now() 
    });

    // Note: Dans un cas réel, c'est Nuxt qui passera isLoading à false
    // via une prop si tu décides de contrôler l'état depuis le parent.
    setTimeout(() => { this.isLoading = false; }, 1500);
  };

  override render() {
    return html`
      <div class="login-card">
        <div class="logo-slot">
          <slot name="logo"></slot>
        </div>

        ${this.defaultIdentifier
          ? html`<div class="demo-banner">
              <span>🎭 Compte démo : ${this.defaultIdentifier} / ${this.defaultPassword}</span>
              <button type="button" class="demo-fill-btn" @click=${this._fillDemo}>Utiliser</button>
            </div>`
          : ''
        }

        <form @submit=${this._handleSubmit}>
          <div class="form-group">
            <label>${this.identifierLabel}</label>
            <input
              name="identifier"
              type="text"
              placeholder=${this.identifierPlaceholder}
              required
              ?disabled=${this.isLoading}
              autocomplete="username"
            >
          </div>

          <div class="form-group">
            <label>${this.passwordLabel}</label>
            <div class="password-wrapper">
              <input
                name="password"
                type=${this.showPassword ? 'text' : 'password'}
                placeholder=${this.passwordPlaceholder}
                required
                ?disabled=${this.isLoading}
                autocomplete="current-password"
              >
              <button
                type="button"
                class="password-toggle"
                ?disabled=${this.isLoading}
                aria-label=${this.showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                @click=${() => { this.showPassword = !this.showPassword; }}
              >
                ${this.showPassword
                  ? html`<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`
                  : html`<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`
                }
              </button>
            </div>
          </div>

          ${this.errorMessage
            ? html`<div class="error-banner">${this.errorMessage}</div>`
            : ''
          }

          <button type="submit" ?disabled=${this.isLoading}>
            ${this.isLoading ? this.loadingLabel : this.submitLabel}
          </button>
        </form>
      </div>
    `;
  }
}