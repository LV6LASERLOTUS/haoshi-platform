import React from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity } from 'react-native';

export default function SearchBar({ queryText, fileName, inputText, onChangeInput, onSubmit, loading, onReset }) {
  return (
    <View style={styles.bannerContainer}>
      {/* Top Row: Context & Reset */}
      <View style={styles.topRow}>
        <TouchableOpacity style={styles.resetButton} onPress={onReset}>
          <Text style={styles.resetText}>清除重設 🔄</Text>
        </TouchableOpacity>
      </View>

      {/* Seamless Inline Quick-Search Bar */}
      <View style={styles.quickInputWrapper}>
        <TextInput
          style={styles.quickInputBox}
          placeholder="點擊此處直接輸入新需求以再次搜尋..."
          placeholderTextColor="#888"
          value={inputText}
          onChangeText={onChangeInput}
        />
        <TouchableOpacity style={styles.quickSendButton} onPress={onSubmit} disabled={loading}>
          <Text style={styles.quickSendText}>{loading ? '...' : '🔍 搜尋'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  bannerContainer: {
    backgroundColor: '#ffffff',
    paddingTop: 12,
    paddingHorizontal: 16,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  contextHeader: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#6c757d',
    marginBottom: 2,
  },
  contextText: {
    fontSize: 13,
    color: '#343a40',
    fontWeight: '500',
  },
  resetButton: {
    backgroundColor: '#f1f3f5',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#dee2e6',
  },
  resetText: {
    fontSize: 11,
    color: '#495057',
    fontWeight: '600',
  },
  quickInputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  quickInputBox: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    borderRadius: 18,
    paddingHorizontal: 12,
    paddingVertical: 6,
    fontSize: 13,
    borderWidth: 1,
    borderColor: '#ced4da',
    color: '#333',
  },
  quickSendButton: {
    backgroundColor: '#2980b9',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 18,
    marginLeft: 8,
  },
  quickSendText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
});