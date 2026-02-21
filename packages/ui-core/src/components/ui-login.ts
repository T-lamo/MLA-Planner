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

  // --- Gestion des erreurs et états ---
  @property({ type: String }) errorMessage = "";
  @state() private isLoading = false;

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

      .logo-slot ::slotted(*) {
        max-height: 60px;
        margin-bottom: 1.5rem;
        display: block;
        text-align: center;
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

      @media (max-width: 640px) {
        .login-card {
          padding: 1.5rem;
          max-width: var(--ui-login-mobile-max-width, 100%);
        }
      }
    `
  ];

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

        ${this.errorMessage 
          ? html`<div class="error-banner">${this.errorMessage}</div>` 
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
            <input 
              name="password"
              type="password" 
              placeholder=${this.passwordPlaceholder}
              required 
              ?disabled=${this.isLoading}
              autocomplete="current-password"
            >
          </div>
          
          <button type="submit" ?disabled=${this.isLoading}>
            ${this.isLoading ? this.loadingLabel : this.submitLabel}
          </button>
        </form>
      </div>
    `;
  }
}