import React from 'react';
import { ScrollView } from 'react-native';
import { CATEGORIES, EXAMPLES } from '../data/orgs';
import Header from '../components/Header';
import Hero from '../components/Hero';
import RequestInput from '../components/RequestInput';
import Chip from '../components/ui/Chip';
import { Label, Row } from '../components/ui/Layout';

/* ───────────── 第一頁：輸入需求 ───────────── */
export default function SearchScreen({
  query, setQuery, category, setCategory, area, setArea, budget, setBudget, onSearch, onToggleTheme, toast,
}) {
  return (
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: 16, paddingBottom: 40, maxWidth: 720, width: '100%', alignSelf: 'center' }}>
      <Header onToggleTheme={onToggleTheme} />
      <Hero />

      <RequestInput
        value={query} onChangeText={setQuery}
        area={area} onAreaChange={setArea}
        budget={budget} onBudgetChange={setBudget}
        onSubmit={() => onSearch()} toast={toast}
      />

      <Label>服務對象</Label>
      <Row>
        {CATEGORIES.map((option) => (
          <Chip
            key={option}
            label={option}
            on={category === option}
            onPress={() => setCategory(category === option ? '' : option)}
          />
        ))}
      </Row>

      <Label>試試看</Label>
      <Row>
        {EXAMPLES.map((example) => (
          <Chip
            key={example}
            dashed
            label={example}
            onPress={() => { setQuery(example); onSearch(example); }}
          />
        ))}
      </Row>
    </ScrollView>
  );
}
