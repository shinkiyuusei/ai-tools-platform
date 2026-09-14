/**
 * Returns the human-readable provider name supplied by the API, with the
 * stable key as a fallback for legacy rows that do not have one yet.
 */
export function providerDisplayName(provider) {
  return provider?.name || provider?.key || ''
}
