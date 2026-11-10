import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useT } from '../theme';
import { SORTS } from '../data/orgs';

/* 結果標題 + 排序切換 */
export default function ResultsHeader({ count, sort, onSortChange }) {
  const c = useT();
  return (
    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
      <View>
        <Text style={{ color: c.ink, fontSize: 17, fontWeight: '700' }}>找到 {count} 個推薦單位</Text>
        <Text style={{ color: c.muted, fontSize: 13 }}>已依你的需求計算符合度</Text>
      </View>
      <View style={{ flexDirection: 'row', backgroundColor: c.line, borderRadius: 10, padding: 3 }}>
        {SORTS.map(([k, t]) => (
          <Pressable key={k} onPress={() => onSortChange(k)} style={{ borderRadius: 8, paddingHorizontal: 12, paddingVertical: 4, backgroundColor: sort === k ? c.surface : 'transparent' }}>
            <Text style={{ fontSize: 13, color: sort === k ? c.ink : c.muted, fontWeight: sort === k ? '600' : '400' }}>{t}</Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}
