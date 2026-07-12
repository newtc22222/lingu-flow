import { ISRSData } from '../models/Card';

/**
 * SuperMemo-2 (SM-2) Spaced Repetition Algorithm.
 * 
 * Quality response scale:
 * 0: Complete blackout.
 * 1: Incorrect response; the correct one remembered.
 * 2: Incorrect response; where the correct one seemed easy to recall.
 * 3: Correct response recalled with serious difficulty.
 * 4: Correct response after a hesitation.
 * 5: Perfect response.
 * 
 * In a 1-4 scale, we typically map them to 2-5 or similar, but the user requested 0-5 or 1-4.
 * We'll use 0-5 for calculation as it matches standard SM-2.
 */
export function calculateSM2(
  srsData: ISRSData,
  quality: number // 0 to 5
): ISRSData {
  let { interval, easeFactor, repetitions } = srsData;

  // quality should be clamped between 0 and 5
  quality = Math.max(0, Math.min(5, Math.round(quality)));

  if (quality >= 3) {
    if (repetitions === 0) {
      interval = 1;
    } else if (repetitions === 1) {
      interval = 6;
    } else {
      interval = Math.round(interval * easeFactor);
    }
    repetitions++;
  } else {
    repetitions = 0;
    interval = 1;
  }

  // Update ease factor
  easeFactor = easeFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
  
  if (easeFactor < 1.3) {
    easeFactor = 1.3;
  }

  // Calculate next review date by adding `interval` days to current time
  const nextReviewDate = new Date();
  nextReviewDate.setDate(nextReviewDate.getDate() + interval);

  return {
    interval,
    easeFactor,
    repetitions,
    nextReviewDate,
  };
}
