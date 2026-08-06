/**
 * Answer options are stored with their positional letter baked in ("A. Paris")
 * — the exam UI and every seeded question assume it. Forms edit the bare text,
 * so the prefix is stripped on load and re-applied on save.
 *
 * The backend normalizes too (see `question_service.normalize_options`); this
 * exists so the form doesn't show the user a letter they didn't type and can't
 * meaningfully edit.
 */
export const OPTION_KEYS = ['A', 'B', 'C', 'D'] as const

export type OptionKey = (typeof OPTION_KEYS)[number]

const OPTION_PREFIX = /^[A-D]\.\s*/

/** Remove a leading "A. " so the form edits only the answer text. */
export function stripOptionPrefix(option: string): string {
  return option.replace(OPTION_PREFIX, '')
}

/** Re-apply the positional prefix. Index decides the letter, not the old text. */
export function applyOptionPrefix(option: string, index: number): string {
  const key = OPTION_KEYS[index] ?? ''
  return key ? `${key}. ${stripOptionPrefix(option)}` : stripOptionPrefix(option)
}

/** Pad or trim to exactly four bare options, for a fixed 4-input form. */
export function toFormOptions(options: string[] = []): string[] {
  const bare = options.map(stripOptionPrefix)
  while (bare.length < OPTION_KEYS.length) bare.push('')
  return bare.slice(0, OPTION_KEYS.length)
}

/** Turn the form's four bare inputs back into stored, prefixed options. */
export function toStoredOptions(options: string[]): string[] {
  return options.map((option, index) => applyOptionPrefix(option, index))
}
