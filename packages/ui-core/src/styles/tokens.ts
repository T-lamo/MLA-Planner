import { css } from 'lit';

/**
 * Design Tokens basés sur les CSS Custom Properties.
 * Le pattern var(--public, fallback) permet au projet hôte d'injecter ses propres styles.
 */
export const designTokens = css`
  :host {
    /* Couleurs */
    --ui-primary: var(--app-primary, #3b82f6);
    --ui-primary-hover: var(--app-primary-dark, #2563eb);
    --ui-text: var(--app-text, #1e293b);
    --ui-bg: var(--app-bg, #ffffff);
    --ui-error: #ef4444;

    /* Échelle et Espacement */
    --ui-radius: var(--app-radius, 8px);
    --ui-font-sans: var(--app-font, 'Inter', system-ui, sans-serif);
    --ui-spacing-unit: 4px;
    
    /* Transitions */
    --ui-transition: 0.2s ease-in-out;
  }
`;