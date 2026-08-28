import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  TextInput, ActivityIndicator, Alert, RefreshControl,
} from 'react-native';
import { apiGetProfile, apiUpdateProfile, apiDashboard } from '../api';
import { useAuth } from '../context/AuthContext';
import { colors, spacing, radius, fontSize, fontWeight } from '../theme';

export default function ProfileScreen() {
  const { logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [stats, setStats]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving]   = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Edit fields
  const [age, setAge]       = useState('');
  const [gender, setGender] = useState('');
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');

  const load = useCallback(async () => {
    try {
      const [pRes, dRes] = await Promise.all([apiGetProfile(), apiDashboard()]);
      const p = pRes.data;
      setProfile(p);
      setAge(p.age ? String(p.age) : '');
      setGender(p.gender || 'male');
      setHeight(p.height ? String(p.height) : '');
      setWeight(p.weight ? String(p.weight) : '');
      setStats(dRes.data.stats || { workouts: 0 });
    } catch {
      console.log('Profile load error');
    } finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiUpdateProfile({
        age: parseInt(age) || null,
        gender: gender.toLowerCase(),
        height: parseFloat(height) || null,
        weight: parseFloat(weight) || null,
      });
      Alert.alert('Success', 'Profile updated');
      load();
    } catch {
      Alert.alert('Error', 'Could not update profile');
    } finally { setSaving(false); }
  };

  if (loading) return <View style={s.center}><ActivityIndicator color={colors.primary} size="large" /></View>;

  const bmi = profile?.height && profile?.weight
    ? (profile.weight / Math.pow(profile.height / 100, 2)).toFixed(1)
    : null;

  return (
    <ScrollView
      style={s.container} contentContainerStyle={s.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={colors.primary} />}
    >
      {/* Avatar Header */}
      <View style={s.header}>
        <View style={s.avatarWrap}>
          <Text style={s.avatarText}>{profile?.username ? profile.username[0].toUpperCase() : 'A'}</Text>
          <View style={s.avatarGlow} />
        </View>
        <Text style={s.name}>{profile?.username || 'Athlete'}</Text>
        <View style={s.badge}><Text style={s.badgeText}>Elite Athlete ✏️</Text></View>
      </View>

      {/* Stats row */}
      <View style={s.statsRow}>
        <View style={s.statBox}>
          <Text style={s.statLbl}>WORKOUTS</Text>
          <Text style={s.statVal}>{stats?.workouts || 0}</Text>
        </View>
        <View style={s.statBox}>
          <Text style={s.statLbl}>STREAK</Text>
          <Text style={[s.statVal, { color: colors.secondary }]}>12</Text>
        </View>
        <View style={s.statBox}>
          <Text style={s.statLbl}>RANK</Text>
          <Text style={[s.statVal, { color: colors.tertiary }]}>Gold</Text>
        </View>
      </View>

      {/* Body Metrics Form */}
      <View style={s.card}>
        <Text style={s.cardTitle}>Body Metrics</Text>

        <View style={s.row}>
          <View style={s.fieldWrap}>
            <Text style={s.label}>Age</Text>
            <TextInput style={s.input} value={age} onChangeText={setAge} keyboardType="numeric" placeholder="28" placeholderTextColor={colors.text3} />
          </View>
          <View style={s.fieldWrap}>
            <Text style={s.label}>Gender</Text>
            <View style={s.genderRow}>
              <TouchableOpacity style={[s.genBtn, gender==='male' && s.genBtnActive]} onPress={()=>setGender('male')}>
                <Text style={[s.genText, gender==='male' && s.genTextActive]}>Male</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[s.genBtn, gender==='female' && s.genBtnActive]} onPress={()=>setGender('female')}>
                <Text style={[s.genText, gender==='female' && s.genTextActive]}>Female</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>

        <View style={s.row}>
          <View style={s.fieldWrap}>
            <Text style={s.label}>Height (cm)</Text>
            <TextInput style={s.input} value={height} onChangeText={setHeight} keyboardType="numeric" placeholder="182" placeholderTextColor={colors.text3} />
          </View>
          <View style={s.fieldWrap}>
            <Text style={s.label}>Weight (kg)</Text>
            <TextInput style={s.input} value={weight} onChangeText={setWeight} keyboardType="numeric" placeholder="78.5" placeholderTextColor={colors.text3} />
          </View>
        </View>

        {/* BMI Readout */}
        {bmi && (
          <View style={s.bmiWrap}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.xs }}>
              <Text style={s.bmiText}>BMI: {bmi}</Text>
              <Text style={[s.bmiText, { color: bmi < 25 ? colors.secondary : colors.tertiary }]}>
                {bmi < 18.5 ? 'Underweight' : bmi < 25 ? 'Normal' : bmi < 30 ? 'Overweight' : 'Obese'}
              </Text>
            </View>
            <View style={s.bmiBar}>
              <View style={[s.bmiFill, { width: `${Math.min((bmi/40)*100, 100)}%`, backgroundColor: bmi < 25 ? colors.secondary : colors.tertiary }]} />
            </View>
          </View>
        )}

        <TouchableOpacity style={[s.saveBtn, saving && {opacity:0.7}]} onPress={handleSave} disabled={saving}>
          {saving ? <ActivityIndicator color="#fff" /> : <Text style={s.saveBtnText}>Save Changes</Text>}
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={s.logoutBtn} onPress={logout}>
        <Text style={s.logoutText}>Log Out</Text>
      </TouchableOpacity>

    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  center:    { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.bg },
  content:   { padding: spacing.xl, paddingBottom: 100 },

  header: { alignItems: 'center', marginTop: spacing.xl, marginBottom: spacing.xxl },
  avatarWrap: {
    width: 100, height: 100, borderRadius: radius.full,
    backgroundColor: colors.bgCard2, alignItems: 'center', justifyContent: 'center',
    borderWidth: 2, borderColor: colors.primary, marginBottom: spacing.md,
    zIndex: 2,
  },
  avatarText: { fontSize: 40, fontWeight: fontWeight.bold, color: colors.white },
  avatarGlow: {
    position: 'absolute', top: -10, left: -10, right: -10, bottom: -10,
    borderRadius: radius.full, borderWidth: 1, borderColor: colors.primaryL, opacity: 0.3, zIndex: 1,
  },
  name: { fontSize: fontSize.xxl, fontWeight: fontWeight.black, color: colors.white, letterSpacing: 1, textTransform: 'uppercase' },
  badge: { backgroundColor: colors.bgCard2, paddingHorizontal: spacing.md, paddingVertical: 4, borderRadius: radius.full, marginTop: spacing.sm },
  badgeText: { fontSize: fontSize.xs, color: colors.primaryL, fontWeight: fontWeight.bold },

  statsRow: { flexDirection: 'row', gap: spacing.md, marginBottom: spacing.xxl },
  statBox: {
    flex: 1, backgroundColor: colors.bgCard, borderRadius: radius.xl,
    alignItems: 'center', paddingVertical: spacing.lg,
    borderWidth: 1, borderColor: colors.border,
  },
  statLbl: { fontSize: 9, color: colors.text3, fontWeight: fontWeight.black, letterSpacing: 1, marginBottom: spacing.xs },
  statVal: { fontSize: fontSize.xl, fontWeight: fontWeight.black, color: colors.white },

  card: {
    backgroundColor: colors.bgCard, borderRadius: radius.xl,
    padding: spacing.xl, borderWidth: 1, borderColor: colors.border,
    marginBottom: spacing.xl,
  },
  cardTitle: { fontSize: fontSize.lg, fontWeight: fontWeight.bold, color: colors.white, marginBottom: spacing.lg },
  row: { flexDirection: 'row', gap: spacing.md, marginBottom: spacing.md },
  fieldWrap: { flex: 1 },
  label: { fontSize: fontSize.xs, color: colors.text2, fontWeight: fontWeight.bold, marginBottom: spacing.xs },
  input: {
    backgroundColor: colors.bgInput, borderRadius: radius.md, padding: spacing.md,
    color: colors.white, fontSize: fontSize.md, fontWeight: fontWeight.bold,
  },
  genderRow: { flexDirection: 'row', gap: spacing.xs, height: 50 },
  genBtn: {
    flex: 1, backgroundColor: colors.bgInput, borderRadius: radius.md,
    alignItems: 'center', justifyContent: 'center',
  },
  genBtnActive: { backgroundColor: colors.primary },
  genText: { fontSize: fontSize.sm, color: colors.text3, fontWeight: fontWeight.bold },
  genTextActive: { color: colors.white },

  bmiWrap: { marginTop: spacing.md, marginBottom: spacing.lg },
  bmiText: { fontSize: fontSize.xs, fontWeight: fontWeight.bold, color: colors.text2 },
  bmiBar: { height: 6, backgroundColor: colors.bgInput, borderRadius: radius.full, overflow: 'hidden' },
  bmiFill: { height: '100%', borderRadius: radius.full },

  saveBtn: {
    backgroundColor: colors.primary, borderRadius: radius.md,
    paddingVertical: spacing.md, alignItems: 'center', marginTop: spacing.sm,
  },
  saveBtnText: { color: colors.white, fontWeight: fontWeight.bold, fontSize: fontSize.md },

  logoutBtn: { padding: spacing.lg, alignItems: 'center' },
  logoutText: { color: colors.danger, fontSize: fontSize.md, fontWeight: fontWeight.bold },
});
