import React from 'react';
import { View, Text } from 'react-native';
import { useT } from '../../theme';

export const Label = ({ children }) => {
  const c = useT();
  return <Text style={{ fontSize: 13, color: c.muted, fontWeight: '600', marginTop: 16, marginBottom: 8 }}>{children}</Text>;
};

export const Row = ({ children, style }) => <View style={[{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }, style]}>{children}</View>;
