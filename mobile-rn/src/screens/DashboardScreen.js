import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  RefreshControl, SafeAreaView, Alert, ActivityIndicator,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { fetchJobEmails } from '../api/gmail';
import { analyzeJobEmail } from '../api/groq';
import { quickAnalyze } from '../utils/jobAnalyzer';
import { getAccessToken, getGroqKey, getJobsCache, saveJobsCache, getUserEmail } from '../utils/storage';
import JobCard from '../components/JobCard';
import StatBar from '../components/StatBar';

export default function DashboardScreen({ navigation }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [analyzingId, setAnalyzingId] = useState(null);

  useFocusEffect(
    useCallback(() => {
      loadCached();
    }, [])
  );

  async function loadCached() {
    const email = await getUserEmail();
    setUserEmail(email || '');
    const cached = await getJobsCache();
    if (cached.length) setJobs(cached);
  }

  async function refresh() {
    setRefreshing(true);
    try {
      const token = await getAccessToken();
      if (!token) { Alert.alert('Not signed in'); return; }
      const emails = await fetchJobEmails(token, 30);
      const parsed = emails.map(quickAnalyze);
      setJobs(parsed);
      await saveJobsCache(parsed);
    } catch (e) {
      Alert.alert('Error fetching emails', e.message);
    } finally {
      setRefreshing(false);
    }
  }

  async function aiAnalyzeJob(job) {
    const groqKey = await getGroqKey();
    if (!groqKey) {
      Alert.alert('Groq API Key needed', 'Add your Groq key in Settings to use AI analysis.');
      return;
    }
    setAnalyzingId(job.id);
    try {
      const result = await analyzeJobEmail(groqKey, job.body || job.snippet);
      const updated = jobs.map(j =>
        j.id === job.id ? { ...j, ...result, ai_analyzed: true } : j
      );
      setJobs(updated);
      await saveJobsCache(updated);
    } catch (e) {
      Alert.alert('AI Analysis failed', e.message);
    } finally {
      setAnalyzingId(null);
    }
  }

  const stats = {
    total: jobs.length,
    remote: jobs.filter(j => j.work_type === 'Remote').length,
    analyzed: jobs.filter(j => j.ai_analyzed).length,
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Job Emails</Text>
          <Text style={styles.subGreeting}>{userEmail}</Text>
        </View>
        <TouchableOpacity onPress={refresh} style={styles.refreshBtn} disabled={refreshing}>
          {refreshing
            ? <ActivityIndicator color="#ffffff" size="small" />
            : <Ionicons name="refresh" size={22} color="#ffffff" />}
        </TouchableOpacity>
      </View>

      {/* Stats */}
      <StatBar stats={stats} />

      {/* Job List */}
      <FlatList
        data={jobs}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor="#0071e3" />}
        renderItem={({ item }) => (
          <JobCard
            job={item}
            analyzing={analyzingId === item.id}
            onPress={() => navigation.navigate('JobDetail', { job: item, allJobs: jobs, setJobs })}
            onAIAnalyze={() => aiAnalyzeJob(item)}
          />
        )}
        ListEmptyComponent={
          !refreshing && (
            <View style={styles.empty}>
              <Ionicons name="mail-open-outline" size={52} color="#c7c7cc" />
              <Text style={styles.emptyText}>No emails yet</Text>
              <Text style={styles.emptySubtext}>Tap ↻ to fetch recruiter emails from Gmail</Text>
            </View>
          )
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f7' },
  header: {
    backgroundColor: '#1d1d1f',
    paddingHorizontal: 20, paddingVertical: 16,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
  },
  greeting: { fontSize: 22, fontWeight: '700', color: '#ffffff' },
  subGreeting: { fontSize: 12, color: 'rgba(255,255,255,0.45)', marginTop: 2 },
  refreshBtn: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.12)',
    alignItems: 'center', justifyContent: 'center',
  },
  list: { padding: 16, gap: 12 },
  empty: { alignItems: 'center', paddingTop: 80 },
  emptyText: { fontSize: 17, fontWeight: '600', color: '#3c3c43', marginTop: 14 },
  emptySubtext: { fontSize: 13, color: '#8e8e93', marginTop: 6 },
});
