// New 9-step condition model. Mirrors the Swappie-style flow.
// Note: All fields default to `null` so the user must actively answer each step.

export type ScreenGlass = "chipped" | "scratched" | "none";
export type WearLevel = "visible" | "some" | "minimal" | "none";
export type WearLevelWithCrack = "cracked" | WearLevel;

export interface FunctionalChecks {
  powersOn: boolean | null;
  network: boolean | null;
  faceId: boolean | null;
  selfieCamera: boolean | null;
  speaker: boolean | null;
  bentOrWaterDamaged: boolean | null; // true = ja (dåligt), false = nej (bra)
}

export interface ScreenFunctionChecks {
  brightSpots: boolean;
  deadPixels: boolean;
  linesOrBurnIn: boolean;
  allWorks: boolean;
}

export interface ConditionAnswers {
  batteryHealth: number | null;
  functional: FunctionalChecks;
  screenFunction: ScreenFunctionChecks;
  screenFunctionAnswered: boolean; // true once user has actively interacted with step 5
  screenGlass: ScreenGlass | null;
  screenWear: WearLevel | null;
  sidesWear: WearLevelWithCrack | null;
  backWear: WearLevelWithCrack | null;
}

export const initialFunctional: FunctionalChecks = {
  powersOn: null,
  network: null,
  faceId: null,
  selfieCamera: null,
  speaker: null,
  bentOrWaterDamaged: null,
};

export const initialScreenFunction: ScreenFunctionChecks = {
  brightSpots: false,
  deadPixels: false,
  linesOrBurnIn: false,
  allWorks: false,
};

export const initialConditionAnswers: ConditionAnswers = {
  batteryHealth: null,
  functional: initialFunctional,
  screenFunction: initialScreenFunction,
  screenFunctionAnswered: false,
  screenGlass: null,
  screenWear: null,
  sidesWear: null,
  backWear: null,
};
