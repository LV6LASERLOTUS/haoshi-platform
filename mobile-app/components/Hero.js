import React from 'react';
import { View, Text } from 'react-native';
import { useT } from '../theme';
import Pop from './ui/Pop';
import { Row } from './ui/Layout';
import HeroArt from './art/HeroArt';

const BADGES = ['280 家認證組織', '財務透明・良善治理'];

export default function Hero() {
  const c = useT();
  return (
    <Pop r={26} bg={c.hero}>
      <View style={{ flexDirection: 'row', alignItems: 'center', paddingVertical: 20, paddingLeft: 18, paddingRight: 8 }}>
        <View style={{ flex: 1 }}>
          <Text style={{ color: '#fff', fontSize: 30, fontWeight: '800', textShadowColor: 'rgba(0,0,0,.25)', textShadowOffset: { width: 2, height: 2 }, textShadowRadius: 0 }}>好事大平台</Text>
          <Text style={{ color: '#fff', fontSize: 15, fontWeight: '600', marginTop: 6, lineHeight: 22 }}>AI 智慧媒合助理{'\n'}說說需求，幫你找到對的夥伴</Text>
          <Row style={{ marginTop: 14, gap: 6 }}>
            {BADGES.map((t) => (
              <Text key={t} style={{ backgroundColor: c.yellow, color: '#25303b', borderColor: c.ol, borderWidth: 2, borderRadius: 999, paddingHorizontal: 10, fontSize: 12, fontWeight: '700', overflow: 'hidden' }}>{t}</Text>
            ))}
          </Row>
        </View>
        <HeroArt />
      </View>
    </Pop>
  );
}
