import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator, Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiLogin, apiRegister } from '../api';
import { useAuth } from '../context/AuthContext';
import { colors, spacing, radius, fontSize, fontWeight } from '../theme';

export default function AuthScreen() {
  const { login } = useAuth();
  const [tab, setTab]           = useState('login');   // 'login' | 'register'
  const [username, setUsername] = useState('');
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading]   = useState(false);
  const [showPw, setShowPw]     = useState(false);

  const handleLogin = async () => {
    if (!email || !password) { Alert.alert('Error', 'Enter email and password'); return; }
    setLoading(true);
    try {
      const { data } = await apiLogin(email.trim().toLowerCase(), password);
      if (data.success) await login(data);
      else Alert.alert('Login Failed', data.error || 'Invalid credentials');
    } catch (e) {
      Alert.alert('Error', e?.response?.data?.error || 'Network error — is the server running?');
    } finally { setLoading(false); }
  };

  const handleRegister = async () => {
    if (!username || !email || !password) { Alert.alert('Error', 'All fields are required'); return; }
    if (password.length < 6) { Alert.alert('Error', 'Password must be at least 6 characters'); return; }
    setLoading(true);
    try {
      const { data } = await apiRegister(username.trim(), email.trim().toLowerCase(), password);
      if (data.success) {
        Alert.alert('Account Created!', 'You can now log in.', [
          { text: 'OK', onPress: () => setTab('login') }
        ]);
      } else Alert.alert('Error', data.error || 'Registration failed');
    } catch (e) {
      Alert.alert('Error', e?.response?.data?.error || 'Network error');
    } finally { setLoading(false); }
  };

  return (
    <KeyboardAvoidingView
      style={s.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={s.container} keyboardShouldPersistTaps="handled">

        {/* Logo */}
        <View style={s.heroWrap}>
          <Text style={s.heroIcon}>💪</Text>
          <Text style={s.heroTitle}>ELITE{'\n'}PERFORMANCE</Text>
          <Text style={s.heroSub}>Your personal fitness companion</Text>
        </View>

        {/* Tab switcher */}
        <View style={s.tabs}>
          <TouchableOpacity
            style={[s.tab, tab === 'login' && s.tabActive]}
            onPress={() => setTab('login')}
          >
            <Text style={[s.tabText, tab === 'login' && s.tabTextActive]}>Log In</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[s.tab, tab === 'register' && s.tabActive]}
            onPress={() => setTab('register')}
          >
            <Text style={[s.tabText, tab === 'register' && s.tabTextActive]}>Sign Up</Text>
          </TouchableOpacity>
        </View>

        {/* Form */}
        <View style={s.card}>
          {tab === 'register' && (
            <View style={s.field}>
              <Text style={s.label}>Name</Text>
              <TextInput
                style={s.input}
                placeholder="Your name"
                placeholderTextColor={colors.text3}
                value={username}
                onChangeText={setUsername}
                autoCapitalize="words"
              />
            </View>
          )}

          <View style={s.field}>
            <Text style={s.label}>Email</Text>
            <TextInput
              style={s.input}
              placeholder="you@example.com"
              placeholderTextColor={colors.text3}
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
            />
          </View>

          <View style={s.field}>
            <Text style={s.label}>Password</Text>
            <View style={s.pwRow}>
              <TextInput
                style={[s.input, s.pwInput]}
                placeholder="••••••••"
                placeholderTextColor={colors.text3}
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPw}
              />
              <TouchableOpacity style={s.eyeBtn} onPress={() => setShowPw(!showPw)}>
                <Text>{showPw ? '🙈' : '👁️'}</Text>
              </TouchableOpacity>
            </View>
          </View>

          <TouchableOpacity
            style={[s.submitBtn, loading && s.submitBtnDisabled]}
            onPress={tab === 'login' ? handleLogin : handleRegister}
            disabled={loading}
          >
            {loading
              ? <ActivityIndicator color="#fff" />
              : <Text style={s.submitText}>{tab === 'login' ? 'Log In' : 'Create Account'}</Text>
            }
          </TouchableOpacity>
        </View>

      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  flex:          { flex: 1, backgroundColor: colors.bg },
  container:     { flexGrow: 1, padding: spacing.xl, justifyContent: 'center' },

  heroWrap:      { alignItems: 'center', marginBottom: spacing.xxl },
  heroIcon:      { fontSize: 52, marginBottom: spacing.sm },
  heroTitle:     {
    fontSize: fontSize.xxxl, fontWeight: fontWeight.black,
    color: colors.primary, textAlign: 'center', letterSpacing: 3,
    fontStyle: 'italic', lineHeight: 44,
  },
  heroSub:       { fontSize: fontSize.sm, color: colors.text3, marginTop: spacing.sm },

  tabs: {
    flexDirection: 'row', backgroundColor: colors.bgCard2,
    borderRadius: radius.lg, padding: 4, marginBottom: spacing.xl,
  },
  tab: {
    flex: 1, paddingVertical: spacing.sm,
    alignItems: 'center', borderRadius: radius.md,
  },
  tabActive:     { backgroundColor: colors.primary },
  tabText:       { fontSize: fontSize.base, fontWeight: fontWeight.semibold, color: colors.text3 },
  tabTextActive: { color: colors.white },

  card: {
    backgroundColor: colors.bgCard, borderRadius: radius.xl,
    padding: spacing.xl, borderWidth: 1, borderColor: colors.border,
  },
  field:    { marginBottom: spacing.lg },
  label:    { fontSize: fontSize.sm, color: colors.text2, fontWeight: fontWeight.semibold, marginBottom: spacing.xs },
  input: {
    backgroundColor: colors.bgInput, borderRadius: radius.md,
    padding: spacing.md, color: colors.text,
    fontSize: fontSize.base, borderWidth: 1, borderColor: colors.border,
  },
  pwRow:    { flexDirection: 'row', alignItems: 'center' },
  pwInput:  { flex: 1 },
  eyeBtn:   { position: 'absolute', right: spacing.md, padding: spacing.xs },

  submitBtn: {
    backgroundColor: colors.primary, borderRadius: radius.md,
    paddingVertical: spacing.md, alignItems: 'center',
    marginTop: spacing.sm,
  },
  submitBtnDisabled: { opacity: 0.7 },
  submitText: {
    color: colors.white, fontSize: fontSize.md,
    fontWeight: fontWeight.bold,
  },
});
