import React, { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Alert, ActivityIndicator, Modal, TextInput, SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { generateEmailReply } from '../api/groq';
import { sendReply } from '../api/gmail';
import { getAccessToken, getGroqKey, saveJobsCache } from '../utils/storage';

export default function JobDetailScreen({ route, navigation }) {
  const { job, allJobs, setJobs } = route.params;
  const [composeVisible, setComposeVisible] = useState(false);
  const [draftLoading, setDraftLoading] = useState(false);
  const [sendLoading, setSendLoading] = useState(false);
  const [draftBody, setDraftBody] = useState('');
  const [toField, setToField] = useState(job.from || '');
  const [subjectField, setSubjectField] = useState(`Re: ${job.subject}`);

  async function generateDraft() {
    const groqKey = await getGroqKey();
    if (!groqKey) { Alert.alert('Add Groq API key in Settings'); return; }
    setDraftLoading(true);
    try {
      const reply = await generateEmailReply(groqKey, {
        jobSummary: job,
        emailBody: job.snippet || job.subject,
        senderName: job.from,
      });
      setDraftBody(reply);
      setComposeVisible(true);
    } catch (e) {
      Alert.alert('Draft generation failed', e.message);
    } finally {
      setDraftLoading(false);
    }
  }

  async function handleSend() {
    if (!draftBody.trim()) { Alert.alert('Reply is empty'); return; }
    setSendLoading(true);
    try {
      const token = await getAccessToken();
      await sendReply(token, {
        to: toField,
        subject: subjectField,
        body: draftBody,
        threadId: job.threadId,
      });

      const updated = (allJobs || []).map(j =>
        j.id === job.id ? { ...j, replied: true } : j
      );
      setJobs?.(updated);
      await saveJobsCache(updated);

      Alert.alert('Sent!', 'Your reply was sent successfully.', [
        { text: 'OK', onPress: () => { setComposeVisible(false); navigation.goBack(); } },
      ]);
    } catch (e) {
      Alert.alert('Send failed', e.message);
    } finally {
      setSendLoading(false);
    }
  }

  const SkillChip = ({ label, type }) => (
    <View style={[styles.chip, type === 'required' ? styles.chipReq : styles.chipNice]}>
      <Text style={[styles.chipText, type === 'required' ? styles.chipTextReq : styles.chipTextNice]}>
        {label}
      </Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Role & Company */}
        <View style={styles.card}>
          <Text style={styles.role}>{job.role || job.subject}</Text>
          <Text style={styles.company}>{job.company || 'Unknown company'}</Text>
          <View style={styles.metaRow}>
            <MetaBadge icon="location-outline" label={job.location || 'Location unknown'} />
            <MetaBadge icon="laptop-outline" label={job.work_type || 'Onsite'} color="#0071e3" />
            {job.salary && <MetaBadge icon="cash-outline" label={job.salary} color="#30a46c" />}
          </View>
          {job.experience && (
            <MetaBadge icon="time-outline" label={`${job.experience} experience`} />
          )}
        </View>

        {/* AI Summary */}
        {job.summary && (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>AI Summary</Text>
            <Text style={styles.summaryText}>{job.summary}</Text>
          </View>
        )}

        {/* Skills */}
        {(job.required_skills?.length > 0 || job.nice_skills?.length > 0) && (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Skills</Text>
            {job.required_skills?.length > 0 && (
              <>
                <Text style={styles.skillLabel}>Required</Text>
                <View style={styles.chipRow}>
                  {job.required_skills.map(s => <SkillChip key={s} label={s} type="required" />)}
                </View>
              </>
            )}
            {job.nice_skills?.length > 0 && (
              <>
                <Text style={[styles.skillLabel, { marginTop: 10 }]}>Nice to have</Text>
                <View style={styles.chipRow}>
                  {job.nice_skills.map(s => <SkillChip key={s} label={s} type="nice" />)}
                </View>
              </>
            )}
          </View>
        )}

        {/* Email snippet */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Email</Text>
          <Text style={styles.from}>From: {job.from}</Text>
          <Text style={styles.snippet}>{job.snippet}</Text>
        </View>

        {/* Reply button */}
        {!job.replied && (
          <TouchableOpacity
            style={styles.replyBtn}
            onPress={() => { setComposeVisible(true); if (!draftBody) generateDraft(); }}
            disabled={draftLoading}
          >
            {draftLoading
              ? <ActivityIndicator color="#fff" />
              : <>
                  <Ionicons name="sparkles" size={18} color="#fff" style={{ marginRight: 8 }} />
                  <Text style={styles.replyBtnText}>AI Draft Reply</Text>
                </>
            }
          </TouchableOpacity>
        )}
        {job.replied && (
          <View style={styles.repliedBadge}>
            <Ionicons name="checkmark-circle" size={18} color="#30a46c" style={{ marginRight: 6 }} />
            <Text style={styles.repliedText}>Replied</Text>
          </View>
        )}
      </ScrollView>

      {/* Compose Modal */}
      <Modal visible={composeVisible} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={styles.modal}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setComposeVisible(false)}>
              <Text style={styles.modalCancel}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Reply</Text>
            <TouchableOpacity onPress={handleSend} disabled={sendLoading}>
              {sendLoading
                ? <ActivityIndicator color="#0071e3" />
                : <Text style={styles.modalSend}>Send</Text>}
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.modalBody}>
            <Text style={styles.fieldLabel}>To</Text>
            <TextInput style={styles.fieldInput} value={toField} onChangeText={setToField} />
            <Text style={styles.fieldLabel}>Subject</Text>
            <TextInput style={styles.fieldInput} value={subjectField} onChangeText={setSubjectField} />
            <Text style={styles.fieldLabel}>Body</Text>
            <TextInput
              style={[styles.fieldInput, styles.bodyInput]}
              value={draftBody}
              onChangeText={setDraftBody}
              multiline
              placeholder="Write your reply..."
            />
            <TouchableOpacity style={styles.regenerateBtn} onPress={generateDraft} disabled={draftLoading}>
              <Ionicons name="refresh" size={16} color="#0071e3" style={{ marginRight: 6 }} />
              <Text style={styles.regenerateText}>Regenerate with AI</Text>
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

function MetaBadge({ icon, label, color = '#636366' }) {
  return (
    <View style={styles.metaBadge}>
      <Ionicons name={icon} size={13} color={color} style={{ marginRight: 4 }} />
      <Text style={[styles.metaBadgeText, { color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f7' },
  scroll: { padding: 16, gap: 12, paddingBottom: 40 },
  card: { backgroundColor: '#fff', borderRadius: 18, padding: 18, shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 8, elevation: 2 },
  role: { fontSize: 20, fontWeight: '700', color: '#1d1d1f', letterSpacing: -0.3 },
  company: { fontSize: 15, color: '#636366', marginTop: 4 },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 12 },
  metaBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#f2f2f7', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 5 },
  metaBadgeText: { fontSize: 12, fontWeight: '500' },
  sectionTitle: { fontSize: 13, fontWeight: '700', color: '#8e8e93', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 10 },
  summaryText: { fontSize: 15, color: '#3c3c43', lineHeight: 22 },
  skillLabel: { fontSize: 12, fontWeight: '600', color: '#8e8e93', marginBottom: 6 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  chip: { borderRadius: 999, paddingHorizontal: 12, paddingVertical: 4 },
  chipReq: { backgroundColor: '#e3f0ff' },
  chipNice: { backgroundColor: '#f0e8ff' },
  chipText: { fontSize: 12, fontWeight: '600' },
  chipTextReq: { color: '#0051a2' },
  chipTextNice: { color: '#6419a0' },
  from: { fontSize: 13, color: '#636366', marginBottom: 8 },
  snippet: { fontSize: 14, color: '#3c3c43', lineHeight: 20 },
  replyBtn: { backgroundColor: '#0071e3', borderRadius: 14, padding: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center' },
  replyBtnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  repliedBadge: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', padding: 16 },
  repliedText: { color: '#30a46c', fontWeight: '600', fontSize: 15 },
  modal: { flex: 1, backgroundColor: '#fff' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: '#e5e5ea' },
  modalTitle: { fontSize: 17, fontWeight: '600' },
  modalCancel: { fontSize: 16, color: '#636366' },
  modalSend: { fontSize: 16, color: '#0071e3', fontWeight: '600' },
  modalBody: { padding: 20 },
  fieldLabel: { fontSize: 12, fontWeight: '700', color: '#8e8e93', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6, marginTop: 14 },
  fieldInput: { borderWidth: 1.5, borderColor: '#d2d2d7', borderRadius: 10, padding: 12, fontSize: 15, color: '#1d1d1f' },
  bodyInput: { minHeight: 200, textAlignVertical: 'top' },
  regenerateBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 16, padding: 12 },
  regenerateText: { color: '#0071e3', fontWeight: '600' },
});
