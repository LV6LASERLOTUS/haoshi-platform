import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ActivityIndicator, Alert, ScrollView } from 'react-native';
import * as ImagePicker from 'expo-image-picker';

export default function App() {
  const [requestText, setRequestText] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [loading, setLoading] = useState(false);

  // Function to pick an image or document from phone gallery
  const pickImage = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 1,
    });

    if (!result.canceled) {
      setSelectedImage(result.assets[0]);
    }
  };

  // Function to submit data to your Python FastAPI backend
  const handleSubmit = async () => {
    if (!requestText.trim()) {
      Alert.alert("提示", "請輸入您的合作需求內容！");
      return;
    }

    const formData = new FormData();
    formData.append('request_text', requestText);

    if (selectedImage) {
      const uriParts = selectedImage.uri.split('.');
      const fileType = uriParts[uriParts.length - 1];
      
      formData.append('uploaded_file', {
        uri: selectedImage.uri,
        name: `photo.${fileType}`,
        type: `image/${fileType}`,
      });
    }

    try {
      setLoading(true);
      // iOS Mirroring: 'http://127.0.0.1:8000/api/v1/match'

      const response = await fetch('http://192.168.50.77:8000/api/v1/match', {
      // const response = await fetch('http://127.0.0.1:8000/api/v1/match', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const result = await response.json();
      if (response.ok) {
        Alert.alert("成功", "需求已成功送出並交由後端分析！");
        setRequestText('');
        setSelectedImage(null);
      } else {
        Alert.alert("失敗", "伺服器處理發生錯誤。");
      }
    } catch (error) {
      console.error(error);
      Alert.alert("連線錯誤", "無法連線至 Python 後端伺服器，請確認 FastAPI 是否正在運行。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>好事大平台</Text>
      <Text style={styles.subtitle}>合作需求提交系統</Text>

      <Text style={styles.label}>請輸入您的需求描述：</Text>
      <TextInput
        style={styles.input}
        placeholder="例如：我們想找中部偏鄉國小舉辦科技營隊..."
        placeholderTextColor="#888"
        multiline
        value={requestText}
        onChangeText={setRequestText}
      />

      <TouchableOpacity style={styles.uploadButton} onPress={pickImage}>
        <Text style={styles.uploadButtonText}>
          {selectedImage ? "已選擇圖片/檔案 (點擊更換)" : "上傳活動企劃或截圖 📁"}
        </Text>
      </TouchableOpacity>

      {selectedImage && (
        <Text style={styles.fileSelectedText}>檔案準備就緒：{selectedImage.uri.split('/').pop()}</Text>
      )}

      <TouchableOpacity style={styles.submitButton} onPress={handleSubmit} disabled={loading}>
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.submitButtonText}>送出需求進行匹配</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: '#f5f5f5',
    padding: 24,
    justifyContent: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2c3e50',
    textAlign: 'center',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#7f8c8d',
    textAlign: 'center',
    marginBottom: 32,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#34495e',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#bdc3c7',
    borderRadius: 8,
    padding: 12,
    height: 120,
    textAlignVertical: 'top',
    fontSize: 16,
    marginBottom: 20,
  },
  uploadButton: {
    backgroundColor: '#ecf0f1',
    borderWidth: 1,
    borderColor: '#bdc3c7',
    borderStyle: 'dashed',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  uploadButtonText: {
    color: '#2980b9',
    fontSize: 15,
    fontWeight: '600',
  },
  fileSelectedText: {
    fontSize: 12,
    color: '#27ae60',
    textAlign: 'center',
    marginBottom: 20,
  },
  submitButton: {
    backgroundColor: '#2980b9',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 10,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});