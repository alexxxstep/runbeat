/**
 * HistoryScreen - Display workout and playlist history
 */
import React, { useEffect } from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';
import { useAuth } from '../hooks/useAuth';
import { usePlaylist } from '../hooks/usePlaylist';
import { LoadingSpinner } from '../components/Shared/LoadingSpinner';

export function HistoryScreen() {
  const { user } = useAuth();
  const { history, loadHistory, isLoading } = usePlaylist();

  useEffect(() => {
    if (user?.id) {
      loadHistory(user.id);
    }
  }, [user?.id, loadHistory]);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Історія</Text>
      </View>

      <FlatList
        data={history}
        keyExtractor={(item) => item.playlist_id || `playlist-${Date.now()}`}
        renderItem={({ item }) => (
          <View style={styles.item}>
            <Text style={styles.itemTitle}>
              Плейлист • {item.total_tracks} треків
            </Text>
            <Text style={styles.itemSubtitle}>
              {Math.round(item.total_duration / 60)} хв
            </Text>
          </View>
        )}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>
              Історія порожня. Створіть свій перший плейлист!
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  item: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F2F2F7',
  },
  itemTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  itemSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
  },
  emptyContainer: {
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
  },
});

