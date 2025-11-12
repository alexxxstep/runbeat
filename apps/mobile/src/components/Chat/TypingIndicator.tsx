/**
 * TypingIndicator component for showing AI is typing
 */
import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';

export function TypingIndicator() {
  return (
    <View style={styles.container}>
      <View style={styles.bubble}>
        <ActivityIndicator size="small" color="#007AFF" />
        <Text style={styles.text}>AI думає...</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: 'flex-start',
    marginVertical: 4,
    marginHorizontal: 16,
  },
  bubble: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E5E5EA',
    padding: 12,
    borderRadius: 16,
  },
  text: {
    marginLeft: 8,
    color: '#8E8E93',
    fontSize: 14,
  },
});

