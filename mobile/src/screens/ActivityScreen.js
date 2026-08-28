import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, TouchableOpacity,
  RefreshControl, ActivityIndicator, Alert, TextInput,
} from 'react-native';
import { apiTimeline, apiDeleteWorkout, apiAddWorkout } from '../api';
import { colors, spacing, radius, fontSize, fontWeight, muscleColors } from '../theme';

export default function ActivityScreen() {
  const [history, setHistory]     = useState([]);
  const [loading, setLoading]     = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showLogForm, setShowLogForm] = useState(false);

  // Form
  const [name, setName]     = useState('');
  const [sets, setSets]     = useState('3');
  const [reps, setReps]     = useState('10');
  const [mins, setMins]     = useState('30');
  const [cals, setCals]     = useState('100');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const { data } = await apiTimeline();
      setHistory(data.history || []);
    } catch {
      console.log('Error loading timeline');
    } finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); }, []);

  const handleDelete = (id) => {
    Alert.alert('Delete Entry', 'Remove this workout from your history?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: async () => {
          try {
            await apiDeleteWorkout(id);
            load();
          } catch { Alert.alert('Error', 'Could not delete entry.'); }
        }
      }
    ]);
  };

  const handleSave = async () => {
    if (!name.trim()) return Alert.alert('Error', 'Exercise name is required');
    setSaving(true);
    try {
      await apiAddWorkout({
        exercise_name: name.trim(),
        sets: parseInt(sets) || 1,
        reps: parseInt(reps) || 1,
        duration: parseInt(mins) || 10,
        calories: parseInt(cals) || 50,
      });
      setShowLogForm(false);
      setName(''); setSets('3'); setReps('10'); setMins('30'); setCals('100');
      load();
    } catch {
      Alert.alert('Error', 'Could not save workout.');
    } finally { setSaving(false); }
  };

  const renderItem = ({ item }) => {
    const musColor = muscleColors[item.muscle_group] || colors.primary;
    const dateStr = item.date ? String(item.date).replace('T', ' ').substring(0, 16) : '';

    return (
      <View style={s.card}>
        <View style={s.cardTop}>
          <View style={[s.iconWrap, { backgroundColor: `${musColor}22` }]}>
            <Text style={s.icon}>🏋️</Text>
          </View>
          <View style={s.cardBody}>
            <Text style={s.name}>{item.exercise_name}</Text>
            <View style={s.tagsRow}>
              {item.muscle_group && (
                <View style={[s.tag, { backgroundColor: `${musColor}22` }]}>
                  <Text style={[s.tagText, { color: musColor }]}>{item.muscle_group.replace('_', ' ')}</Text>
                </View>
              )}
              <View style={[s.tag, { backgroundColor: `${colors.tertiary}22` }]}>
                <Text style={[s.tagText, { color: colors.tertiary }]}>{item.duration} min</Text>
              </View>
              {item.sets && item.reps ? (
                <View style={[s.tag, { backgroundColor: `${colors.secondary}22` }]}>
                  <Text style={[s.tagText, { color: colors.secondary }]}>{item.sets}×{item.reps}</Text>
                </View>
              ) : null}
            </View>
          </View>
          <TouchableOpacity onPress={() => handleDelete(item.id)} style={s.delBtn}>
            <Text style={s.delText}>×</Text>
          </TouchableOpacity>
        </View>

        <View style={s.cardBottom}>
          <Text style={s.date}>{dateStr}</Text>
          {item.calories ? (
            <View style={s.calBadge}>
              <Text style={s.calIcon}>🔥</Text>
              <Text style={s.calText}>{item.calories} kcal</Text>
            </View>
          ) : null}
        </View>
      </View>
    );
  };

  if (loading) return <View style={s.center}><ActivityIndicator color={colors.primary} size="large" /></View>;

  return (
    <View style={s.container}>
      {/* Header */}
      <View style={s.header}>
        <Text style={s.title}>Timeline</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => setShowLogForm(!showLogForm)}>
          <Text style={s.addBtnText}>{showLogForm ? 'Cancel' : '+ Log Workout'}</Text>
        </TouchableOpacity>
      </View>

      {/* Manual Log Form */}
      {showLogForm && (
        <View style={s.form}>
          <Text style={s.formTitle}>Manual Log</Text>
          <TextInput style={s.input} placeholder="Exercise Name (e.g. Bench Press)" placeholderTextColor={colors.text3} value={name} onChangeText={setName} />
          <View style={s.row}>
            <TextInput style={[s.input, { flex: 1 }]} placeholder="Sets" placeholderTextColor={colors.text3} keyboardType="numeric" value={sets} onChangeText={setSets} />
            <TextInput style={[s.input, { flex: 1 }]} placeholder="Reps" placeholderTextColor={colors.text3} keyboardType="numeric" value={reps} onChangeText={setReps} />
          </View>
          <View style={s.row}>
            <TextInput style={[s.input, { flex: 1 }]} placeholder="Mins" placeholderTextColor={colors.text3} keyboardType="numeric" value={mins} onChangeText={setMins} />
            <TextInput style={[s.input, { flex: 1 }]} placeholder="Cals" placeholderTextColor={colors.text3} keyboardType="numeric" value={cals} onChangeText={setCals} />
          </View>
          <TouchableOpacity style={[s.saveBtn, saving && {opacity:0.7}]} onPress={handleSave} disabled={saving}>
            {saving ? <ActivityIndicator color="#fff" /> : <Text style={s.saveBtnText}>Save Entry</Text>}
          </TouchableOpacity>
        </View>
      )}

      {/* Timeline List */}
      <FlatList
        data={history}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        contentContainerStyle={s.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={colors.primary} />}
        ListEmptyComponent={
          <View style={s.emptyState}>
            <Text style={s.emptyIcon}>📅</Text>
            <Text style={s.emptyText}>No activity found. Time to get moving!</Text>
          </View>
        }
      />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  center:    { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.bg },

  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    padding: spacing.xl, paddingBottom: spacing.md,
  },
  title: { fontSize: fontSize.xxl, fontWeight: fontWeight.black, color: colors.white },
  addBtn: {
    backgroundColor: colors.primary, borderRadius: radius.full,
    paddingHorizontal: spacing.lg, paddingVertical: spacing.sm,
  },
  addBtnText: { color: colors.white, fontWeight: fontWeight.bold, fontSize: fontSize.sm },

  form: {
    backgroundColor: colors.bgCard, marginHorizontal: spacing.xl,
    borderRadius: radius.xl, padding: spacing.lg, marginBottom: spacing.md,
    borderWidth: 1, borderColor: colors.border,
  },
  formTitle: { fontSize: fontSize.md, fontWeight: fontWeight.bold, color: colors.white, marginBottom: spacing.md },
  input: {
    backgroundColor: colors.bgInput, borderRadius: radius.md,
    padding: spacing.md, color: colors.text, fontSize: fontSize.base,
    borderWidth: 1, borderColor: colors.border, marginBottom: spacing.sm,
  },
  row: { flexDirection: 'row', gap: spacing.sm },
  saveBtn: {
    backgroundColor: colors.primary, borderRadius: radius.md,
    paddingVertical: spacing.md, alignItems: 'center', marginTop: spacing.xs,
  },
  saveBtnText: { color: colors.white, fontWeight: fontWeight.bold, fontSize: fontSize.md },

  list: { padding: spacing.xl, paddingTop: 0, gap: spacing.md, paddingBottom: 80 },

  card: {
    backgroundColor: colors.bgCard, borderRadius: radius.xl,
    borderWidth: 1, borderColor: colors.border, padding: spacing.lg,
  },
  cardTop: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: spacing.md },
  iconWrap: { width: 44, height: 44, borderRadius: radius.lg, alignItems: 'center', justifyContent: 'center', marginRight: spacing.md },
  icon: { fontSize: fontSize.lg },
  cardBody: { flex: 1 },
  name: { fontSize: fontSize.md, fontWeight: fontWeight.bold, color: colors.white, marginBottom: spacing.xs },
  tagsRow: { flexDirection: 'row', gap: spacing.xs, flexWrap: 'wrap' },
  tag: { paddingHorizontal: spacing.sm, paddingVertical: 3, borderRadius: radius.sm },
  tagText: { fontSize: 10, fontWeight: fontWeight.bold, textTransform: 'uppercase' },

  delBtn: { padding: spacing.xs, marginLeft: spacing.sm },
  delText: { color: colors.text3, fontSize: fontSize.xl, lineHeight: 22 },

  cardBottom: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    borderTopWidth: 1, borderTopColor: colors.border, paddingTop: spacing.sm, marginTop: spacing.xs,
  },
  date: { fontSize: fontSize.xs, color: colors.text3, fontWeight: fontWeight.semibold },
  calBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: `${colors.tertiary}15`, paddingHorizontal: spacing.sm, paddingVertical: 4, borderRadius: radius.full },
  calIcon: { fontSize: 12, marginRight: 4 },
  calText: { color: colors.tertiary, fontSize: 11, fontWeight: fontWeight.bold },

  emptyState: { alignItems: 'center', marginTop: spacing.xxxl },
  emptyIcon: { fontSize: 48, marginBottom: spacing.md },
  emptyText: { color: colors.text3, fontSize: fontSize.sm },
});
