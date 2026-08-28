import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  RefreshControl, ActivityIndicator,
} from 'react-native';
import { apiDashboard } from '../api';
import { useAuth } from '../context/AuthContext';
import { colors, spacing, radius, fontSize, fontWeight } from '../theme';

export default function DashboardScreen({ navigation }) {
  const { user, logout } = useAuth();
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await apiDashboard();
      setData(res.data);
    } catch (e) {
      console.log('Dashboard error', e?.message);
    } finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); }, []);

  const bmiLabel = (bmi) => {
    if (!bmi) return '';
    if (bmi < 18.5) return 'Underweight';
    if (bmi < 25)   return 'Healthy';
    if (bmi < 30)   return 'Overweight';
    return 'Obese';
  };

  const bmiColor = (bmi) => {
    if (!bmi) return colors.text3;
    if (bmi < 18.5) return colors.sky;
    if (bmi < 25)   return colors.secondary;
    if (bmi < 30)   return colors.tertiary;
    return colors.danger;
  };

  const muscleIcon = (muscle) => {
    const map = {
      chest:'🏋️', shoulders:'💪', biceps:'💪', triceps:'💪',
      abdominals:'🎯', quadriceps:'🦵', glutes:'🍑', hamstrings:'🦵',
      calves:'🦵', middle_back:'🔙', lower_back:'🔙', lats:'🔙',
    };
    return map[muscle] || '🏃';
  };

  if (loading) return (
    <View style={[s.container, { justifyContent: 'center', alignItems: 'center' }]}>
      <ActivityIndicator color={colors.primary} size="large" />
    </View>
  );

  const stats  = data?.stats  || {};
  const recent = data?.recent_activity || [];

  return (
    <ScrollView
      style={s.container}
      contentContainerStyle={s.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={colors.primary} />}
    >
      {/* Header */}
      <View style={s.header}>
        <View>
          <Text style={s.greeting}>GOOD {new Date().getHours() < 12 ? 'MORNING' : new Date().getHours() < 17 ? 'AFTERNOON' : 'EVENING'}</Text>
          <Text style={s.username}>{user?.username || 'Athlete'}</Text>
        </View>
        <TouchableOpacity onPress={logout} style={s.logoutBtn}>
          <Text style={s.logoutTxt}>⎋</Text>
        </TouchableOpacity>
      </View>

      {/* BMI Card */}
      {data?.bmi && (
        <View style={s.bmiCard}>
          <View style={s.bmiTop}>
            <Text style={s.bmiTitle}>Body Mass Index</Text>
            <Text style={s.bmiIcon}>📊</Text>
          </View>
          <View style={s.bmiValueRow}>
            <Text style={[s.bmiValue, { color: bmiColor(data.bmi) }]}>{data.bmi}</Text>
            <Text style={[s.bmiLabel, { color: bmiColor(data.bmi) }]}>{bmiLabel(data.bmi)}</Text>
          </View>
          {/* BMI bar */}
          <View style={s.bmiBar}>
            <View style={[s.bmiBarFill, { width: `${Math.min((data.bmi / 40) * 100, 100)}%`, backgroundColor: bmiColor(data.bmi) }]} />
          </View>
        </View>
      )}

      {/* BMR Card */}
      {data?.bmr && (
        <View style={[s.bmiCard, { marginTop: spacing.md }]}>
          <View style={s.bmiTop}>
            <Text style={s.bmiTitle}>Basal Metabolic Rate</Text>
            <Text style={s.bmiIcon}>🔥</Text>
          </View>
          <Text style={s.bmrValue}>{data.bmr.toLocaleString()} <Text style={s.bmrUnit}>kcal/day</Text></Text>
        </View>
      )}

      {/* Stats Row */}
      <View style={s.statsRow}>
        <View style={s.statBox}>
          <Text style={s.statIcon}>🏋️</Text>
          <Text style={s.statVal}>{stats.workouts || 0}</Text>
          <Text style={s.statLbl}>WORKOUTS</Text>
        </View>
        <View style={s.statBox}>
          <Text style={s.statIcon}>🔥</Text>
          <Text style={s.statVal}>{(stats.calories || 0) > 999 ? `${((stats.calories||0)/1000).toFixed(1)}k` : stats.calories || 0}</Text>
          <Text style={s.statLbl}>CALS BURNED</Text>
        </View>
        <View style={s.statBox}>
          <Text style={s.statIcon}>⏱</Text>
          <Text style={s.statVal}>{stats.minutes || 0}</Text>
          <Text style={s.statLbl}>MINUTES</Text>
        </View>
      </View>

      {/* Quick Actions */}
      <View style={s.quickRow}>
        <TouchableOpacity style={s.quickBtn} onPress={() => navigation.navigate('AIplan')}>
          <Text style={s.quickIcon}>🤖</Text>
          <Text style={s.quickLabel}>AI Plan</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.quickBtn} onPress={() => navigation.navigate('Search', { tab: 'map' })}>
          <Text style={s.quickIcon}>💪</Text>
          <Text style={s.quickLabel}>Muscle Map</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[s.quickBtn, s.quickBtnPrimary]} onPress={() => navigation.navigate('Activity')}>
          <Text style={s.quickIcon}>➕</Text>
          <Text style={[s.quickLabel, { color: colors.white }]}>Log Workout</Text>
        </TouchableOpacity>
      </View>

      {/* Recent Activity */}
      <View style={s.sectionHeader}>
        <Text style={s.sectionTitle}>Recent Activity</Text>
        <TouchableOpacity onPress={() => navigation.navigate('Activity')}>
          <Text style={s.viewAll}>VIEW ALL</Text>
        </TouchableOpacity>
      </View>

      {recent.length === 0 ? (
        <View style={s.emptyState}>
          <Text style={s.emptyIcon}>🏃</Text>
          <Text style={s.emptyText}>No workouts yet — log your first one!</Text>
        </View>
      ) : recent.map((item, i) => (
        <TouchableOpacity key={i} style={s.actCard} onPress={() => navigation.navigate('Activity')}>
          <View style={s.actIconWrap}>
            <Text style={s.actIcon}>{muscleIcon(item.muscle)}</Text>
          </View>
          <View style={s.actBody}>
            <Text style={s.actName}>{item.exercise}</Text>
            <View style={s.actMeta}>
              {item.sets  && <Text style={s.actTag}>{item.sets} SETS</Text>}
              {item.reps  && <Text style={s.actTag}>{item.reps} REPS</Text>}
              {item.duration && <Text style={s.actTag}>{item.duration} MIN</Text>}
            </View>
            {item.calories && <Text style={s.actCal}>🔥 {item.calories} kcal</Text>}
          </View>
          <Text style={s.actDate}>{item.date ? String(item.date).split('T')[0] : ''}</Text>
        </TouchableOpacity>
      ))}

    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content:   { padding: spacing.xl, paddingBottom: spacing.xxxl },

  header:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.xl },
  greeting:  { fontSize: fontSize.xs, color: colors.text3, fontWeight: fontWeight.bold, letterSpacing: 1.5 },
  username:  { fontSize: fontSize.xl, fontWeight: fontWeight.black, color: colors.white },
  logoutBtn: { backgroundColor: colors.bgCard2, borderRadius: radius.full, padding: spacing.sm },
  logoutTxt: { fontSize: fontSize.lg, color: colors.text2 },

  bmiCard:   {
    backgroundColor: colors.bgCard, borderRadius: radius.xl,
    padding: spacing.xl, borderWidth: 1, borderColor: colors.border,
  },
  bmiTop:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.sm },
  bmiTitle:  { fontSize: fontSize.base, color: colors.text2, fontWeight: fontWeight.semibold },
  bmiIcon:   { fontSize: fontSize.lg },
  bmiValueRow: { flexDirection: 'row', alignItems: 'baseline', gap: spacing.sm, marginBottom: spacing.md },
  bmiValue:  { fontSize: fontSize.xxxl, fontWeight: fontWeight.black },
  bmiLabel:  { fontSize: fontSize.base, fontWeight: fontWeight.bold },
  bmiBar:    { height: 6, backgroundColor: colors.bgCard2, borderRadius: radius.full, overflow: 'hidden' },
  bmiBarFill:{ height: 6, borderRadius: radius.full },
  bmrValue:  { fontSize: fontSize.xxl, fontWeight: fontWeight.black, color: colors.white },
  bmrUnit:   { fontSize: fontSize.sm, color: colors.text3, fontWeight: fontWeight.regular },

  statsRow:  { flexDirection: 'row', gap: spacing.md, marginTop: spacing.xl },
  statBox:   {
    flex: 1, backgroundColor: colors.bgCard, borderRadius: radius.xl,
    padding: spacing.md, alignItems: 'center', borderWidth: 1, borderColor: colors.border,
  },
  statIcon: { fontSize: fontSize.xl, marginBottom: spacing.xs },
  statVal:  { fontSize: fontSize.lg, fontWeight: fontWeight.black, color: colors.white },
  statLbl:  { fontSize: 9, color: colors.text3, fontWeight: fontWeight.bold, letterSpacing: 0.5, textAlign: 'center' },

  quickRow: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.xl },
  quickBtn: {
    flex: 1, backgroundColor: colors.bgCard, borderRadius: radius.xl,
    padding: spacing.md, alignItems: 'center', borderWidth: 1, borderColor: colors.border,
  },
  quickBtnPrimary: { backgroundColor: colors.primary, borderColor: colors.primary },
  quickIcon: { fontSize: fontSize.xl, marginBottom: spacing.xs },
  quickLabel:{ fontSize: fontSize.xs, color: colors.text2, fontWeight: fontWeight.bold },

  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: spacing.xxl, marginBottom: spacing.md },
  sectionTitle:  { fontSize: fontSize.md, fontWeight: fontWeight.bold, color: colors.white },
  viewAll:       { fontSize: fontSize.xs, color: colors.primary, fontWeight: fontWeight.bold, letterSpacing: 1 },

  emptyState: { backgroundColor: colors.bgCard, borderRadius: radius.xl, padding: spacing.xxl, alignItems: 'center', borderWidth: 1, borderColor: colors.border },
  emptyIcon:  { fontSize: 40, marginBottom: spacing.sm },
  emptyText:  { color: colors.text3, fontSize: fontSize.sm, textAlign: 'center' },

  actCard: {
    backgroundColor: colors.bgCard, borderRadius: radius.xl,
    padding: spacing.lg, marginBottom: spacing.md,
    borderWidth: 1, borderColor: colors.border,
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
  },
  actIconWrap: {
    width: 44, height: 44, borderRadius: radius.full,
    backgroundColor: `${colors.primary}22`, alignItems: 'center', justifyContent: 'center',
  },
  actIcon:  { fontSize: fontSize.lg },
  actBody:  { flex: 1 },
  actName:  { fontSize: fontSize.base, fontWeight: fontWeight.bold, color: colors.white, marginBottom: spacing.xs },
  actMeta:  { flexDirection: 'row', gap: spacing.xs, flexWrap: 'wrap' },
  actTag:   {
    fontSize: 10, color: colors.primary, fontWeight: fontWeight.bold,
    backgroundColor: `${colors.primary}20`, paddingHorizontal: spacing.sm,
    paddingVertical: 2, borderRadius: radius.sm,
  },
  actCal:   { fontSize: fontSize.xs, color: colors.tertiary, marginTop: spacing.xs },
  actDate:  { fontSize: fontSize.xs, color: colors.text3 },
});
