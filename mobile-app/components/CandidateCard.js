import React from 'react';
import { StyleSheet, Text, View, TouchableOpacity } from 'react-native';

export default function CandidateCard({ item, index, isSelected, onToggleSelect, onFeedback }) {
  return (
    <View style={[styles.card, isSelected && styles.cardSelected]}>
      <View style={styles.cardHeader}>
        <TouchableOpacity onPress={() => onToggleSelect(item.email)} style={styles.flexRow}>
          <Text style={styles.checkbox}>{isSelected ? '☑️' : '🟩'}</Text>
          <View>
            <Text style={styles.cardTitle}>#{index + 1} {item.name}</Text>
            <Text style={styles.cardSubtitle}>{item.type}</Text>
          </View>
        </TouchableOpacity>
        <View style={styles.scoreBadge}>
          <Text style={styles.scoreText}>{item.score}% Match</Text>
        </View>
      </View>

      <Text style={styles.rationaleText}>{item.rationale}</Text>

      <TouchableOpacity style={styles.feedbackBtn} onPress={() => onFeedback(item.id, item.name)}>
        <Text style={styles.feedbackText}>💬 回饋修正</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 12, borderWidth: 1, borderColor: '#dee2e6' },
  cardSelected: { borderColor: '#2980b9', backgroundColor: '#f4f8fb' },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  flexRow: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  checkbox: { marginRight: 8, fontSize: 16 },
  cardTitle: { fontSize: 15, fontWeight: 'bold', color: '#212529' },
  cardSubtitle: { fontSize: 11, color: '#6c757d' },
  scoreBadge: { backgroundColor: '#e6fcf5', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  scoreText: { color: '#0ca678', fontSize: 12, fontWeight: 'bold' },
  rationaleText: { fontSize: 13, color: '#495057', lineHeight: 18, marginBottom: 8 },
  feedbackBtn: { alignSelf: 'flex-end', paddingVertical: 4 },
  feedbackText: { fontSize: 12, color: '#4c6ef5', fontWeight: '500' }
});