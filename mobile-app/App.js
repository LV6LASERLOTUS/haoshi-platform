import React, { useState } from 'react';
import { StyleSheet, View, ScrollView, Text, SafeAreaView, TextInput, TouchableOpacity, ActivityIndicator, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as DocumentPicker from 'expo-document-picker';

// Import our modular components
import RequestBanner from './components/RequestBanner';
import CandidateCard from './components/CandidateCard';
import EmailActionToolbar from './components/EmailActionToolbar';

export default function App() {
  const [requestText, setRequestText] = useState('');
  const [attachedFile, setAttachedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const [submittedQuery, setSubmittedQuery] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [selectedEmails, setSelectedEmails] = useState(new Set());

  // Pickers
  const pickImage = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, allowsEditing: true, quality: 1 });
    if (!result.canceled) {
      const asset = result.assets[0];
      setAttachedFile({ uri: asset.uri, name: asset.fileName || 'photo.jpg', type: 'image/jpeg' });
    }
  };

  const pickDocument = async () => {
    try {
      let result = await DocumentPicker.getDocumentAsync({ type: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'] });
      if (!result.canceled && result.assets?.[0]) {
        const doc = result.assets[0];
        setAttachedFile({ uri: doc.uri, name: doc.name, type: doc.mimeType || 'application/pdf' });
      }
    } catch (error) {
      console.log("Doc picker error:", error);
    }
  };

  // Submit and update view smoothly
  const handleSubmit = async () => {
    if (!requestText.trim()) {
      Alert.alert("提示", "請輸入您的合作需求內容！");
      return;
    }

    try {
      setLoading(true);
      setTimeout(() => {
        setSubmittedQuery(requestText);
        setCandidates([
          { id: '1', name: '台灣偏鄉教育協會', type: '教育/NPO', email: 'rural@example.org', score: 92, rationale: '過去有 5 次偏鄉科技營隊經驗，完美匹配預算。' },
          { id: '2', name: '青年夢想協進會', type: '青年發展', email: 'youth@example.org', score: 85, rationale: '領域高度契合，但需注意志工調度時間。' },
          { id: '3', name: '陽光科普推廣中心', type: '科學教育', email: 'sun@example.org', score: 78, rationale: '科普教學背景強，活動規模符合期待。' },
        ]);
        setLoading(false);
      }, 800);
    } catch (error) {
      console.error(error);
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSubmittedQuery(null);
    setCandidates([]);
    setSelectedEmails(new Set());
    setRequestText('');
    setAttachedFile(null);
  };

  // Selection handlers
  const toggleSelect = (email) => {
    const updated = new Set(selectedEmails);
    if (updated.has(email)) updated.delete(email);
    else updated.add(email);
    setSelectedEmails(updated);
  };

  const handleSelectAll = () => {
    const all = new Set(candidates.map(c => c.email));
    setSelectedEmails(all);
  };

  const handleClearAll = () => {
    setSelectedEmails(new Set());
  };

  const handleBatchEmail = () => {
    const list = Array.from(selectedEmails);
    Alert.alert("發送合作信", `準備寄送介紹信給以下 ${list.length} 個單位：\n\n${list.join('\n')}`);
  };

  const handleFeedback = (id, name) => {
    Alert.alert("回饋修正", `已記錄您針對單位「${name}」的回饋意見！`);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
        style={styles.container}
      >
        {!submittedQuery ? (
          // --- VIEW A: Initial Landing Intake Screen ---
          <ScrollView contentContainerStyle={styles.centerContainer}>
            <Text style={styles.title}>好事大平台</Text>
            <Text style={styles.subtitle}>AI 智慧媒合助理</Text>

            <Text style={styles.label}>請輸入您的需求描述：</Text>
            <TextInput
              style={styles.inputLarge}
              placeholder="例如：我們想找中部偏鄉國小舉辦科技營隊..."
              placeholderTextColor="#888"
              multiline
              value={requestText}
              onChangeText={setRequestText}
            />

            <View style={styles.buttonRow}>
              <TouchableOpacity style={styles.subUploadButton} onPress={pickImage}>
                <Text style={styles.subButtonText}>🖼️ 選擇相片</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.subUploadButton} onPress={pickDocument}>
                <Text style={styles.subButtonText}>📄 選擇檔案</Text>
              </TouchableOpacity>
            </View>

            {attachedFile && (
              <Text style={styles.fileSelectedText}>已選擇：{attachedFile.name}</Text>
            )}

            <TouchableOpacity style={styles.submitButton} onPress={handleSubmit} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.submitButtonText}>送出需求進行匹配</Text>}
            </TouchableOpacity>
          </ScrollView>
        ) : (
          // --- VIEW B: Results Screen with Unified Top Banner & Input ---
          <View style={styles.resultsContainer}>
            {/* Unified Top Banner with Integrated Quick Search */}
            <RequestBanner 
              queryText={submittedQuery} 
              fileName={attachedFile?.name} 
              inputText={requestText}
              onChangeInput={setRequestText}
              onSubmit={handleSubmit}
              loading={loading}
              onReset={handleReset} 
            />

            {/* Scrollable Candidate List (~20 Results) */}
            <ScrollView contentContainerStyle={styles.listContainer}>
              <Text style={styles.sectionHeader}>找到 {candidates.length} 個推薦適合單位</Text>

              {candidates.map((item, index) => (
                <CandidateCard 
                  key={item.id}
                  item={item}
                  index={index}
                  isSelected={selectedEmails.has(item.email)}
                  onToggleSelect={toggleSelect}
                  onFeedback={handleFeedback}
                />
              ))}
            </ScrollView>

            {/* Bottom Floating Email Action Toolbar Component */}
            <EmailActionToolbar 
              selectedCount={selectedEmails.size}
              totalCount={candidates.length}
              onSelectAll={handleSelectAll}
              onClearAll={handleClearAll}
              onSendEmail={handleBatchEmail}
            />
          </View>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#f8f9fa' },
  container: { flex: 1 },
  centerContainer: { flexGrow: 1, padding: 24, justifyContent: 'center' },
  title: { fontSize: 28, fontWeight: 'bold', color: '#2c3e50', textAlign: 'center', marginBottom: 4 },
  subtitle: { fontSize: 16, color: '#7f8c8d', textAlign: 'center', marginBottom: 32 },
  label: { fontSize: 14, fontWeight: '600', color: '#34495e', marginBottom: 8 },
  inputLarge: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#bdc3c7', borderRadius: 8, padding: 12, height: 120, textAlignVertical: 'top', fontSize: 16, marginBottom: 20 },
  buttonRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  subUploadButton: { flex: 0.48, backgroundColor: '#ecf0f1', borderWidth: 1, borderColor: '#bdc3c7', borderRadius: 8, padding: 14, alignItems: 'center' },
  subButtonText: { color: '#2980b9', fontSize: 14, fontWeight: '600' },
  fileSelectedText: { fontSize: 13, color: '#16a085', textAlign: 'center', marginBottom: 20 },
  submitButton: { backgroundColor: '#2980b9', borderRadius: 8, padding: 16, alignItems: 'center', marginTop: 10 },
  submitButtonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  
  resultsContainer: { flex: 1 },
  listContainer: { padding: 16, paddingBottom: 100 },
  sectionHeader: { fontSize: 14, fontWeight: '600', color: '#495057', marginBottom: 12 }
});