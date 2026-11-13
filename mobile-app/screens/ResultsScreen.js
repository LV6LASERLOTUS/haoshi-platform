import React, { useState } from 'react';
import { View, Text, ScrollView } from 'react-native';
import { useT } from '../theme';
import ResultsHeader from '../components/ResultsHeader';
import ResultCard from '../components/ResultCard';
import SavedBar from '../components/SavedBar';
import Skeleton from '../components/ui/Skeleton';
import BackButton from '../components/ui/BackButton';

/* ───────────── 第二頁：媒合結果 ───────────── */
export default function ResultsScreen({ query, loading, res, onBack, onFeedback, toast }) {
  const c = useT();
  const [sort, setSort] = useState('match');
  const [saved, setSaved] = useState({});

  const toggleSave = (name) => {
    setSaved({ ...saved, [name]: !saved[name] });
    toast(saved[name] ? '已取消收藏' : '已收藏');
  };

  const list = res ? [...res] : [];
  if (sort === 'budget') list.sort((a, b) => b.s.預算 - a.s.預算);
  if (sort === 'area') list.sort((a, b) => b.s.地區 - a.s.地區);
  const savedCount = Object.values(saved).filter(Boolean).length;

  return (
    <View style={{ flex: 1 }}>
      {/* 頂部列：標題 + 右上角返回 */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 16, paddingVertical: 10, borderBottomWidth: 2.5, borderColor: c.ol, backgroundColor: c.surface }}>
        <View style={{ flex: 1 }}>
          <Text style={{ color: c.ink, fontSize: 18, fontWeight: '800' }}>媒合結果</Text>
          {!!query && <Text numberOfLines={1} style={{ color: c.muted, fontSize: 13 }}>「{query}」</Text>}
        </View>
        <BackButton onPress={onBack} />
      </View>

      <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 110, maxWidth: 720, width: '100%', alignSelf: 'center' }}>
        {loading && (
          <>
            <Text style={{ color: c.ink, fontSize: 17, fontWeight: '700', marginBottom: 12 }}>AI 正在分析需求…</Text>
            <Skeleton /><Skeleton /><Skeleton />
          </>
        )}
        {res && !loading && (
          <>
            <ResultsHeader count={list.length} sort={sort} onSortChange={setSort} />
            {list.map((o, i) => (
              <ResultCard key={o.n} o={o} i={i} top={i === 0 && sort === 'match'} saved={!!saved[o.n]}
                onSave={() => toggleSave(o.n)} onFeedback={() => onFeedback?.(o)} toast={toast} />
            ))}
          </>
        )}
      </ScrollView>

      {savedCount > 0 && <SavedBar count={savedCount} onCompare={() => toast('比較功能（示意）')} />}
    </View>
  );
}
