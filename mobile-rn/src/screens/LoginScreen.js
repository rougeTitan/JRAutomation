import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, SafeAreaView,
} from 'react-native';
import * as WebBrowser from 'expo-web-browser';
import * as AuthSession from 'expo-auth-session/providers/google';
import { Ionicons } from '@expo/vector-icons';
import { saveTokens, saveUserEmail } from '../utils/storage';

WebBrowser.maybeCompleteAuthSession();

// ── Get these from Google Cloud Console → OAuth 2.0 Clients (Android) ─────
const ANDROID_CLIENT_ID = '608251097092-90m74jqnjrhmt01vtfj87qlooclqom3p.apps.googleusercontent.com';
const IOS_CLIENT_ID = 'YOUR_IOS_CLIENT_ID.apps.googleusercontent.com';

export default function LoginScreen({ onSignIn }) {
  const [loading, setLoading] = useState(false);

  const [request, response, promptAsync] = AuthSession.useAuthRequest({
    androidClientId: ANDROID_CLIENT_ID,
    iosClientId: IOS_CLIENT_ID,
    scopes: [
      'https://www.googleapis.com/auth/gmail.modify',
      'https://www.googleapis.com/auth/userinfo.email',
    ],
  });

  React.useEffect(() => {
    if (response?.type === 'success') {
      handleAuthSuccess(response.authentication);
    } else if (response?.type === 'error') {
      Alert.alert('Sign-in failed', response.error?.message || 'Unknown error');
      setLoading(false);
    }
  }, [response]);

  async function handleAuthSuccess(auth) {
    try {
      await saveTokens({
        accessToken: auth.accessToken,
        refreshToken: auth.refreshToken,
        expiresIn: auth.expiresIn,
      });

      const userRes = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      });
      const user = await userRes.json();
      await saveUserEmail(user.email || '');

      onSignIn();
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  }

  function handleSignIn() {
    setLoading(true);
    promptAsync();
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.iconWrap}>
          <Ionicons name="briefcase" size={56} color="#ffffff" />
        </View>
        <Text style={styles.title}>JobAI</Text>
        <Text style={styles.subtitle}>
          AI-powered recruiter email analyzer.{'\n'}Sign in with Gmail to get started.
        </Text>

        <TouchableOpacity
          style={[styles.signInBtn, loading && styles.signInBtnDisabled]}
          onPress={handleSignIn}
          disabled={loading || !request}
          activeOpacity={0.85}
        >
          {loading ? (
            <ActivityIndicator color="#1d1d1f" />
          ) : (
            <>
              <Ionicons name="logo-google" size={20} color="#1d1d1f" style={{ marginRight: 10 }} />
              <Text style={styles.signInText}>Sign in with Google</Text>
            </>
          )}
        </TouchableOpacity>

        <Text style={styles.note}>
          Only reads recruiter emails. API keys stored securely on your device.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1d1d1f' },
  content: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 32 },
  iconWrap: {
    width: 100, height: 100, borderRadius: 24,
    backgroundColor: '#0071e3',
    alignItems: 'center', justifyContent: 'center', marginBottom: 28,
  },
  title: { fontSize: 36, fontWeight: '700', color: '#ffffff', letterSpacing: -0.5 },
  subtitle: {
    fontSize: 15, color: 'rgba(255,255,255,0.55)',
    textAlign: 'center', marginTop: 12, lineHeight: 22,
  },
  signInBtn: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#ffffff', borderRadius: 14,
    paddingVertical: 16, paddingHorizontal: 32,
    marginTop: 48, width: '100%', justifyContent: 'center',
  },
  signInBtnDisabled: { opacity: 0.6 },
  signInText: { fontSize: 16, fontWeight: '600', color: '#1d1d1f' },
  note: {
    fontSize: 12, color: 'rgba(255,255,255,0.3)',
    textAlign: 'center', marginTop: 24, lineHeight: 18,
  },
});
