/**
 * ChatScreen - Main chat interface for RunBeat
 */
import React, { useEffect } from 'react';
import {
  View,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';

import { MessageBubble } from '../components/Chat/MessageBubble';
import { InputBar } from '../components/Chat/InputBar';
import { TypingIndicator } from '../components/Chat/TypingIndicator';
import { useChat } from '../hooks/useChat';
import { useAuth } from '../hooks/useAuth';
import { RootStackParamList } from '../navigation';

type ChatScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Chat'>;

export function ChatScreen() {
  const navigation = useNavigation<ChatScreenNavigationProp>();
  const { user } = useAuth();
  const { messages, sendMessage, generatePlaylist, isLoading } = useChat();

  const handleSend = async (text: string) => {
    const workout = await sendMessage(text, user?.id);

    // If workout is ready, generate playlist
    if (workout && !workout.needs_clarification) {
      try {
        const playlist = await generatePlaylist(workout);
        if (playlist) {
          // Navigate to player screen
          navigation.navigate('Player', {
            playlistId: playlist.playlist_id,
          });
        }
      } catch (error) {
        console.error('Failed to generate playlist:', error);
      }
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      <FlatList
        data={messages}
        renderItem={({ item }) => <MessageBubble message={item} />}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.messagesContainer}
        inverted={false}
      />
      {isLoading && <TypingIndicator />}
      <InputBar onSend={handleSend} disabled={isLoading} />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  messagesContainer: {
    padding: 16,
  },
});

