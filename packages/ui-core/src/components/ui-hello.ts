import { html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { CoreElement } from './CoreElement';

@customElement('ui-hello')
export class UiHello extends CoreElement {
  @property({ type: String }) name = 'World';

  render() {
    return html`<span>Hello, ${this.name}!</span>`;
  }
}