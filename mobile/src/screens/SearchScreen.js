import React, { useState, useCallback } from 'react';
import {
  View, Text, TextInput, FlatList, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert,
} from 'react-native';
import { apiSearch, apiAddFavourite } from '../api';
import { colors, spacing, radius, fontSize, fontWeight, difficultyColors, muscleColors } from '../theme';

const MUSCLES = ['','chest','shoulders','biceps','triceps','abdominals','lats','middle_back','lower_back','glutes','quadriceps','hamstrings','calves','forearms','traps'];
const MUSCLE_LABELS = {'':'All','chest':'Chest','shoulders':'Shoulders','biceps':'Biceps','triceps':'Triceps','abdominals':'Core','lats':'Lats','middle_back':'Mid Back','lower_back':'Low Back','glutes':'Glutes','quadriceps':'Quads','hamstrings':'Hamstrings','calves':'Calves','forearms':'Forearms','traps':'Traps'};
const TYPES = ['','strength','cardio','stretching','plyometrics','powerlifting','olympic_weightlifting'];
const DIFFICULTIES = ['','beginner','intermediate','expert'];

export default function SearchScreen() {
  const [query, setQuery]         = useState('');
  const [muscle, setMuscle]       = useState('');
  const [exType, setExType]       = useState('');
  const [difficulty, setDiff]     = useState('');
  const [results, setResults]     = useState([]);
  const [loading, setLoading]     = useState(false);
  const [expanded, setExpanded]   = useState(null);
  const [searched, setSearched]   = useState(false);

  const search = useCallback(async () => {
    setLoading(true);
    setSearched(true);
    try {
      const { data } = await apiSearch({ name: query, muscle, type: exType, difficulty });
      setResults(data.exercises || []);
    } catch {
      Alert.alert('Error', 'Search failed. Check your connection.');
    } finally { setLoading(false); }
  }, [query, muscle, exType, difficulty]);

  const addFav = async (ex) => {
    try {
      await apiAddFavourite({ name: ex.name, type: ex.type, muscle: ex.muscle, difficulty: ex.difficulty, instructions: ex.instructions });
      Alert.alert('Saved! ⭐', `${ex.name} added to favourites.`);
    } catch { Alert.alert('Error', 'Could not save.'); }
  };

  const renderChips = (options, selected, onSelect, labelMap = {}) => (
    <FlatList
      horizontal showsHorizontalScrollIndicator={false}
      data={options}
      keyExtractor={(item) => item}
      renderItem={({ item }) => (
        <TouchableOpacity
          style={[s.chip, selected === item && s.chipActive]}
          onPress={() => { onSelect(item); }}
        >
          <Text style={[s.chipText, selected === item && s.chipTextActive]}>
            {labelMap[item] || item || 'All'}
          </Text>
        </TouchableOpacity>
      )}
      contentContainerStyle={s.chips}
    />
  );

  const renderItem = ({ item, index }) => {
    const isOpen   = expanded === index;
    const diffCol  = difficultyColors[item.difficulty] || colors.text3;
    const musColor = muscleColors[item.muscle] || colors.primary;
    return (
      <View style={s.card}>
        <TouchableOpacity onPress={() => setExpanded(isOpen ? null : index)} style={s.cardTop}>
          <View style={s.cardLeft}>
            <Text style={s.cardName}>{item.name}</Text>
            <View style={s.badges}>
              {item.type       && <View style={[s.badge, { backgroundColor: `${colors.primary}22` }]}><Text style={[s.badgeText, { color: colors.primaryL }]}>{item.type.replace('_',' ')}</Text></View>}
              {item.muscle     && <View style={[s.badge, { backgroundColor: `${musColor}22` }]}><Text style={[s.badgeText, { color: musColor }]}>{item.muscle.replace('_',' ')}</Text></View>}
              {item.difficulty && <View style={[s.badge, { backgroundColor: `${diffCol}22` }]}><Text style={[s.badgeText, { color: diffCol }]}>{item.difficulty}</Text></View>}
            </View>
          </View>
          <View style={[s.dot, { backgroundColor: musColor }]} />
        </TouchableOpacity>

        {isOpen && (
          <View style={s.expandBody}>
            {item.instructions ? <Text style={s.instrText}>{item.instructions}</Text> : null}
            <TouchableOpacity style={s.saveBtn} onPress={() => addFav(item)}>
              <Text style={s.saveBtnText}>🤍 Save to Favourites</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };

  return (
    <View style={s.container}>
      {/* Search bar */}
      <View style={s.searchWrap}>
        <Text style={s.searchIcon}>🔍</Text>
        <TextInput
          style={s.searchInput}
          placeholder="Search exercises..."
          placeholderTextColor={colors.text3}
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={search}
          returnKeyType="search"
        />
        <TouchableOpacity style={s.goBtn} onPress={search}>
          <Text style={s.goBtnText}>Go</Text>
        </TouchableOpacity>
      </View>

      {/* Filters */}
      <View style={s.filters}>
        {renderChips(MUSCLES.slice(0,8), muscle, setMuscle, MUSCLE_LABELS)}
        {renderChips(DIFFICULTIES, difficulty, setDiff, { '':'Any Level','beginner':'Beginner','intermediate':'Intermediate','expert':'Expert' })}
      </View>

      {/* Results */}
      {loading ? (
        <View style={s.center}>
          <ActivityIndicator color={colors.primary} size="large" />
          <Text style={s.loadingText}>Searching...</Text>
        </View>
      ) : results.length > 0 ? (
        <FlatList
          data={results}
          keyExtractor={(_, i) => String(i)}
          renderItem={renderItem}
          contentContainerStyle={s.list}
          showsVerticalScrollIndicator={false}
        />
      ) : searched ? (
        <View style={s.center}>
          <Text style={s.emptyIcon}>🔍</Text>
          <Text style={s.emptyText}>No results found. Try different filters.</Text>
        </View>
      ) : (
        <View style={s.center}>
          <Text style={s.emptyIcon}>💪</Text>
          <Text style={s.emptyText}>Search for exercises by name,{'\n'}muscle group, or difficulty.</Text>
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },

  searchWrap: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: colors.bgCard, margin: spacing.xl,
    borderRadius: radius.full, paddingHorizontal: spacing.lg,
    borderWidth: 1, borderColor: colors.border,
  },
  searchIcon:  { fontSize: fontSize.base, marginRight: spacing.sm },
  searchInput: { flex: 1, paddingVertical: spacing.md, color: colors.text, fontSize: fontSize.base },
  goBtn: {
    backgroundColor: colors.primary, borderRadius: radius.full,
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
  },
  goBtnText: { color: colors.white, fontWeight: fontWeight.bold, fontSize: fontSize.sm },

  filters: { marginBottom: spacing.sm },
  chips:   { paddingHorizontal: spacing.xl, paddingBottom: spacing.sm, gap: spacing.sm },
  chip: {
    paddingHorizontal: spacing.lg, paddingVertical: spacing.sm,
    borderRadius: radius.full, backgroundColor: colors.bgCard2,
    borderWidth: 1, borderColor: colors.border,
  },
  chipActive:    { backgroundColor: colors.primary, borderColor: colors.primary },
  chipText:      { fontSize: fontSize.sm, color: colors.text3, fontWeight: fontWeight.semibold },
  chipTextActive:{ color: colors.white },

  list:    { padding: spacing.xl, paddingTop: 0, gap: spacing.sm },

  card: {
    backgroundColor: colors.bgCard, borderRadius: radius.xl,
    borderWidth: 1, borderColor: colors.border, overflow: 'hidden',
  },
  cardTop: { flexDirection: 'row', alignItems: 'center', padding: spacing.lg, gap: spacing.md },
  cardLeft:{ flex: 1 },
  cardName:{ fontSize: fontSize.md, fontWeight: fontWeight.bold, color: colors.white, marginBottom: spacing.xs },
  badges:  { flexDirection: 'row', gap: spacing.xs, flexWrap: 'wrap' },
  badge:   { paddingHorizontal: spacing.sm, paddingVertical: 2, borderRadius: radius.sm },
  badgeText:{ fontSize: 10, fontWeight: fontWeight.bold },
  dot:     { width: 8, height: 8, borderRadius: radius.full },

  expandBody: { borderTopWidth: 1, borderTopColor: colors.border, padding: spacing.lg },
  instrText:  { fontSize: fontSize.sm, color: colors.text2, lineHeight: 20, marginBottom: spacing.md },
  saveBtn: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.sm,
    backgroundColor: colors.bgCard2, borderRadius: radius.md,
    padding: spacing.md, alignSelf: 'flex-start',
    borderWidth: 1, borderColor: colors.border,
  },
  saveBtnText: { color: colors.text2, fontSize: fontSize.sm, fontWeight: fontWeight.semibold },

  center:      { flex: 1, justifyContent: 'center', alignItems: 'center', padding: spacing.xxl },
  loadingText: { color: colors.text3, marginTop: spacing.lg },
  emptyIcon:   { fontSize: 48, marginBottom: spacing.md },
  emptyText:   { color: colors.text3, textAlign: 'center', fontSize: fontSize.sm, lineHeight: 22 },
});
