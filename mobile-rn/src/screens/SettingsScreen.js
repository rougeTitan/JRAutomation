import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  Alert, ScrollView, SafeAreaView, Switch,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import {
  getGroqKey, saveGroqKey,
  getOpenAIKey, saveOpenAIKey,
  getUserEmail, clearTokens,
} from '../utils/storage';

export default function SettingsScreen({ navigation }) {
  const [groqKey, setGroqKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [showGroq, setShowGroq] = useState(false);
  const [showOpenAI, setShowOpenAI] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    async function load() {
      const gk = await getGroqKey();
      const ok = await getOpenAIKey();
      const em = await getUserEmail();
      if (gk) setGroqKey(gk);
      if (ok) setOpenaiKey(ok);
      if (em) setUserEmail(em);
    }
    load();
  }, []);

  async function saveKeys() {
    await saveGroqKey(groqKey.trim());
    await saveOpenAIKey(openaiKey.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  async function signOut() {
    Alert.alert('Sign Out', 'This will clear your Gmail session and cached data.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out', style: 'destructive',
        onPress: async () => {
          await clearTokens();
          navigation.reset({ index: 0, routes: [{ name: 'Login' }] });
        },
      },
    ]);
  }

  const Section = ({ title, children }) => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.sectionCard}>{children}</View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Settings</Text>
      </View>
      <ScrollView contentContainerStyle={styles.scroll}>

        {/* Account */}
        <Section title="Account">
          <View style={styles.row}>
            <Ionicons name="person-circle-outline" size={22} color="#636366" />
            <Text style={styles.rowText}>{userEmail || 'Not signed in'}</Text>
          </View>
          <TouchableOpacity style={styles.signOutBtn} onPress={signOut}>
            <Ionicons name="log-out-outline" size={18} color="#ff3b30" style={{ marginRight: 8 }} />
            <Text style={styles.signOutText}>Sign Out</Text>
          </TouchableOpacity>
        </Section>

        {/* API Keys */}
        <Section title="API Keys (stored securely on device)">
          <Text style={styles.keyLabel}>Groq API Key</Text>
          <Text style={styles.keyHint}>
            Get free key at <Text style={styles.link}>console.groq.com/keys</Text>
          </Text>
          <View style={styles.keyInputWrap}>
            <TextInput
              style={styles.keyInput}
              value={groqKey}
              onChangeText={setGroqKey}
              placeholder="gsk_..."
              secureTextEntry={!showGroq}
              autoCapitalize="none"
              autoCorrect={false}
            />
            <TouchableOpacity onPress={() => setShowGroq(v => !v)} style={styles.eyeBtn}>
              <Ionicons name={showGroq ? 'eye-off' : 'eye'} size={18} color="#8e8e93" />
            </TouchableOpacity>
          </View>

          <Text style={[styles.keyLabel, { marginTop: 16 }]}>OpenAI API Key</Text>
          <Text style={styles.keyHint}>
            Optional — enables deeper job analysis at{' '}
            <Text style={styles.link}>platform.openai.com/api-keys</Text>
          </Text>
          <View style={styles.keyInputWrap}>
            <TextInput
              style={styles.keyInput}
              value={openaiKey}
              onChangeText={setOpenaiKey}
              placeholder="sk-..."
              secureTextEntry={!showOpenAI}
              autoCapitalize="none"
              autoCorrect={false}
            />
            <TouchableOpacity onPress={() => setShowOpenAI(v => !v)} style={styles.eyeBtn}>
              <Ionicons name={showOpenAI ? 'eye-off' : 'eye'} size={18} color="#8e8e93" />
            </TouchableOpacity>
          </View>

          <TouchableOpacity style={[styles.saveBtn, saved && styles.saveBtnSaved]} onPress={saveKeys}>
            <Ionicons
              name={saved ? 'checkmark-circle' : 'save-outline'}
              size={18} color="#fff"
              style={{ marginRight: 8 }}
            />
            <Text style={styles.saveBtnText}>{saved ? 'Saved!' : 'Save Keys'}</Text>
          </TouchableOpacity>
        </Section>

        {/* About */}
        <Section title="About">
          <View style={styles.row}>
            <Ionicons name="information-circle-outline" size={20} color="#636366" />
            <Text style={styles.rowText}>JobAI v1.0.0</Text>
          </View>
          <Text style={styles.aboutText}>
            Self-contained app — calls Gmail, Groq, and OpenAI APIs directly from your device.
            No data is sent to any intermediate server.
          </Text>
        </Section>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f7' },
  header: { backgroundColor: '#1d1d1f', paddingHorizontal: 20, paddingVertical: 16 },
  headerTitle: { fontSize: 22, fontWeight: '700', color: '#ffffff' },
  scroll: { padding: 16, gap: 20, paddingBottom: 40 },
  section: {},
  sectionTitle: { fontSize: 12, fontWeight: '700', color: '#8e8e93', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8, marginLeft: 4 },
  sectionCard: { backgroundColor: '#fff', borderRadius: 18, padding: 18, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 8, elevation: 1 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 12 },
  rowText: { fontSize: 15, color: '#3c3c43' },
  signOutBtn: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10 },
  signOutText: { color: '#ff3b30', fontWeight: '600', fontSize: 15 },
  keyLabel: { fontSize: 14, fontWeight: '600', color: '#1d1d1f', marginBottom: 4 },
  keyHint: { fontSize: 12, color: '#8e8e93', marginBottom: 8 },
  link: { color: '#0071e3' },
  keyInputWrap: { flexDirection: 'row', alignItems: 'center', borderWidth: 1.5, borderColor: '#d2d2d7', borderRadius: 10, overflow: 'hidden' },
  keyInput: { flex: 1, padding: 12, fontSize: 14, color: '#1d1d1f' },
  eyeBtn: { paddingHorizontal: 12 },
  saveBtn: { backgroundColor: '#0071e3', borderRadius: 12, padding: 14, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 18 },
  saveBtnSaved: { backgroundColor: '#30a46c' },
  saveBtnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  aboutText: { fontSize: 13, color: '#636366', lineHeight: 20, marginTop: 8 },
});
