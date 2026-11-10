import React from 'react';
import { ScrollView } from 'react-native';
import { CATS, EXAMPLES } from '../data/orgs';
import Header from '../components/Header';
import Hero from '../components/Hero';
import RequestInput from '../components/RequestInput';
import Chip from '../components/ui/Chip';
import { Label, Row } from '../components/ui/Layout';

/* ───────────── 第一頁：輸入需求 ───────────── */
export default function SearchScreen({
  q, setQ, cat, setCat, area, setArea, budget, setBudget, onRun, onToggleTheme, toast,
}) {
  return (
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: 16, paddingBottom: 40, maxWidth: 720, width: '100%', alignSelf: 'center' }}>
      <Header onToggleTheme={onToggleTheme} />
      <Hero />

      <RequestInput
        value={q} onChangeText={setQ}
        area={area} onAreaChange={setArea}
        budget={budget} onBudgetChange={setBudget}
        onSubmit={() => onRun()} toast={toast}
      />

      <Label>服務對象</Label>
      <Row>{CATS.map((x) => <Chip key={x} label={x} on={cat === x} onPress={() => setCat(cat === x ? '' : x)} />)}</Row>
      <Label>試試看</Label>
      <Row>{EXAMPLES.map((x) => <Chip key={x} dashed label={x} onPress={() => { setQ(x); onRun(x); }} />)}</Row>
    </ScrollView>
  );
}
