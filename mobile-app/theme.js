import React, { useContext } from 'react';

/* ───────────── Theme ───────────── */
export const LIGHT = {
  dark: false, bg: '#edf3f8', surface: '#ffffff', ink: '#1f2a37', muted: '#5d6b78', line: '#cfdde9',
  ol: '#25303b', hero: '#2f7ab5', yellow: '#f0b83f', primary: '#2f7ab5', primaryInk: '#ffffff',
  primarySoft: '#dcebf6', accent: '#e0524b', accentSoft: '#fde4e1', warn: '#a85a00',
};
export const DARK = {
  dark: true, bg: '#0f1a24', surface: '#17232f', ink: '#eef3f7', muted: '#9fb1c0', line: '#2b3e50',
  ol: '#05090d', hero: '#2b6a9e', yellow: '#f0b83f', primary: '#5aa7dd', primaryInk: '#06121c',
  primarySoft: '#183247', accent: '#ff7a72', accentSoft: '#40201f', warn: '#f5c15a',
};

export const ThemeCtx = React.createContext(LIGHT);
export const useT = () => useContext(ThemeCtx);
