import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function StatBar({ stats }) {
  return (
    <View style={styles.container}>
      <Stat icon="mail" label="Total" value={stats.total} color="#0071e3" />
      <View style={styles.divider} />
      <Stat icon="laptop-outline" label="Remote" value={stats.remote} color="#30a46c" />
      <View style={styles.divider} />
      <Stat icon="sparkles" label="Analyzed" value={stats.analyzed} color="#6419a0" />
    </View>
  );
}

function Stat({ icon, label, value, color }) {
  return (
    <View style={styles.stat}>
      <Ionicons name={icon} size={18} color={color} />
      <Text style={styles.value}>{value}</Text>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#f2f2f7',
  },
  stat: { alignItems: 'center', gap: 2 },
  value: { fontSize: 20, fontWeight: '700', color: '#1d1d1f', letterSpacing: -0.5 },
  label: { fontSize: 11, color: '#8e8e93', fontWeight: '500' },
  divider: { width: 1, height: 32, backgroundColor: '#e5e5ea' },
});
