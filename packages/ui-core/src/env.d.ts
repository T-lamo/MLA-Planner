/// <reference types="vite/client" />

interface HTMLElement {
  dispatchEvent(event: Event): boolean;
}

declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}