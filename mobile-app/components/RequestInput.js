import React, { useState } from 'react';
import { View, Text, TextInput, Pressable } from 'react-native';
import { useT } from '../theme';
import { AREAS, BUDGETS } from '../data/orgs';
import Pop from './ui/Pop';
import PopBtn from './ui/PopBtn';
import Chip from './ui/Chip';
import { Row } from './ui/Layout';

/* 輸入區：需求描述 + 附件 + 進階條件（地區 / 預算） */
export default function RequestInput({ value, onChangeText, area, onAreaChange, budget, onBudgetChange, onSubmit, toast }) {
  const c = useT();
  const [focus, setFocus] = useState(false);
  const [adv, setAdv] = useState(false);

  const tools = [
    ['⚙ 進階條件', () => setAdv(!adv), adv],
    ['🖼 照片', () => toast('接上 expo-image-picker（示意）')],
    ['📎 檔案', () => toast('接上 expo-document-picker（示意）')],
  ];

  return (
    <Pop r={22} sc={focus ? c.yellow : c.ol} style={{ marginTop: 20 }}>
      <TextInput
        value={value} onChangeText={onChangeText} multiline onFocus={() => setFocus(true)} onBlur={() => setFocus(false)}
        placeholder="例如：我們想找中部偏鄉國小舉辦科技營隊，預算 10 萬內，約 60 位學生…"
        placeholderTextColor={c.muted}
        style={{ color: c.ink, fontSize: 16, minHeight: 96, padding: 16, paddingBottom: 4, textAlignVertical: 'top', lineHeight: 24 }}
      />
      <View style={{ flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 8, padding: 12 }}>
        {tools.map(([t, fn, on]) => (
          <Pressable key={t} onPress={fn} style={{ backgroundColor: on ? c.primarySoft : c.bg, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 7 }}>
            <Text style={{ color: on ? c.primary : c.muted, fontSize: 14 }}>{t}</Text>
          </Pressable>
        ))}
        <PopBtn style={{ marginLeft: 'auto' }} bg={c.primary} color={c.primaryInk} bold r={14} onPress={onSubmit}>開始媒合</PopBtn>
      </View>
      {adv && (
        <View style={{ paddingHorizontal: 12, paddingBottom: 12 }}>
          <Text style={{ fontSize: 12, color: c.muted, marginBottom: 6 }}>地區</Text>
          <Row>{AREAS.map((a) => <Chip key={a} label={a} on={area === a} onPress={() => onAreaChange(a)} />)}</Row>
          <Text style={{ fontSize: 12, color: c.muted, marginTop: 10, marginBottom: 6 }}>預算</Text>
          <Row>{BUDGETS.map((b) => <Chip key={b} label={b} on={budget === b} onPress={() => onBudgetChange(b)} />)}</Row>
        </View>
      )}
    </Pop>
  );
}
