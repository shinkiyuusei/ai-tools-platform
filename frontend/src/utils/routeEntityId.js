/**
 * Route parameters arrive as strings. Keep entity IDs as strings because the
 * database uses BIGINT identifiers, which can exceed JavaScript's safe integer
 * range and be corrupted by Number().
 */
export function routeEntityId(value) {
  return String(value ?? '')
}
