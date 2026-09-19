/** HTTP or response-parsing failure. */
export class MythicMCError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = new.target.name
    this.status = status
  }
}

/** 400: invalid username or UUID. */
export class BadRequestError extends MythicMCError {}

/** 401: missing or invalid API key. */
export class AuthenticationError extends MythicMCError {}

/** 404: unknown player, board, or missing Survival statistics. */
export class NotFoundError extends MythicMCError {}

/** 429: retries exhausted or Retry-After exceeds 60 seconds. */
export class RateLimitError extends MythicMCError {
  /** Retry-After in seconds, or null when unavailable. */
  readonly retryAfter: number | null

  constructor(message: string, retryAfter: number | null) {
    super(429, message)
    this.retryAfter = retryAfter
  }
}

/** 503: unavailable data, ambiguous username, or server failure. */
export class UnavailableError extends MythicMCError {}
