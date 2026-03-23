/**
 * Hashes a password with SHA-256 using the native Web Crypto API before
 * sending it over the wire. This ensures the plain-text password never
 * leaves the browser. The backend then applies a second layer of hashing
 * (argon2 / bcrypt) before persisting, following the "defense in depth"
 * principle.
 *
 * The same hash MUST be applied consistently on every flow that sends a
 * password to the backend (profile creation, profile update, login).
 */
export async function hashPassword(password: string): Promise<string> {
  const encoded = new TextEncoder().encode(password)
  const hashBuffer = await crypto.subtle.digest('SHA-256', encoded)
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}
