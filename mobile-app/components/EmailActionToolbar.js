import React from 'react';
import { StyleSheet, Text, View, TouchableOpacity } from 'react-native';

export default function EmailActionToolbar({ selectedCount, totalCount, onSelectAll, onClearAll, onSendEmail }) {
  if (selectedCount === 0) return null; // Hide if nothing is selected

  return (
    <View style={styles.floatingBar}>
      <View style={styles.infoGroup}>
        <Text style={styles.selectedCountText}>已選 {selectedCount} / {totalCount} 個單位</Text>
        <View style={styles.actionLinks}>
          <TouchableOpacity onPress={onSelectAll}>
            <Text style={styles.linkText}>全選</Text>
          </TouchableOpacity>
          <Text style={styles.separator}>|</Text>
          <TouchableOpacity onPress={onClearAll}>
            <Text style={styles.linkText}>取消</Text>
          </TouchableOpacity>
        </View>
      </View>

      <TouchableOpacity style={styles.emailButton} onPress={onSendEmail}>
        <Text style={styles.emailButtonText}>📧 發送合作信</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  floatingBar: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: '#212529',
    borderRadius: 30,
    paddingVertical: 12,
    paddingHorizontal: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 6,
  },
  infoGroup: {
    flexDirection: 'column',
  },
  selectedCountText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
  actionLinks: {
    flexDirection: 'row',
    marginTop: 2,
  },
  linkText: {
    color: '#adb5bd',
    fontSize: 11,
    textDecorationLine: 'underline',
  },
  separator: {
    color: '#6c757d',
    fontSize: 11,
    marginHorizontal: 6,
  },
  emailButton: {
    backgroundColor: '#4c6ef5',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
  },
  emailButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
});