import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const WORK_TYPE_COLOR = { Remote: '#0071e3', Hybrid: '#f59e0b', Onsite: '#636366' };

export default function JobCard({ job, onPress, onAIAnalyze, analyzing }) {
  return (
    <TouchableOpacity style={[styles.card, job.replied && styles.cardReplied]} onPress={onPress} activeOpacity={0.8}>
      {/* Top row */}
      <View style={styles.topRow}>
        <View style={styles.titleBlock}>
          <Text style={styles.role} numberOfLines={1}>{job.role || job.subject}</Text>
          <Text style={styles.company} numberOfLines={1}>{job.company || 'Unknown company'}</Text>
        </View>
        <View style={styles.badges}>
          {job.replied && (
            <View style={styles.repliedBadge}>
              <Text style={styles.repliedBadgeText}>Replied</Text>
            </View>
          )}
          {job.ai_analyzed && (
            <View style={styles.aiBadge}>
              <Ionicons name="sparkles" size={10} color="#6419a0" />
              <Text style={styles.aiBadgeText}>AI</Text>
            </View>
          )}
        </View>
      </View>

      {/* Meta */}
      <View style={styles.metaRow}>
        {job.location && (
          <View style={styles.metaItem}>
            <Ionicons name="location-outline" size={12} color="#8e8e93" />
            <Text style={styles.metaText}>{job.location}</Text>
          </View>
        )}
        {job.work_type && (
          <View style={[styles.metaItem, styles.workTypeBadge, { backgroundColor: WORK_TYPE_COLOR[job.work_type] + '18' }]}>
            <Text style={[styles.workTypeText, { color: WORK_TYPE_COLOR[job.work_type] }]}>
              {job.work_type}
            </Text>
          </View>
        )}
        {job.salary && (
          <View style={styles.metaItem}>
            <Ionicons name="cash-outline" size={12} color="#30a46c" />
            <Text style={[styles.metaText, { color: '#30a46c' }]}>{job.salary}</Text>
          </View>
        )}
      </View>

      {/* Skills */}
      {job.required_skills?.length > 0 && (
        <View style={styles.skillsRow}>
          {job.required_skills.slice(0, 4).map(s => (
            <View key={s} style={styles.skill}>
              <Text style={styles.skillText}>{s}</Text>
            </View>
          ))}
          {job.required_skills.length > 4 && (
            <Text style={styles.moreSkills}>+{job.required_skills.length - 4}</Text>
          )}
        </View>
      )}

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.date}>{formatDate(job.date)}</Text>
        {!job.ai_analyzed && !job.replied && (
          <TouchableOpacity style={styles.analyzeBtn} onPress={onAIAnalyze} disabled={analyzing}>
            {analyzing
              ? <ActivityIndicator size="small" color="#0071e3" />
              : <>
                  <Ionicons name="sparkles" size={13} color="#0071e3" style={{ marginRight: 4 }} />
                  <Text style={styles.analyzeBtnText}>AI Analyze</Text>
                </>
            }
          </TouchableOpacity>
        )}
      </View>
    </TouchableOpacity>
  );
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  try { return new Date(dateStr).toLocaleDateString(); } catch { return dateStr; }
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', borderRadius: 16, padding: 16, shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 8, elevation: 2 },
  cardReplied: { opacity: 0.6 },
  topRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 },
  titleBlock: { flex: 1, marginRight: 8 },
  role: { fontSize: 16, fontWeight: '700', color: '#1d1d1f', letterSpacing: -0.2 },
  company: { fontSize: 13, color: '#636366', marginTop: 2 },
  badges: { flexDirection: 'row', gap: 6 },
  aiBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#f0e8ff', borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3, gap: 3 },
  aiBadgeText: { fontSize: 10, fontWeight: '700', color: '#6419a0' },
  repliedBadge: { backgroundColor: '#e8f9f1', borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3 },
  repliedBadgeText: { fontSize: 10, fontWeight: '700', color: '#30a46c' },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 10 },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#f2f2f7', borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4 },
  metaText: { fontSize: 12, color: '#8e8e93' },
  workTypeBadge: { backgroundColor: 'transparent' },
  workTypeText: { fontSize: 12, fontWeight: '600' },
  skillsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 10 },
  skill: { backgroundColor: '#e3f0ff', borderRadius: 999, paddingHorizontal: 10, paddingVertical: 3 },
  skillText: { fontSize: 11, fontWeight: '600', color: '#0051a2' },
  moreSkills: { fontSize: 11, color: '#8e8e93', alignSelf: 'center' },
  footer: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 },
  date: { fontSize: 11, color: '#c7c7cc' },
  analyzeBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#e3f0ff', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
  analyzeBtnText: { fontSize: 12, fontWeight: '600', color: '#0071e3' },
});
