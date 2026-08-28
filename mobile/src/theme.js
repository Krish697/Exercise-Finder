// ─── Design System — matches the Stitch design exactly ───────────────────────

export const colors = {
  // Core palette (from Stitch style guide)
  primary:    '#6366F1',   // Indigo
  primaryL:   '#818CF8',   // Lighter indigo
  primaryD:   '#4F46E5',   // Deeper indigo
  secondary:  '#10B981',   // Emerald green
  secondaryL: '#34D399',
  tertiary:   '#F59E0B',   // Amber
  tertiaryL:  '#FCD34D',
  danger:     '#EF4444',
  dangerL:    '#F87171',
  purple:     '#A855F7',
  cyan:       '#06B6D4',
  sky:        '#0EA5E9',

  // Backgrounds
  bg:         '#0F0F14',
  bgCard:     '#16161F',
  bgCard2:    '#1C1C28',
  bgInput:    '#1E1E2C',

  // Borders
  border:     'rgba(255,255,255,0.08)',
  borderL:    'rgba(255,255,255,0.12)',

  // Text
  text:       '#F1F1F5',
  text2:      '#9CA3AF',
  text3:      '#6B7280',
  textMuted:  '#4B5563',

  // Status
  success:    '#10B981',
  warning:    '#F59E0B',
  error:      '#EF4444',

  white: '#FFFFFF',
  black: '#000000',
  transparent: 'transparent',
};

export const spacing = {
  xs:  4,
  sm:  8,
  md:  12,
  lg:  16,
  xl:  24,
  xxl: 32,
  xxxl: 48,
};

export const radius = {
  sm:   6,
  md:   10,
  lg:   14,
  xl:   20,
  xxl:  28,
  full: 999,
};

export const fontSize = {
  xs:   11,
  sm:   13,
  base: 15,
  md:   17,
  lg:   20,
  xl:   24,
  xxl:  30,
  xxxl: 38,
};

export const fontWeight = {
  regular: '400',
  medium:  '500',
  semibold:'600',
  bold:    '700',
  extrabold:'800',
  black:   '900',
};

// Muscle group colors for map
export const muscleColors = {
  chest:       colors.primary,
  shoulders:   colors.purple,
  biceps:      colors.sky,
  triceps:     colors.cyan,
  forearms:    '#22D3EE',
  abdominals:  colors.secondary,
  lats:        colors.purple,
  middle_back: colors.tertiary,
  lower_back:  colors.tertiary,
  glutes:      colors.danger,
  quadriceps:  colors.primary,
  hamstrings:  colors.secondary,
  calves:      colors.tertiary,
  traps:       colors.sky,
};

export const difficultyColors = {
  beginner:     colors.secondary,
  intermediate: colors.tertiary,
  expert:       colors.danger,
};

export default { colors, spacing, radius, fontSize, fontWeight, muscleColors, difficultyColors };
