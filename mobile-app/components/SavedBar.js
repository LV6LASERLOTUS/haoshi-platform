import React from 'react';
import { View, Text } from 'react-native';
import { useT } from '../theme';
import PopBtn from './ui/PopBtn';

/* 底部收藏列 */
export default function SavedBar({ count, onCompare }) {
  const c = useT();
  return (
    <View style={{ position: 'absolute', left: 0, right: 0, bottom: 0, backgroundColor: c.surface, borderTopWidth: 2.5, borderColor: c.ol, padding: 12, paddingBottom: 24, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
      <Text style={{ color: c.ink, fontSize: 14 }}>已收藏 {count} 個單位</Text>
      <PopBtn bg={c.primary} color={c.primaryInk} bold onPress={onCompare}>比較已收藏</PopBtn>
    </View>
  );
}
