import { LitElement } from 'lit';
import { designTokens } from '../styles/tokens';

export abstract class CoreElement extends LitElement {
  // Tous les composants héritent des tokens par défaut
  static styles = [designTokens] as any;

  /**
   * Helper pour émettre des événements standards.
   * bubbles: true permet la remontée dans le DOM.
   * composed: true permet de traverser la barrière du Shadow DOM.
   */
  protected emit(name: string, detail: any) {
    this.dispatchEvent(
      new CustomEvent(name, {
        detail,
        bubbles: true,
        composed: true
      })
    );
  }
}