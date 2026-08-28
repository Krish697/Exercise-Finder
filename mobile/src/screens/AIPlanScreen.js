import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  TextInput, Alert, ActivityIndicator, FlatList,
} from 'react-native';
import { apiAIPlan, apiCreatePlan } from '../api';
import { colors, spacing, radius, fontSize, fontWeight } from '../theme';

const TEMPLATES = [
  { key: 'strength',    icon: '🏋️', label: 'Strength' },
  { key: 'hypertrophy', icon: '💪', label: 'Muscle' },
  { key: 'fat_loss',    icon: '🔥', label: 'Fat Burn' },
  { key: 'home',        icon: '🏠', label: 'Home' },
  { key: 'cardio',      icon: '🏃', label: 'Cardio' },
];
const LEVELS = ['beginner', 'intermediate', 'advanced', 'elite'];

export default function AIPlanScreen({ navigation }) {
  const [goal, setGoal]         = useState('');
  const [level, setLevel]       = useState('intermediate');
  const [loading, setLoading]   = useState(false);
  const [plan, setPlan]         = useState(null);
  const [saving, setSaving]     = useState(false);

  const generate = async (templateKey = '') => {
    setLoading(true);
    setPlan(null);
    try {
      const { data } = await apiAIPlan({
        goal: goal || templateKey,
        fitness_level: level,
        template_type: templateKey,
      });
      setPlan(data.plan);
    } catch {
      Alert.alert('Error', 'Failed to generate plan. Try again.');
    } finally { setLoading(false); }
  };

  const savePlan = async () => {
    if (!plan) return;
    setSaving(true);
    try {
      await apiCreatePlan({ ...plan, ai_generated: plan.ai_generated });
      Alert.alert('Saved! 🎉', 'Plan saved to your Plans.', [
        { text: 'Go to Plans', onPress: () => navigation.navigate('Plans') },
        { text: 'Stay here' },
      ]);
    } catch {
      Alert.alert('Error', 'Could not save plan.');
    } finally { setSaving(false); }
  };

  return (
    <ScrollView style={s.container} contentContainerStyle={s.content} showsVerticalScrollIndicator={false}>

      {/* Hero */}
      <View style={s.hero}>
        <Text style={s.heroSparkle}>✨</Text>
        <Text style={s.heroTitle}>Design Your{'\n'}Perfect Routine</Text>
        <Text style={s.heroSub}>AI analyzes your goals and creates a tailored plan</Text>
      </View>

      {/* Goal input */}
      <View style={s.card}>
        <Text style={s.label}>Describe your goal...</Text>
        <TextInput
          style={s.input}
          placeholder="e.g. Build upper body strength with dumbbells"
          placeholderTextColor={colors.text3}
          value={goal}
          onChangeText={setGoal}
          multiline numberOfLines={2}
        />

        <Text style={[s.label, { marginTop: spacing.lg }]}>Fitness Level</Text>
        <View style={s.levelRow}>
          {LEVELS.map(l => (
            <TouchableOpacity
              key={l}
              style={[s.levelBtn, level === l && s.levelBtnActive]}
              onPress={() => setLevel(l)}
            >
              <Text style={[s.levelText, level === l && s.levelTextActive]}>
                {l.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity style={[s.genBtn, loading && s.genBtnDisabled]} onPress={() => generate()} disabled={loading}>
          {loading
            ? <ActivityIndicator color="#fff" />
            : <Text style={s.genBtnText}>✨ Generate AI Plan</Text>
          }
        </TouchableOpacity>
      </View>

      {/* Quick Templates */}
      <Text style={s.sectionTitle}>Quick Templates</Text>
      <View style={s.templateGrid}>
        {TEMPLATES.map(t => (
          <TouchableOpacity key={t.key} style={s.templateBtn} onPress={() => generate(t.key)}>
            <Text style={s.templateIcon}>{t.icon}</Text>
            <Text style={s.templateLabel}>{t.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Generated Plan Preview */}
      {plan && (
        <View style={s.planCard}>
          <View style={s.planHeader}>
            <View style={{ flex: 1 }}>
              <Text style={s.planName}>{plan.name}</Text>
              {plan.description && <Text style={s.planDesc}>{plan.description}</Text>}
            </View>
            {plan.ai_generated && (
              <View style={s.aiBadge}><Text style={s.aiBadgeText}>🤖 AI</Text></View>
            )}
          </View>

          {(plan.exercises || []).map((ex, i) => (
            <View key={i} style={s.exRow}>
              <View style={{ flex: 1 }}>
                <Text style={s.exName}>{ex.name}</Text>
                {ex.instructions ? (
                  <Text style={s.exInstr} numberOfLines={1}>{ex.instructions}</Text>
                ) : null}
              </View>
              <View style={s.exRight}>
                <Text style={s.exSetsReps}>{ex.sets}×{ex.reps}</Text>
                {ex.muscle ? <Text style={s.exMuscle}>{ex.muscle.replace('_',' ')}</Text> : null}
              </View>
            </View>
          ))}

          <View style={s.planActions}>
            <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.7 }]} onPress={savePlan} disabled={saving}>
              {saving
                ? <ActivityIndicator color="#fff" size="small" />
                : <Text style={s.saveBtnText}>💾 Save &amp; Start Checklist</Text>
              }
            </TouchableOpacity>
            <TouchableOpacity style={s.regenBtn} onPress={() => generate()}>
              <Text style={s.regenBtnText}>🔄</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content:   { padding: spacing.xl, paddingBottom: 80 },

  hero: { alignItems: 'center', marginBottom: spacing.xl },
  heroSparkle: { fontSize: 40, marginBottom: spacing.sm },
  heroTitle: {
    fontSize: fontSize.xxl, fontWeight: fontWeight.black, color: colors.white,
    textAlign: 'center', lineHeight: 34,
  },
  heroSub: { fontSize: fontSize.sm, color: colors.text3, textAlign: 'center', marginTop: spacing.sm, lineHeight: 20 },

  card: {
    backgroundColor: colors.bgCard, borderRadius: radius.xl,
    padding: spacing.xl, borderWidth: 1, borderColor: colors.border,
    marginBottom: spacing.xl,
  },
  label: { fontSize: fontSize.sm, color: colors.text2, fontWeight: fontWeight.semibold, marginBottom: spacing.sm },
  input: {
    backgroundColor: colors.bgInput, borderRadius: radius.md,
    padding: spacing.md, color: colors.text, fontSize: fontSize.base,
    borderWidth: 1, borderColor: colors.border, minHeight: 70,
    textAlignVertical: 'top',
  },

  levelRow: { flexDirection: 'row', gap: spacing.sm, flexWrap: 'wrap', marginBottom: spacing.lg },
  levelBtn: {
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
    borderRadius: radius.md, backgroundColor: colors.bgCard2,
    borderWidth: 1, borderColor: colors.border,
  },
  levelBtnActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  levelText:      { fontSize: fontSize.xs, fontWeight: fontWeight.bold, color: colors.text3 },
  levelTextActive:{ color: colors.white },

  genBtn: {
    backgroundColor: colors.primary, borderRadius: radius.md,
    paddingVertical: spacing.md, alignItems: 'center',
  },
  genBtnDisabled: { opacity: 0.7 },
  genBtnText: { color: colors.white, fontSize: fontSize.md, fontWeight: fontWeight.bold },

  sectionTitle: { fontSize: fontSize.md, fontWeight: fontWeight.bold, color: colors.white, marginBottom: spacing.md },
  templateGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, marginBottom: spacing.xl },
  templateBtn: {
    width: '30%', aspectRatio: 1, backgroundColor: colors.bgCard,
    borderRadius: radius.xl, alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: colors.border, gap: spacing.xs,
  },
  templateIcon:  { fontSize: fontSize.xxl },
  templateLabel: { fontSize: fontSize.xs, color: colors.text2, fontWeight: fontWeight.bold },

  planCard: {
    backgroundColor: colors.bgCard, borderRadius: radius.xl,
    padding: spacing.xl, borderWidth: 1, borderColor: colors.primaryD,
    marginTop: spacing.md,
  },
  planHeader:    { flexDirection: 'row', alignItems: 'flex-start', marginBottom: spacing.lg },
  planName:      { fontSize: fontSize.lg, fontWeight: fontWeight.black, color: colors.white },
  planDesc:      { fontSize: fontSize.sm, color: colors.text3, marginTop: spacing.xs },
  aiBadge:       { backgroundColor: `${colors.purple}33`, borderRadius: radius.full, paddingHorizontal: spacing.md, paddingVertical: 3 },
  aiBadgeText:   { fontSize: fontSize.xs, color: colors.purple, fontWeight: fontWeight.bold },

  exRow: {
    flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.md,
    borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  exName:    { fontSize: fontSize.sm, fontWeight: fontWeight.bold, color: colors.white },
  exInstr:   { fontSize: fontSize.xs, color: colors.text3, marginTop: 2 },
  exRight:   { alignItems: 'flex-end' },
  exSetsReps:{ fontSize: fontSize.base, fontWeight: fontWeight.black, color: colors.primaryL },
  exMuscle:  { fontSize: 10, color: colors.text3, textTransform: 'capitalize' },

  planActions: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.lg },
  saveBtn: {
    flex: 1, backgroundColor: colors.primary, borderRadius: radius.md,
    paddingVertical: spacing.md, alignItems: 'center',
  },
  saveBtnText: { color: colors.white, fontWeight: fontWeight.bold, fontSize: fontSize.sm },
  regenBtn: {
    backgroundColor: colors.bgCard2, borderRadius: radius.md,
    paddingHorizontal: spacing.lg, justifyContent: 'center',
    borderWidth: 1, borderColor: colors.border,
  },
  regenBtnText: { fontSize: fontSize.lg },
});
